import json
import time
import logging
import requests

from .robot_state import RobotState
from .eva_errors import eva_error, EvaError

# TODO add more granular logs using __logger
# TODO lots of sleeps in control_* de to the robot state being updated slowly after starting an action, can this be improved?


class EvaHTTPClient:
    """
    Eva HTTP client

     - host_ip (string):                The IP address of an Eva, i.e. 192.168.1.245
     - token (string):                  A valid token for accessing Eva, retrievable from the Choreograph config page
     - custom_logger (logging.Logger):  An *optional* logger, if not supplied the client will instantiate its own
     - request_timeout (float):         An *optional* time in seconds to wait for a request to resolve, defaults to 5
    """
    def __init__(self, host_ip, token, custom_logger=None, request_timeout=5):
        self.host_ip = host_ip
        self.token = token
        self.request_timeout = request_timeout

        if custom_logger is not None:
            self.__logger = custom_logger
        else:
            self.__logger = logging.getLogger('automata.EvaHTTPClient:{}'.format(host_ip))


    def api_call(self, method, path, payload=None):
        headers = {
            'Authorization': 'API {}'.format(self.token),
        }
        return requests.request(
            method, 'http://{}/api/v1/{}'.format(self.host_ip, path),
            data=payload, headers=headers,
            timeout=self.request_timeout,
        )


    # DATA
    # TODO consider adding type for switch between flat and object modes
    def data_snapshot(self, mode='flat'):
        r = self.api_call('GET', 'data/snapshot?mode=' + mode)
        if r.status_code != 200:
            eva_error('data_snapshot request error', r)
        return r.json()['snapshot']


    def data_snapshot_property(self, prop, mode='object'):
        snapshot = self.data_snapshot(mode=mode)
        if prop in snapshot:
            return snapshot[prop]
        else:
            eva_error('data_snapshot_property request error, property {} not found'.format(prop))


    def data_servo_positions(self):
        return self.data_snapshot_property('servos.telemetry.position')


    # USERS
    def users_get(self):
        r = self.api_call('GET', 'users')
        if r.status_code != 200:
            eva_error('users_get request error', r)
        return r.json()


    # CONFIG
    # TODO implement unfinished routes
    def config_update(self):
        return NotImplementedError


    # GPIO
    def gpio_set(self, pin, status):
        r = self.__globals_editing(keys='outputs.' + pin, values=status)
        if r.status_code != 200:
            eva_error('gpio_set error', r)


    def gpio_get(self, pin, pin_type):
        if (pin not in ['a0', 'a1', 'd0', 'd1', 'd2', 'd3']):
            eva_error('gpio_get error, no such pin ' + pin)
        if (pin_type not in ['input', 'output']):
            eva_error('gpio_get error, pin_type must be "input" or "output"')
        return self.data_snapshot_property('global.{}s'.format(pin_type))[pin]


    # GPIO helper function
    def __globals_editing(self, keys, values, mode='flat'):
        data = {'changes': []}
        if (isinstance(keys, list) and isinstance(values, list)):
            [data['changes'].append({'key': c[0], 'value': c[1]}) for c in zip(keys, values)]
        else:
            data['changes'].append({'key': keys, 'value': values})
        data = json.dumps(data)
        r = self.api_call('POST', 'data/globals?mode=' + mode, data)
        return r


    # TOOLPATHS
    def toolpaths_list(self):
        r = self.api_call('GET', 'toolpaths')
        if r.status_code != 200:
            eva_error('toolpaths_list error', r)
        return r.json()['toolpaths']


    def toolpaths_retrieve(self, ID):
        r = self.api_call('GET', 'toolpaths/{}'.format(ID))
        if r.status_code != 200:
            eva_error('toolpaths_retrieve error for ID {}'.format(ID), r)
        return r.json()['toolpath']


    def toolpaths_save(self, name, toolpath):
        toolpaths = self.toolpaths_list()

        toolpathId = None
        for toolpath in toolpaths:
            if toolpath['name'] == name:
                toolpathId = toolpath['id']
                break

        toolpath = json.dumps({'name': name, 'toolpath': toolpath})
        if toolpathId == None:
            action = 'save'
            r = self.api_call('POST', 'toolpaths', toolpath)
        else:
            action = 'update'
            r = self.api_call('PUT', 'toolpaths/{}'.format(toolpathId), toolpath)

        if r.status_code != 200:
            eva_error('toolpaths_save {} error'.format(action), r)
        else:
            if action == 'save':
                toolpathId = r.json()['toolpath']['id']
            return toolpathId


    def toolpaths_use_saved(self, toolpathId):
        r = self.api_call('POST', 'toolpaths/{}/use'.format(toolpathId))
        if r.status_code != 200:
            eva_error('toolpaths_use_saved error', r)


    def toolpaths_use(self,  toolpathRepr):
        r = self.api_call('POST', 'toolpath/use', json.dumps({'toolpath': toolpathRepr}))
        if r.status_code != 200:
            eva_error('toolpaths_use error', r)


    def toolpaths_delete(self, toolpathId):
        r = self.api_call('DELETE', 'toolpaths/{}'.format(toolpathId))
        if r.status_code != 200:
            eva_error('toolpaths_delete error', r)

    # LOCK
    def lock_status(self):
        r = self.api_call('GET', 'controls/lock')
        if r.status_code != 200:
            eva_error('lock_status error', r)
        return r.json()


    def lock_lock(self):
        r = self.api_call('POST', 'controls/lock')
        if r.status_code != 200:
            eva_error('lock_lock error', r)


    def lock_renew(self):
        r = self.api_call('PUT', 'controls/lock')
        if r.status_code != 200:
            eva_error('lock_renew error', r)


    def lock_unlock(self):
        r = self.api_call('DELETE', 'controls/lock')
        if r.status_code != 200:
            eva_error('lock_unlock error', r)


    def lock_wait_for(self, interval_sec=2, timeout=None):
        if self.lock_status()['owner'] == 'you':
            return

        if timeout is not None:
            timeoutT = time.time() + timeout
        while True:
            try:
                self.lock_lock()
                return
            except Exception as e:
                if not isinstance(e, EvaError):
                    raise e
                pass

            if timeout is not None:
                if timeoutT < time.time():
                    eva_error('lock_wait_for timeout triggered')

            time.sleep(interval_sec)


    # CONTROLS/STATE
    def control_wait_for(self, goal, interval_sec=1):
        """
        control_wait_for will poll Eva's state, waiting for Eva to reach the goal state
        """
        parsed_goal = RobotState(goal)

        while True:
            robot_state = RobotState(self.data_snapshot()['control.state'])

            if robot_state == RobotState.ERROR:
                eva_error('Eva is in error control state')
            elif robot_state == parsed_goal:
                return
            
            time.sleep(interval_sec)


    def control_wait_for_ready(self):
        """
        control_wait_for_ready will poll Eva's state, waiting for Eva to reach "Ready" state
        """
        self.control_wait_for(RobotState.READY)


    def control_home(self, wait_for_ready=True):
        r = self.api_call('POST', 'controls/home')
        if r.status_code != 200:
            eva_error('control_home error', r)
        elif wait_for_ready:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.READY)


    def control_run(self, loop=1, wait_for_ready=True):
        r = self.api_call('POST', 'controls/run', json.dumps({'loop': loop}))
        if r.status_code != 200:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            eva_error('control_run error', r)
        elif wait_for_ready:
            self.control_wait_for(RobotState.READY)


    def control_go_to(self, joints, wait_for_ready=True):
        r = self.api_call('POST', 'controls/go_to', json.dumps({'joints': joints}))
        if r.status_code != 200:
            eva_error('control_go_to error', r)
        elif wait_for_ready:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.READY)


    def control_pause(self, wait_for_paused=True):
        r = self.api_call('POST', 'controls/pause')
        if r.status_code != 200:
            eva_error('control_pause error', r)
        elif wait_for_paused:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.PAUSED)


    def control_resume(self, wait_for_ready=True):
        r = self.api_call('POST', 'controls/resume')
        if r.status_code != 200:
            eva_error('control_resume error', r)
        elif wait_for_ready:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.READY)


    def control_cancel(self, wait_for_ready=True):
        r = self.api_call('POST', 'controls/cancel')
        if r.status_code != 200:
            eva_error('control_cancel error', r)
        elif wait_for_ready:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.READY)


    def control_stop_loop(self, wait_for_ready=True):
        r = self.api_call('POST', 'controls/stop_loop')
        if r.status_code != 200:
            eva_error('control_stop_loop error', r)
        elif wait_for_ready:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.READY)


    def control_reset_errors(self, wait_for_ready=True):
        r = self.api_call('POST', 'controls/reset_errors')
        if r.status_code != 200:
            eva_error('control_reset_errors error', r)
        elif wait_for_ready:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.READY)


    # CALCULATIONS
    def calc_forward_kinematics(self, joints, fk_type='both'):
        r = self.api_call('PUT', 'calc/forward_kinematics', json.dumps({'joints': joints}))

        if r.status_code != 200:
            eva_error('calc_forward_kinematics error', r)
        
        if (fk_type == 'position') or (fk_type == 'orientation'):
            return r.json()['fk'][fk_type]
        elif (fk_type == 'both'):
            return r.json()['fk']
        else:
            eva_error('calc_forward_kinematics invalid fk_type {}'.format(fk_type), r)


    def calc_inverse_kinematics(self, guess, target_position, target_orientation):
        payload = json.dumps({'guess': guess, 'position': target_position, 'orientation': target_orientation})
        r = self.api_call('PUT', 'calc/inverse_kinematics', payload)

        if r.status_code != 200:
            eva_error('inverse_kinematics error', r)
        return r.json()


    def calc_nudge(self, joints, direction, offset):
        payload = json.dumps({'joints': joints, 'direction': direction, 'offset': offset})
        r = self.api_call('PUT', 'calc/nudge', payload)

        if r.status_code != 200:
            eva_error('calc_nudge error', r)
        return r.json()['nudge']['joints']


    def calc_pose_valid(self, joints):
        payload = json.dumps({'joints': joints})
        r = self.api_call('PUT', 'calc/pose_valid', payload)

        if r.status_code != 200:
            eva_error('calc_pose_valid error', r)
        return r.json()['pose']['valid']


    def calc_rotate(self, joints, axis, offset):
        payload = json.dumps({'joints': joints, 'axis': axis, 'offset': offset})
        r = self.api_call('PUT', 'calc/rotate', payload)

        if r.status_code != 200:
            eva_error('calc_rotate error', r)
        return r.json()
