import json
import asyncio
import time
import logging
import threading


from .helpers import (strip_ip)
from .eva_ws import ws_connect
from .eva_errors import EvaDisconnectionError
from .eva_http_client import EvaHTTPClient
from .eva_locker import EvaWithLocker


class Eva:
    """
    The Eva class represents a self updating snapshot of Eva at any one time.
    Once initialised Eva connects to Eva via a websocket and keeps the current
    state of the robot using the websocket update messages.
    """
    def __init__(self, host_ip, token, request_timeout=5, renew_period=60*20):
        parsed_host_ip = strip_ip(host_ip)

        self.__http_client = EvaHTTPClient(parsed_host_ip, token, request_timeout=request_timeout, renew_period=renew_period)
        self.__logger = logging.getLogger('eva-sdk.Eva:{}'.format(host_ip))

        self.__eva_locker = EvaWithLocker(self)


    def set_request_timeout(self, request_timeout):
        self.__http_client.request_timeout = request_timeout


    # --------------------------------------------- Lock Holder ---------------------------------------------
    def __enter__(self):
        self.__eva_locker.__enter__()
        return self


    def __exit__(self, type, value, traceback):
        self.__eva_locker.__exit__(type, value, traceback)


    # --------------------------------------------- HTTP HANDLERS ---------------------------------------------
    def api_call_with_auth(self, method, path, payload=None):
        self.__logger.debug('Eva.api_call_with_auth {} {}'.format(method, path))
        return self.__http_client.api_call_with_auth(method, path, payload=payload)


    # Auth
    def auth_renew_session(self):
        self.__logger.debug('Eva.auth_renew_session called')
        return self.__http_client.auth_renew_session()


    def auth_create_session(self):
        self.__logger.debug('Eva.auth_create_session called')
        return self.__http_client.auth_create_session()


    def auth_invalidate_session(self):
        self.__logger.debug('Eva.auth_invalidate_session called')
        return self.__http_client.auth_invalidate_session()


    # Data
    def data_snapshot(self, mode='flat'):
        self.__logger.debug('Eva.data_snapshot called')
        return self.__http_client.data_snapshot(mode=mode)


    def data_snapshot_property(self, prop, mode='object'):
        self.__logger.debug('Eva.data_snapshot_property called')
        return self.__http_client.data_snapshot_property(prop, mode=mode)


    def data_servo_positions(self):
        self.__logger.debug('Eva.data_servo_positions called')
        return self.__http_client.data_servo_positions()


    # Users
    def users_get(self):
        self.__logger.debug('Eva.users_get called')
        return self.__http_client.users_get()


    # Config
    def config_update(self):
        self.__logger.debug('Eva.config_update called')
        return self.__http_client.config_update()


    # GPIO
    def gpio_set(self, pin, status):
        self.__logger.debug('Eva.gpio_set called')
        return self.__http_client.gpio_set(pin, status)


    def gpio_get(self, pin, pin_type):
        self.__logger.debug('Eva.gpio_get called')
        return self.__http_client.gpio_get(pin, pin_type)


    # Toolpaths
    def toolpaths_list(self):
        self.__logger.debug('Eva.toolpaths_list called')
        return self.__http_client.toolpaths_list()


    def toolpaths_retrieve(self, ID):
        self.__logger.debug('Eva.toolpaths_retrieve called')
        return self.__http_client.toolpaths_retrieve(ID)


    def toolpaths_save(self, name, toolpath):
        self.__logger.debug('Eva.toolpaths_save called')
        return self.__http_client.toolpaths_save(name, toolpath)


    def toolpaths_use_saved(self, toolpathId):
        self.__logger.debug('Eva.toolpaths_use_saved called')
        return self.__http_client.toolpaths_use_saved(toolpathId)


    def toolpaths_use(self, toolpathRepr):
        self.__logger.debug('Eva.toolpaths_use called')
        return self.__http_client.toolpaths_use(toolpathRepr)

    def toolpaths_delete(self, toolpathId):
        self.__logger.debug('Eva.toolpaths_delete called')
        return self.__http_client.toolpaths_delete(toolpathId)


    # Lock
    def lock_status(self):
        self.__logger.debug('Eva.lock_status called')
        return self.__http_client.lock_status()


    def lock(self, wait=True, timeout=None):
        self.__logger.debug('Eva.lock called')
        if wait:
            self.__http_client.lock_wait_for(timeout=timeout)
        else:
            self.__http_client.lock_lock()
        return self


    def lock_renew(self):
        self.__logger.debug('Eva.lock_renew called')
        return self.__http_client.lock_renew()


    def unlock(self):
        self.__logger.debug('Eva.unlock called')
        return self.__http_client.lock_unlock()


    # Control
    def control_wait_for_ready(self):
        self.__logger.debug('Eva.control_wait_for_ready called')
        return self.__http_client.control_wait_for_ready()


    def control_wait_for(self, goal):
        self.__logger.debug('Eva.control_wait_for called')
        return self.__http_client.control_wait_for(goal)


    def control_home(self, wait_for_ready=True):
        self.__logger.debug('Eva.control_home called')
        return self.__http_client.control_home(wait_for_ready=wait_for_ready)


    def control_run(self, mode='teach', loop=1, wait_for_ready=True):
        self.__logger.debug('Eva.control_run called')
        return self.__http_client.control_run(mode=mode, loop=loop, wait_for_ready=wait_for_ready)


    def control_go_to(self, joints, wait_for_ready=True, velocity=None, duration=None):
        self.__logger.debug('Eva.control_go_to called')
        return self.__http_client.control_go_to(joints, wait_for_ready=wait_for_ready, velocity=velocity, duration=duration)


    def control_pause(self, wait_for_paused=True):
        self.__logger.debug('Eva.control_pause called')
        return self.__http_client.control_pause(wait_for_paused=wait_for_paused)


    def control_resume(self, wait_for_ready=True):
        self.__logger.debug('Eva.control_resume called')
        return self.__http_client.control_resume(wait_for_ready=wait_for_ready)


    def control_cancel(self, wait_for_ready=True):
        self.__logger.debug('Eva.control_cancel called')
        return self.__http_client.control_cancel(wait_for_ready=wait_for_ready)


    def control_stop_loop(self, wait_for_ready=True):
        self.__logger.debug('Eva.control_stop_loop called')
        return self.__http_client.control_stop_loop(wait_for_ready=wait_for_ready)


    def control_reset_errors(self, wait_for_ready=True):
        self.__logger.debug('Eva.control_reset_errors called')
        return self.__http_client.control_reset_errors(wait_for_ready=wait_for_ready)


    # Calc
    def calc_forward_kinematics(self, joints, fk_type='both', tcp_config=None):
        self.__logger.debug('Eva.calc_forward_kinematics called')
        return self.__http_client.calc_forward_kinematics(joints, fk_type=fk_type, tcp_config=tcp_config)


    def calc_inverse_kinematics(self, guess, target_position, target_orientation, tcp_config=None):
        self.__logger.debug('Eva.calc_inverse_kinematics called')
        return self.__http_client.calc_inverse_kinematics(guess, target_position, target_orientation, tcp_config=tcp_config)


    def calc_nudge(self, joints, direction, offset, tcp_config=None):
        self.__logger.debug('Eva.calc_nudge called')
        return self.__http_client.calc_nudge(joints, direction, offset, tcp_config=tcp_config)


    def calc_pose_valid(self, joints, tcp_config=None):
        self.__logger.debug('Eva.calc_pose_valid called')
        return self.__http_client.calc_pose_valid(joints, tcp_config=tcp_config)


    def calc_rotate(self, joints, axis, offset, tcp_config=None):
        self.__logger.debug('Eva.calc_rotate called')
        return self.__http_client.calc_rotate(joints, axis, offset, tcp_config=tcp_config)
