# Create and run a docker container with mosaic5G

Docker-M5G is an ecosystem of opensource platforms and use-cases for 4G-5G R&D to build a light-weight 5G service delivery platform across reusable software components.
Docker-Mosaic-5G is composed of the following submodules:

The LL-MEC low latency MEC platform
The FlexRAN for real-time master controller
The OAI-CN  for monolitic and disaggregated CN

This script allows you to create docker containers already hosting the mosaic5G components.

**WARNING NOTE**: This creates a set of containers with **security** options **disabled**, this is an unsupported setup, if you have multiple snap packages inside the same container they will be able to break out of the confinement and see each others data and processes. Use this setup to build or test single snap packages but **do not rely on security inside the container**.


## Extra packages installed in the Docker 

```
1. net-tools
2. iputils-ping
3. vim
4. 
5. 
```
