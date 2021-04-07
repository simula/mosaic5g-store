ccflags-y += -O2 

ccflags-y += -DRHEL_RELEASE_CODE=0 -DRRC_VERSION=3696 -DNAS_NETLINK -DPDCP_USE_NETLINK -DOAI_NW_DRIVER_USE_NETLINK   

obj-m += ue_ip.o
ue_ip-objs += device.o
ue_ip-objs += common.o
ue_ip-objs += netlink.o

all:
		make -C /lib/modules/$(shell uname -r)/build  M=$(PWD) modules
clean:
		make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
