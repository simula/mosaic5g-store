# Supporting web server for GUI

The **drone.py** provides

- a simple web server serving the necessary static files

- support for saving and restoring GUI state

- support for running processes (tasks) based on GUI commands (disable by default)

**WARNING**: The current implementation does not include any authentication
support. Due to drone being capable of running arbitrary commands as instructed
by the GUI, it is a security risk. Thus, do not change lightly the default setting of
listening only to `localhost` connections if `tasks` is enabled.
However, it is possible to change the defaults:

- `--port=<port to listen>`

- `--address=<address to listen>`

- `--tasks`


To start the drone without tasks support (as simple web server), for example,

```bash
cd sdk/frontend/drone
python drone.py --port=8088
```
... or allow connectons from any address
```bash
python drone.py --port=8088 --address=0
```
... and with task support

```bash
cd sdk/frontend/drone
python drone.py --port=8088 --tasks
```
