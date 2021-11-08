#!/usr/bin/env python3

from evasdk import Eva
import json

# This example shows usage of the Eva object, used for controlling Eva,
# reading Eva's current state and responding to different events triggered
# by Eva's operation.

host_ip = input("Please enter a Eva IP: ")
token = input("Please enter a valid Eva token: ")

eva = Eva(host_ip, token)

# Send Eva to a waypoint
with eva.lock():
    eva.control_wait_for_ready()
    eva.control_go_to([0, 0, 0, 0, 0, 0])

# Print Eva's toolpaths
toolpaths = eva.toolpaths_list()
outToolpaths = []
for toolpathItem in toolpaths:
    toolpath = eva.toolpaths_retrieve(toolpathItem['id'])
    outToolpaths.append(toolpath)
print(json.dumps(outToolpaths))

# Create a basic toolpath and execute it
toolpath = {
    "metadata": {
        "version": 2,
        "default_max_speed": 0.25,
        "payload": 0,
        "analog_modes": {
            "i0": "voltage",
            "i1": "voltage",
            "o0": "voltage",
            "o1": "voltage"
        },
        "next_label_id": 3
    },
    "waypoints": [{
        "label_id": 1,
        "joints": [0, 0.5235987755982988, -1.7453292519943295, 0, -1.9198621771937625, 0]
    }, {
        "label_id": 2,
        "joints": [0.18392622441053394, 0.8259819316864014, -2.050006151199341, 0.1785774528980255, -1.6037521743774412, -0.549331545829773]
    }],
    "timeline": [{
        "type": "home",
        "waypoint_id": 0
    }, {
        "type": "trajectory",
        "trajectory": "joint_space",
        "waypoint_id": 1
    }, {
        "type": "trajectory",
        "trajectory": "joint_space",
        "waypoint_id": 0
    }]
}

with eva.lock():
    eva.control_wait_for_ready()
    eva.toolpaths_use(toolpath)
    eva.control_home()
    eva.control_run(loop=1)
