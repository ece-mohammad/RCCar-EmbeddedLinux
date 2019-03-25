#!/bin/sh

# --------------------------------------------------------------------
# wifi configure
# -------------------------------------------------------------------
cp package/busybox/S10mdev ${TARGET_DIR}/etc/init.d/S10mdev
chmod 755 ${TARGET_DIR}/etc/init.d/S10mdev
cp package/busybox/mdev.conf ${TARGET_DIR}/etc/mdev.conf



#cp board/raspberrypi3/interfaces ${TARGET_DIR}/etc/network/interfaces
#cp board/raspberrypi3/wpa_supplicant.conf ${TARGET_DIR}/etc/wpa_supplicant.conf
#cp board/raspberrypi3/dhcpd.conf ${TARGET_DIR}/etc/dhcp/dhcpd.conf

