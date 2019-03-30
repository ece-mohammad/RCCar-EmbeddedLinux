# RCCar-EmbeddedLinux
Remote Controller Car, controlled through a ssh session. Using RPI3b+, linux image built by buildroot.

### overlay
contains the root file system overlay for buildroot

### postbuild
contains the post build scripts for buildroot

### wifi_ap.comfig
buildroot configurations file, it adds python, hostapd packages to the image, adds root password and enables wchar support among other things

---------------------------
## Usage:
1. Configure buildroot image, build it and burn the image to an sdcard
2. Boot RPI from the sdcard, wait for its wifi ap to start and connect to it.
3. Login through an ssh session
4. after login you will be prompted the following terminal:
`
    ____  ______   _________    ____
   / __ \/ ____/  / ____/   |  / __ \
  / /_/ / /      / /   / /| | / /_/ /
 / _, _/ /___   / /___/ ___ |/ _, _/
/_/ |_|\____/   \____/_/  |_/_/ |_|

-----------------------------------------
Controls:
q/w: increase/decrease turn rate.
a/z: increase/decrease speed.
f4: exit.
-----------------------------------------
Current direction: rotate_left
Current speed: 0
Current turn rate: 0
Distance to object: 0
`
- user navigation keys (up/down/left/right) to move the car
- use the keys (q/w, a/z) to change speeds
- press F4 to close the ssh session and return to RPI terminal
