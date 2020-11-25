# Network Store 
A repository of network function, control application, SDK, charms, templates, 
images, tools.


## Note
This branch is intended for the snaps in devmode, while the snaps in confined mode are now on develop branch

# FlexRAN SDK

A Software Developement Kit (SDK) has been developped to facilitate the use of the API that is exposed by FlexRAN-rtc.
Multiple network applications, including RRM, monitoring, and spectrum sharing apps have been developped to illustrate the use of this SDK. 
The apps are located in the *sdk* subdirectory while the SDK itself is located in the *sdk/lib* subdirectory and are both coded using Python. Both apps use the same (optional) arguments : 
* *--url* to define the URL of the API exposed by FlexRAN-rtc
* *--port* to define the port of the API exposed by FlexRAN-rtc
* *--op-mode* to define the operating mode. Either *sdk* to operate with FlexRAN or *test* to get data from JSON files
* *--log* to define the log level. Either *debug*, *info*, *warning*, *error* or *critical*

When operating in test mode, the input data is taken from JSON files located in the *sdk/inputs* inputs directory. 
They contain example data that could have been retrieved from an operating FlexRAN. The file used for both example apps is [all.json](sdk/output/all_1.json). 
As its name suggests, this file contains all data sets that otherwise would be available in two different files: one for configurations and the other for stats. 
The first part, also found in the file *enb_config.json*, contains the description of the setup : eNodeBs with their configuration and capabilities, UEs with their configuration and capabilities and logical channels with their configuration and capabilities. 
The second part, also found in the file *mac_stats.json*, contains various stats provided by the MAC layer for each, like the [CQI](http://www.sharetechnote.com/html/Handbook_LTE_CQI.html) and the [BSR](http://www.sharetechnote.com/html/Handbook_LTE_BSR.html). Those two parts (either in one or two files) can be modified during the execution of the apps to simulate varying situations, like UEs competing for the channel resource or channel conditions varying over time. 

The [rrm_app.py](sdk/rrm_app.py) is a fairly simple RRM app that demonstrates some capabilities of the SDK and does not require anything more than the previously described arguments. 
The [rrm_kpi_app.py](sdk/rrm_kpi_app.py) is a bit more complex and requires an additionnal file [template.yaml](tests/template.yaml). 
This file is divided in two parts. The first part contains, for each eNodeB, a list of slices defined by their type. 
The second part contains for each slice type its characteristics, which are so far : the reserved rate, the priority of the slice and the robustness of the communications. 
