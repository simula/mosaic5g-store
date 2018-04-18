# Supporting web server for GUI

The **drone.py** provides

- a simple web server serving the necessary static files

- support for saving and restoring GUI state

- support for running processes (tasks) based on GUI commands

**WARNING**: The current implementation does not include any authentication
support. Due to drone being capable of running arbitrary commands as instructed
by the GUI, is a security risk. Thus, do not change lightly the default setting of
listening only to `localhost` connections. However, it is possible to change the
defaults:

- `--port=<port to listen>`

- `--address=<address to listen>`


To start the drone, for example,

```bash
cd sdk/frontend/drone
python drone.py --port=8088
```
