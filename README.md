# pibluebot

This is a server script which controls the Raspberry pi rover.  For an implementation overview refer to the following [video](https://www.youtube.com/watch?v=Gx4004YZKME):


## Implementation

The rover is controlled by Raspberry Pi Zero v 1.3, with Raspbian-jesse distribution installed.  The rover actions are controlled by rover.py script. The script is ran as an unprivileged user _rover_ who is a member of  _tty_ and _shutdown_ groups. The _tty_ group membership is needed for serial port operations, the _shutdown_ groups was added to manage permissions for the `shutdown` command, which were granted by adding the following line in the sudoers file via `visudo` command:

`%shutdown ALL = NOPASSWD: /sbin/shutdown`


### Permission tricks

In a default Raspbian installation the _tty_ group owns the serial interface, however it can onty write to it.The _tty_ does NOT have read permissions! Even if you change the permissions manually, they will notpersist across reboots.  One way to overcome this is by wrapping the rover.py into a two part systemd service. The first part grants read permission to the _tty_ group before starting the rover.py script. The second part runs rover.py as a _rover_ user.

Please refer to the [rover-setup.service](https://github.com/vrestivo/pibluebot_public/blob/master/rover-setup.service) and [rover.service] (https://github.com/vrestivo/pibluebot_public/blob/master/rover.service) files



