#!/usr/bin/env python3

import eva-sdk
import json
import asyncio
import websockets
import time

# This example shows usage of the eva_ws and eva_http modules, used for direct control
# using the network interfaces. eva_http also contains some helper functions not
# contained in the public API, such as lock_wait_for.

host_ip = input("Please enter a Eva IP: ")
token = input("Please enter a valid Eva token: ")

print('ip: [{}], token: [{}]\n'.format(host_ip, token))

http_client = eva-sdk.EvaHTTPClient(host_ip, token)

users = http_client.users_get()
print('Eva at {} users: {}\n'.format(host_ip, users))

joint_angles = http_client.data_servo_positions()
print('Eva current joint angles: {}'.format(joint_angles))

async def eva_ws_example(host_ip, token):
    websocket = await eva-sdk.ws_connect(host_ip, token)

    msg_count = 0
    time_since_msg = time.time()
    while True:
        ws_msg_json = await websocket.recv()
        print('WS msg delta T: {}, number: {}'.format(time.time() - time_since_msg, msg_count))
        msg_count += 1
        time_since_msg = time.time()

        ws_msg = json.loads(ws_msg_json)
        print(ws_msg)

asyncio.get_event_loop().run_until_complete(eva_ws_example(host_ip, token))
