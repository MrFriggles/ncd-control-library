![event parameter](https://github.com/MrFriggles/ncd-control-library/actions/workflows/flake8.yml/badge.svg?event=push)

# NCD Control Library
This is a Python that will help create scripts to automate tests using the NCD ethernet relay controller.

Library is still in development, and requires further exception and error handling added.

## Usage
```python
from NCD import *

ncd = NCDDevice("1.2.3.4", 1234)
# or to let the library find the device on the network
ncd = NCDDevice(port=1234)
ncd.connect()

# Switching ON relay 1 in bank 1:
ncd.switchrelay(1, 1, True)

# Switching OFF relay 2 in bank 4:
ncd.switchrelay(4, 2, False)

# Switching ON relay 1 in ALL banks:
ncd.switchrelay(NCDDevice.ALL_BANKS, 1, True)
```

