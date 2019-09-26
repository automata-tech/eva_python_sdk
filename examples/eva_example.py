#!/usr/bin/env python3

from automata.Eva import Eva
import time
import json
import logging

# This example shows usage of the Eva object, used for controlling Eva,
# reading Eva's current state and responding to different events triggered
# by Eva's operation. 

host_ip = input("Please enter a Eva IP: ")
token = input("Please enter a valid Eva token: ")
client_id = input("Please enter the token client ID: ")

eva = Eva(host_ip, token, client_id)

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

with eva.lock():
    eva.control_wait_for_ready()
    eva.toolpaths_use(toolpath)
    eva.control_home()
    eva.control_run(loop=1)
