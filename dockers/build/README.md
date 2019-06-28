# Build 

This folder contains the build materials shared by all containers. 

- **hook**: Handles all the configurations related to the snap
- **conf.yaml**: the default config file that is shipped with container
- **build.sh**: The script is used for building docker images, updating hook and cleaning.

## Hook

The hook mainly uses `sed` to set the configuration. It takes configs from *conf.yaml* and retrieve IP information from Golang's *net* package. Visit [here](https://github.com/tig4605246/oai-snap-in-docker) to take a look at the source code of hook.

## conf.yaml

conf.yaml contains the two things. One is the parameters for oai-cn and oai-ran, the other is the information of network environment. the conf supports following lte parameters,

- MNC and MCC
- eutraBand
- downlinkFrequency
- uplinkFrequencyOffset

The test flag here is for unit test. Make sure it's **false** when in general usage.

## build.sh

### Overview

build.sh can automate the build process of all docker images. It'll copy the materials from build/ folder, run the build process inside individual folder, then remove the materials that is copied.

### Tutorial

**Quick Start**

- To build oai-cn docker containers from source, with the tag mytest:
  - `./build.sh oai-cn mytest`
  - With default setting, you'll get an image **mosaic5gecosys/oaicn:mytest**.

- To build oai-ran docker containers from source, with the tag mytest:
  - `./build.sh oai-ran mytest`
  - With default setting, you'll get an image **mosaic5gecosys/oairan:mytest**

- In addition, `flexran` and `ll-mec` are for building *flexran* and *ll-mec* respectively.

- To clean up unused containers & iamges:
  - `./build.sh clean_all`
  - This will clean the images and containers that are used for building

**build.sh** takes two inputs: the *target app* and the *version tag*. For example, `./build.sh oai-cn 0.1` will build a oai-cn image tagged 0.1. The parameters related to repository and image names are listed at the start of the script. Chane them to match your environment.

```shell
REPO_NAME="mosaic5gecosys" # Change it to your repository
TARGET="${REPO_NAME}/${TARGET_NAME}" # The name of our image
TAG_BASE="base" # The tag for the base image
BASE_CONTAINER="build_base" # The name of the temporary container
RELEASE_TAG="latest" # Default release tag
```

If you have [hook source](https://github.com/tig4605246/oai-snap-in-docker) in your GOPATH, you can run `./build.sh build-hook` to rebuild and update the hook in the build folder. 
