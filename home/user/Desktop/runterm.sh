#!/bin/bash

# Console wrapper to display VPN-GAT logs
#
# this is called from the systemd unit
# made for LXDE desktop env
# place under /home/user/Desktop/runterm.sh

export DISPLAY=:0
lxterm -e /home/user/Desktop/run.sh
