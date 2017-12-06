# pibluebot

This is a server script which controls the Raspberry pi rover.  For an implementation overview refer to the following [video](https://www.youtube.com/watch?v=Gx4004YZKME):


## Implementation

The rover is controlled by Raspberry Pi Zero W, with Raspbian-jesse distribution installed.  The rover actions are controlled by rover.py script.
The script is ran as an unprivileged user _rover_ who is a member of _dialout_ _tty_ and _shutdown_ groups.
The _tty_ group membership is needed for serial port operations, the _shutdown_ groups was added to manage permissions for the `shutdown` command,
which were granted by adding the following line in the sudoers file via `visudo` command:

`%shutdown ALL = NOPASSWD: /sbin/shutdown`


###Bluetooth Gotchas
The rover implementation uses Bluetooth Serial Profile, which is NOT enabled by default.  In order to fix it there are a few modifications
required for the systemd bluetooth service:
1. add compatibility option `-C` to the `bluetoothd` 
2. add serial profile using `sdptool` command

The above requirements are reflected in the following 2 lines of your systemd bluetooh.service script:

`ExecStart=/usr/lib/bluetooth/bluetoothd -C`
and
`ExecStartPost=/usr/bin/sdptool add SP`



### Permission tricks

In Pi Zero W the Bluetooth is ran through a serial inteface /dev/ttyAMA0.  However, you will not be able to connect to it directly.
The tricky part is the way RFCOMM sockets are implemented in the in Linux.  By default the device will be listening for a connection,
using `rfcomm listen hcXX`, or `rfcomm watch hcXX` commands, where hcXX is your Bluetooth interface. 
Once connection is acceptied the Bluetooth stack will create anotherserial inteface, usually /dev/rfcomm0,
and hand over the connection to it.  The inteface is owned by group dialout, hence the required
group membership mentioned above.

The systemd rover-setup.service takes care of listening for a connection by running `rfcomm watch hci0`.
The rover.service launches the rover.py script, which communicates via /dev/rfcomm0.

Please refer to the [rover-setup.service](https://github.com/vrestivo/pibluebot_public/blob/master/rover-setup.service) and [rover.service] (https://github.com/vrestivo/pibluebot_public/blob/master/rover.service) files



