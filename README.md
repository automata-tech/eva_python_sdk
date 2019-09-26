# Eva Python SDK

The eva_python_sdk provides convenient access to the Automata Eva API from applications written in Python 3.

__* This SDK is currently in beta, any breaking changes during development will be communicated via changelog__

- [Eva Python SDK](#eva-python-sdk)
  - [Installation](#installation)
    - [Using pipenv](#using-pipenv)
  - [Examples](#examples)
    - [Eva](#eva)
    - [automata.eva_http and automata.eva_ws](#automataevahttp-and-automataevaws)
  - [Logging](#logging)
  - [Bugs and feature requests](#bugs-and-feature-requests)
  - [Testing](#testing)
  - [License](#license)

## Installation

### Using pipenv

    $ pipenv install git+https://github.com/automata-tech/eva_python_sdk.git@master#egg=automata

## Examples

The Eva object allows you to directly control an Eva robot. It provides lots of useful helper function for interacting with the robot.

### Eva

**Connecting**
```python
from automata import Eva

host = '<your_eva_IP_here>'
token = '<your_token_here>'
client_id = '<your_tokens_client_id_here>'

eva = Eva(host, token, client_id)
```

**GoTo movement**
```python
eva = Eva(host_ip, token, client_id)

with eva.lock():
    eva.control_wait_for_ready()
    eva.control_go_to([0, 0, 0, 0, 0, 0])
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

eva = Eva(host, token, client_id)

with eva.lock():
    eva.control_wait_for_ready()
    eva.toolpaths_use(toolpath)
    eva.control_home()
    eva.control_run(loop=1)
```

Please refer to the examples directory for more SDK usage examples.

### automata.eva_http and automata.eva_ws

These can be used to interact directly with the HTTP and Websocket APIs.

## Logging

The SDK uses Debug and Error level logging exclusively. Each Eva instance will log using the name `automata.Eva:<host_name_here>`. If you wish to enable the debug logging:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Bugs and feature requests

Please raise any bugs or feature requests as a Github issues. We also gratefully accept pull requests for features and bug fixes.

## Testing

    $ pipenv shell
    $ python -m pytest automata/<name-of-file-to-test> 

    # some tests require supplying ip, token and the token's client ID via the `--ip`, `--token` and `--id` arguments
    $ python -m pytest automata/<name-of-file-to-test> --ip 172.16.16.2 --token abc-123-def-456 --id abcd0123

## License

This code is free to use under the terms of the Apache 2 license. Please refer to LICENSE for more information.
