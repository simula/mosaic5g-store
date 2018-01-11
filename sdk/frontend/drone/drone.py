import os
import sys
import signal
import pwd
import glob
import ssl
import pty
import base64
import subprocess
import tornado.ioloop
import tornado.iostream
import tornado.process
import tornado.web
import tornado.websocket
import tornado.options

RUNNING = {}

def task_prepare(uid, gid):
    def __action():
        os.setsid()
        if gid:
            os.setgid(gid)
        if uid:
            os.setuid(uid)
        print "Task started uid:gid = {}:{}".format(os.getuid(), os.getgid())
    return __action

class DroneTask(object):

    def __init__(self, id):
        self.id = id
        self.c = None
        self.kill = False
        self.watchers = set()
        RUNNING[id] = self


    def run(self, command, input, cwd, user):
        if self.c is None:
            try:
                if user is None:
                    uid = None
                    gid = None
                else:
                    pw = pwd.getpwnam(user)
                    uid = pw.pw_uid
                    gid = pw.pw_gid
                #master, slave = pty.openpty()
                #self.master = tornado.iostream.PipeIOStream(master);
                self.c = tornado.process.Subprocess(command,
                                                    stdout=tornado.process.Subprocess.STREAM,
                                                    stdin=subprocess.PIPE,
                                                    stderr=tornado.process.Subprocess.STREAM,
                                                    close_fds=True,
                                                    cwd=cwd,
                                                    preexec_fn=task_prepare(uid, gid)
                )
            except Exception as e:
                self._send_to(self.watchers, {'id': self.id, 'error': str(e)})
                self.done()
                return
                
            self.c.stdout.set_close_callback(self.done)
            #self.c.stderr.set_close_callback(self.done)
            self.c.stdout.read_until_close(callback=self.got, streaming_callback=self.got)
            self.c.stderr.read_until_close(callback=self.got, streaming_callback=self.got)
            #self.master.read_until_close(callback=self.got, streaming_callback=self.got)

    def stop(self):
        p = self.c
        if p is not None:
            if p.proc.poll() is None:
                print "Issuing kill for '" + self.id + "'"
                # Use SIGTERM on first stop, and SIGKILL on subsequent stop attempts.
                os.killpg(os.getpgid(p.proc.pid), signal.SIGKILL if self.kill else signal.SIGTERM)
                self.kill = True
            
    def got(self, data):
        self._send_to(self.watchers, {'status': 'running', 'id': self.id, 'log': unicode(data, errors='replace')})

    def done(self):
        RUNNING.pop(self.id, None)
        #self.master.close_fd()
        watchers = self.watchers
        self.watchers = set()
        self._send_to(watchers, {'id': self.id, 'status': 'done'})

    def __del__(self):
        self.done()

    def _send_to(self, watchers, msg):
        for w in watchers:
            w.send(msg)

    def watch(self, client):
        self.watchers.add(client)
        
    def unwatch(self, client):
        self.watchers.discard(client)

class DroneClient(tornado.websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):
        print ("ws init: " + str(args) + " " + str(kwargs))
        super(DroneClient,self).__init__(*args, **kwargs)

    def check_origin(self, origin):
        return True

    def open(self):
        print("ws open")
        #print str(self.get_ssl_certificate())

    def on_message(self, message):
        message = tornado.escape.json_decode(message)
        print("ws message="+ str(message))
        req = message.get('request')
        id = message.get('id')
        task = RUNNING.get(id)
        if req == 'start':
            command = message.get('command')
            if task is None:
                if command is not None:
                    task = DroneTask(id)
                    self.send({'status': 'starting', 'id': str(id)})
                    task.watch(self)
                    task.run(command,
                             message.get('input'),
                             message.get('cwd'),
                             message.get('user'))
                else:
                    self.send({'status': 'running', 'id': str(id)})
            else:
                task.watch(self)
                task.kill = False
                self.send({'status': 'running', 'id': str(id)})
        elif task is None:
            # Note: gives this, even if request is garbage
            self.send({'error': "Task '" + str(id) + "' is not active", 'message': message, 'id': str(id)})
        elif req == 'stop':
            task.watch(self)
            self.send({'status': 'stopping', 'id': str(id)})
            task.stop()
        elif req == 'input':
            #task.master.write_to_fd(message.get('input', '').encode('utf-8'))
            task.c.stdin.write(message.get('input', '').encode('utf-8'))
        else:
            self.send({'error': "Unknown request '" + str(req), 'message': message})

    def on_close(self):
        print ("ws closed")
        self._detach()

    def send(self, msg):
        self.write_message(msg)

    def _detach(self):
        # Remove client from all running tasks
        for task in RUNNING.itervalues():
            print str(task)
            task.unwatch(self)
        
    def __del__(self):
        self._detach()

class ConfigHandler(tornado.web.RequestHandler):

    def _json_reply(self, data):
        self.set_header('Content-type', 'application/json')
        self.write(data)

    def _json_error(self, msg, id=None):
        data = {'message': msg}
        if id is not None:
            data['id'] = id
        self._json_reply(data)
        
    def _file_name_in(self, dir, name):
        return './' + dir + '/' + name

    def delete(self, dir, name):
        if name is None or name == '/':
            self._json_error("DELETE target not given: {}".format(self.request.path))
        else:
            path = './' + dir + name
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    self._json_reply({'id': dir,
                                 'message': "Removed '" + path + "'"})
                else:
                    self._json_error("'{}' does not exist".format(name))
            except Exception as e:
                self._json_error("Delete '{}' failed: {}".format(name, str(e)))

    def get(self, dir, name):
        if name is None or name == '/':
            self._json_reply({'id': dir, 'result': [x.rpartition('/')[2] for x in glob.glob('./' + dir + '/*')]})
        else:
            #name = name[1:]  # name starts always with '/', remove it
            path = './' + dir + name
            try:
                with open(path, "r") as f:
                    # This assumes saved data is a JSON string
                    self.set_header('Content-type', 'application/json')
                    self.write(f.read())
            except Exception as e:
                self._json_error("Failed reading file '{}': {}".format(path, str(e)))

    def post(self, dir, name):
        if name is None or name == '/':
            self._json_error("POST target not given: {}".format(self.request.path))
        else:
            path = './' + dir + name
            try:
                with open(path, "w") as f:
                    f. write(self.request.body)
                self._json_reply({'id': dir, 'message': "Saved '" + path + "'"});
            except Exception as e:
                self._json_error("Failed writing file '{}': {}".format(path, str(e)))
    
def main():
    tornado.options.define("address", default="localhost", help="Listening address")
    tornado.options.define("port", default=8080, help="Listening port")
    tornado.options.parse_command_line()
    
    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static")
    }
    application = tornado.web.Application([
        (r"/drone", DroneClient),
        (r"/config/(conf|tasks)(/.*)?", ConfigHandler),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": settings['static_path'], "default_filename": "index.html"})
    ], **settings);
    # ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    # ssl_ctx.load_cert_chain('./keys/drone.crt', './keys/drone.key')
    #ssl_ctx.verify_mode = ssl.CERT_REQUIRED
    # application.listen(tornado.options.options.port, ssl_options=ssl_ctx)
    application.listen(tornado.options.options.port, address=tornado.options.options.address)
    try:
        tornado.ioloop.IOLoop.current().start()
    except:
        pass

    for task in RUNNING.itervalues():
        task.stop()

if __name__ == '__main__':
    main()

