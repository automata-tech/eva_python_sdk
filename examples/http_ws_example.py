#!/usr/bin/env python3

import evasdk
import json
import asyncio
import time

# This example shows usage of the eva_ws and eva_http modules, used for direct control
# using the network interfaces. eva_http also contains some helper functions not
# contained in the public API, such as lock_wait_for.

host_ip = input("Please enter a Eva IP: ")
token = input("Please enter a valid Eva token: ")

print('ip: [{}], token: [{}]\n'.format(host_ip, token))

http_client = evasdk.EvaHTTPClient(host_ip, token)

# The session token will be valid for 30 minutes, you'll need to renew the session
# if you want the websocket connection to continue after that point.
session_token = http_client.auth_create_session()

users = http_client.users_get()
print('Eva at {} users: {}\n'.format(host_ip, users))

joint_angles = http_client.data_servo_positions()
print('Eva current joint angles: {}'.format(joint_angles))


async def eva_ws_example(host_ip, session_token):
    websocket = await evasdk.ws_connect(host_ip, session_token)

    msg_count = 0
    time_since_msg = time.time()
    while True:
        ws_msg_json = await websocket.recv()
        print('WS msg delta T: {}, number: {}'.format(time.time() - time_since_msg, msg_count))
        msg_count += 1
        time_since_msg = time.time()

        ws_msg = json.loads(ws_msg_json)
        print(ws_msg)

asyncio.get_event_loop().run_until_complete(eva_ws_example(host_ip, session_token))
