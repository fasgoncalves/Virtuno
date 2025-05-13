#!/bin/bash
#
PORTA_SPICE=$1
#
export USER=root
#export SUDO_UID=1000
source /root/.bashrc
export LOGNAME=root
export OLDPWD=/opt/Virtuno
export XAUTHORITY=/root/.Xauthority
export DISPLAY=:1
/usr/bin/xhost +
stat /root/.Xauthority
#
#sudo -u fgoncalves -p triAxpto remote-viewer "spice://127.0.0.1:$PORTA_SPICE"
sudo remote-viewer "spice://127.0.0.1:$PORTA_SPICE" 
#
