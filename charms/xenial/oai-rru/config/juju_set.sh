#!/bin/bash
juju set oai-enb  downlink_frequency=2680000000L
juju set oai-enb  uplink_frequency_offset=-120000000
juju set oai-enb  eutra_band=7
#juju set oai-enb  N_RB_DL=50
#juju set oai-enb nb_antennas_tx=2
#juju set oai-enb nb_antennas_rx=2
#juju set oai-enb tx_gain=90
#juju set oai-enb tx_gain=120
