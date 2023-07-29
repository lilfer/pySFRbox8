# SFR TV Box 8 Python Library

This Python library provides a simple interface to control the SFR TV Box 8 (stb8) over WebSockets.

## Features

- Send remote control commands to the box.
- Get the current power status of the box.
- Get information about the box.
- Listen for power status updates.

## Installation

The library requires the `websocket-client` module. You can install it using pip:

```pip install websocket-client ```

Once you have installed the required module, you can include the `pySFRbox8.py` file in your project and start using the `Remote` and `StatusListener` classes.

## Buttons

The following buttons can be used with the `press_button` method:

- power
- up, down, right, left
- ok
- back
- home
- volDown, volUp, mute
- channelDown, channelUp
- fastBackward, fastForward
- playPause
- 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
- stop
- record

This list is implemented in the `Remote` class as the `BUTTONS` attribute.

## Usage

### Remote Control

```python
from pySFRbox8 import Remote

host = 'your_box_ip_address'

# with context manager
with Remote(host) as remote:
    remote.press_button('up')
    remote.press_button('power')
    versions = remote.get_versions()
    print(versions)  # {'remoteControlVersion': '1.2.0', 'boxType': 'STB8', 'boxName': 'SFR_STB8_XXXX', 'macAddress': 'XXXXXXXXXXXX'}
    if remote.is_power_on():
        print("Box is powered on!")
    else:
        print("Box is powered off!")

# without context manager
remote = Remote(host)
remote.press_button('3')
remote.close()
```

### Status Listener

```python
from pySFRbox8 import StatusListener

host = 'your_box_ip_address'

def on_status_change(is_power_on):
    if is_power_on:
        print("Box is now powered on!")
    else:
        print("Box is now powered off!")

# with context manager
with StatusListener(host, on_status_change=on_status_change):
    input("Press Enter to stop monitoring.")

# without context manager
status_listener = StatusListener(host, on_status_change=on_status_change)
input("Press Enter to stop monitoring.")
status_listener.close()
```