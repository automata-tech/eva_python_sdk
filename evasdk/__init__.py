"""Eva Python SDK

This module provides convenient access to the Automata Eva API from applications written in Python 3.

## Examples

The Eva object allows you to directly control an Eva robot. It provides lots of useful helper function for interacting with the robot.

### Eva

**Connecting**

```python
host = '<your_eva_IP_here>'
token = '<your_token_here>'

eva = Eva(host, token)
```

**GoTo movement**

```python
eva = Eva(host_ip, token)

with eva.lock():
    eva.control_wait_for_ready()
    eva.control_go_to([0, 0, 0, 0, 0, 0], mode='teach')
```

**Toolpath create and run**

```python
toolpath = {
    "metadata":{
        "default_velocity":0.7,
        "next_label_id":5,
        "analog_modes":{ "i0":"voltage", "i1":"voltage", "o0":"voltage", "o1":"voltage" }
    },
    "waypoints":[
        { "joints":[-0.68147224, 0.3648368, -1.0703622, 9.354615e-05, -2.4358354, -0.6813218], "label_id":3 },
        { "joints":[-0.6350288, 0.25192022, -1.0664424, 0.030407501, -2.2955494, -0.615318], "label_id":2 },
        { "joints":[-0.13414459, 0.5361486, -1.280493, -6.992453e-08, -2.3972468, -0.13414553], "label_id":1 },
        { "joints":[-0.4103904, 0.33332264, -1.5417944, -5.380291e-06, -1.9328799, -0.41031334], "label_id":4 }
    ],
    "timeline":[
        { "type":"home", "waypoint_id":2 },
        { "type":"trajectory", "trajectory":"joint_space", "waypoint_id":1 },
        { "type":"trajectory", "trajectory":"joint_space", "waypoint_id":0 },
        { "type":"trajectory", "trajectory":"joint_space", "waypoint_id":2 }
    ]
}

eva = Eva(host, token)

with eva.lock():
    eva.control_wait_for_ready()
    eva.toolpaths_use(toolpath)
    eva.control_home()
    eva.control_run(loop=1, mode='teach')
```

Please refer to the examples directory for more SDK usage examples.

### evasdk.eva_http and evasdk.eva_ws

These can be used to interact directly with the HTTP and Websocket APIs.
Useful when you don't want the managed websocket connection provided by the evasdk.Eva object.
"""

from .Eva import Eva
from .eva_http_client import EvaHTTPClient
from .robot_state import RobotState
from .helpers import strip_ip
from .eva_errors import (
    EvaError,
    EvaValidationError, EvaAuthError, EvaAutoRenewError,
    EvaAdminError, EvaServerError, EvaWebsocketError)
from .version import __version__
from .EvaDiscoverer import (
    DiscoverCallback, DiscoveredEva,
    find_evas, find_eva, find_first_eva, discover_evas,
)
