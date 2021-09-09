#!/usr/bin/env python3

from evasdk import Eva

# This example shows usage of the eva_ws and eva_http modules, used for direct control
# using the network interfaces. eva_http also contains some helper functions not
# contained in the public API, such as lock_wait_for.

host_ip = input("Please enter a Eva IP: ")
token = input("Please enter a valid Eva token: ")

print(f'ip: [{host_ip}], token: [{token}]\n')

eva = Eva(host_ip, token)

users = eva.users_get()
print(f'Eva at {host_ip} users: {users}\n')

joint_angles = eva.data_servo_positions()
print(f'Eva current joint angles: {joint_angles}')

with eva.websocket() as ws:
    ws.register('state_change', print)
    input('press return when you want to stop\n')
