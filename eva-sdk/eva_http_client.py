import json
import time
import logging
import requests

from .robot_state import RobotState
from .eva_errors import eva_error, EvaError, EvaAutoRenewError

# TODO add more granular logs using __logger
# TODO lots of sleeps in control_* de to the robot state being updated slowly after starting an action, can this be improved?


class EvaHTTPClient:
    """
    Eva HTTP client

     - host_ip (string):                The IP address of an Eva, i.e. 192.168.1.245
     - api_token (string):              A valid API token for accessing Eva, retrievable from the Choreograph config page
     - custom_logger (logging.Logger):  An *optional* logger, if not supplied the client will instantiate its own
     - request_timeout (float):         An *optional* time in seconds to wait for a request to resolve, defaults to 5
     - renew_period (int):              An *optional* time in seconds between renew session requests, defaults to 20 minutes
    """
    def __init__(self, host_ip, api_token, custom_logger=None, request_timeout=5, renew_period=60*20):
        self.host_ip = host_ip
        self.api_token = api_token
        self.request_timeout = request_timeout

        if custom_logger is not None:
            self.__logger = custom_logger
        else:
            self.__logger = logging.getLogger('eva-sdk.EvaHTTPClient:{}'.format(host_ip))

        self.session_token = None
        self.renew_period = renew_period
        self.__last_renew = time.time()

        if not 0 < renew_period < 30*60:
            raise ValueError('Session must be renewed before expiring (30 minutes)')


    def api_call_with_auth(self, *args, **kwargs):
        r = self.__api_request(*args, **kwargs)

        # Try creating a new session if we get an auth error and retrying the failed request
        if r.status_code == 401:
            self.__logger.debug('Creating a new session and retrying failed request')
            self.auth_create_session()
            return self.__api_request(*args, **kwargs)

        if self.renew_period < time.time() - self.__last_renew < 30*60:
            self.__logger.debug('Automatically renewing session')
            try:
                self.auth_renew_session()
            except EvaError as e:
                raise EvaAutoRenewError('Failed to automatically renew, got error {}'.format(str(e)))

        return r


    def __api_request(self, method, path, payload=None, headers=None, timeout=None):
        if not headers:
            headers = {'Authorization': 'Bearer {}'.format(self.session_token)}

        return requests.request(
            method, 'http://{}/api/v1/{}'.format(self.host_ip, path),
            data=payload, headers=headers,
            timeout=(timeout or self.request_timeout),
        )

    # API VERSIONS
    def api_versions(self):
        r = self.__api_request('GET', 'versions')
        if r.status_code != 200:
            eva_error('api_versions request error', r)
        return r.json()

    # AUTH
    def auth_renew_session(self):
        self.__logger.debug('Renewing session token {}'.format(self.session_token))
        # Bypass api_call_with_auth to avoid getting in a renewal loop
        r = self.__api_request('POST', 'auth/renew')

        if r.status_code == 401:
            self.session_token = None
            self.auth_create_session()

        elif r.status_code != 204:
            eva_error('auth_renew_session request error', r)

        else:
            self.__last_renew = time.time()


    def auth_create_session(self):
        self.__logger.debug('Creating session token')
        # Bypass api_call_with_auth to avoid getting in a 401 loop
        r = self.__api_request('POST', 'auth', payload=json.dumps({'token': self.api_token}), headers={})

        if r.status_code != 200:
            eva_error('auth_create_session request error', r)

        self.__last_renew = time.time()
        self.session_token = r.json()['token']
        self.__logger.debug('Created session token {}'.format(self.session_token))
        return self.session_token


    def auth_invalidate_session(self):
        self.__logger.debug('Invalidating session token {}'.format(self.session_token))
        r = self.__api_request('DELETE', 'auth')

        if r.status_code != 204:
            eva_error('auth_invalidate_session request error', r)

        self.session_token = None


    # DATA
    # TODO consider adding type for switch between flat and object modes
    def data_snapshot(self, mode='flat'):
        r = self.api_call_with_auth('GET', 'data/snapshot?mode=' + mode)
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
        r = self.api_call_with_auth('GET', 'users')
        if r.status_code != 200:
            eva_error('users_get request error', r)
        return r.json()


    # CONFIG
    def config_update(self, update):
        r = self.api_call_with_auth(
            'POST', 'config/update', update,
            headers={'Content-Type': 'application/x.automata-update'}, timeout=30
        )
        if r.status_code != 200:
            eva_error('config_update error', r)
        return r.json()


    # GPIO
    def gpio_set(self, pin, status):
        r = self.__globals_editing(keys='outputs.' + pin, values=status)
        if r.status_code != 200:
            eva_error('gpio_set error', r)


    def gpio_get(self, pin, pin_type):
        if (pin not in ['a0', 'a1', 'd0', 'd1', 'd2', 'd3', 'ee_d0', 'ee_d1', 'ee_a0', 'ee_a1']):
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
        r = self.api_call_with_auth('POST', 'data/globals?mode=' + mode, data)
        return r


    # TOOLPATHS
    def toolpaths_list(self):
        r = self.api_call_with_auth('GET', 'toolpaths')
        if r.status_code != 200:
            eva_error('toolpaths_list error', r)
        return r.json()['toolpaths']


    def toolpaths_retrieve(self, ID):
        r = self.api_call_with_auth('GET', 'toolpaths/{}'.format(ID))
        if r.status_code != 200:
            eva_error('toolpaths_retrieve error for ID {}'.format(ID), r)
        return r.json()['toolpath']


    def toolpaths_save(self, name, toolpathRepr):
        toolpaths = self.toolpaths_list()

        toolpathId = None
        for toolpath in toolpaths:
            if toolpath['name'] == name:
                toolpathId = toolpath['id']
                break

        toolpath = json.dumps({'name': name, 'toolpath': toolpathRepr})
        if toolpathId is None:
            action = 'save'
            r = self.api_call_with_auth('POST', 'toolpaths', toolpath)
        else:
            action = 'update'
            r = self.api_call_with_auth('PUT', 'toolpaths/{}'.format(toolpathId), toolpath)

        if r.status_code != 200:
            eva_error('toolpaths_save {} error'.format(action), r)
        else:
            if action == 'save':
                toolpathId = r.json()['toolpath']['id']
            return toolpathId


    def toolpaths_use_saved(self, toolpathId):
        r = self.api_call_with_auth('POST', 'toolpaths/{}/use'.format(toolpathId))
        if r.status_code != 200:
            eva_error('toolpaths_use_saved error', r)


    def toolpaths_use(self,  toolpathRepr):
        r = self.api_call_with_auth('POST', 'toolpath/use', json.dumps({'toolpath': toolpathRepr}))
        if r.status_code != 200:
            eva_error('toolpaths_use error', r)


    def toolpaths_delete(self, toolpathId):
        r = self.api_call_with_auth('DELETE', 'toolpaths/{}'.format(toolpathId))
        if r.status_code != 200:
            eva_error('toolpaths_delete error', r)

    # LOCK
    def lock_status(self):
        r = self.api_call_with_auth('GET', 'controls/lock')
        if r.status_code != 200:
            eva_error('lock_status error', r)
        return r.json()


    def lock_lock(self):
        r = self.api_call_with_auth('POST', 'controls/lock')
        if r.status_code != 200:
            eva_error('lock_lock error', r)


    def lock_renew(self):
        r = self.api_call_with_auth('PUT', 'controls/lock')
        if r.status_code != 200:
            eva_error('lock_renew error', r)


    def lock_unlock(self):
        r = self.api_call_with_auth('DELETE', 'controls/lock')
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
        r = self.api_call_with_auth('POST', 'controls/home')
        if r.status_code != 200:
            eva_error('control_home error', r)
        elif wait_for_ready:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.READY)


    def control_run(self, mode='teach', loop=1, wait_for_ready=True):
        r = self.api_call_with_auth('POST', 'controls/run', json.dumps({'mode': mode, 'loop': loop}))
        if r.status_code != 200:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            eva_error('control_run error', r)
        elif wait_for_ready:
            self.control_wait_for(RobotState.READY)


    def control_go_to(self, joints, wait_for_ready=True, velocity=None, duration=None):
        if velocity is not None:
            body = json.dumps({'joints': joints, 'velocity': velocity})
        elif duration is not None:
            body = json.dumps({'joints': joints, 'time': duration})
        else:
            body = json.dumps({'joints': joints})

        r = self.api_call_with_auth('POST', 'controls/go_to', body)
        if r.status_code != 200:
            eva_error('control_go_to error', r)
        elif wait_for_ready:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.READY)


    def control_pause(self, wait_for_paused=True):
        r = self.api_call_with_auth('POST', 'controls/pause')
        if r.status_code != 200:
            eva_error('control_pause error', r)
        elif wait_for_paused:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.PAUSED)


    def control_resume(self, wait_for_ready=True):
        r = self.api_call_with_auth('POST', 'controls/resume')
        if r.status_code != 200:
            eva_error('control_resume error', r)
        elif wait_for_ready:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.READY)


    def control_cancel(self, wait_for_ready=True):
        r = self.api_call_with_auth('POST', 'controls/cancel')
        if r.status_code != 200:
            eva_error('control_cancel error', r)
        elif wait_for_ready:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.READY)


    def control_stop_loop(self, wait_for_ready=True):
        r = self.api_call_with_auth('POST', 'controls/stop_loop')
        if r.status_code != 200:
            eva_error('control_stop_loop error', r)
        elif wait_for_ready:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.READY)


    def control_reset_errors(self, wait_for_ready=True):
        r = self.api_call_with_auth('POST', 'controls/reset_errors')
        if r.status_code != 200:
            eva_error('control_reset_errors error', r)
        elif wait_for_ready:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.READY)


    # CALCULATIONS
    def calc_forward_kinematics(self, joints, fk_type='both', tcp_config=None):
        body = {'joints': joints}
        if tcp_config is not None:
            body['tcp_config'] = tcp_config

        r = self.api_call_with_auth('PUT', 'calc/forward_kinematics', json.dumps(body))

        if r.status_code != 200:
            eva_error('calc_forward_kinematics error', r)

        if (fk_type == 'position') or (fk_type == 'orientation'):
            return r.json()['fk'][fk_type]
        elif (fk_type == 'both'):
            return r.json()['fk']
        else:
            eva_error('calc_forward_kinematics invalid fk_type {}'.format(fk_type), r)


    def calc_inverse_kinematics(self, guess, target_position, target_orientation, tcp_config=None):
        body = {'guess': guess, 'position': target_position, 'orientation': target_orientation}
        if tcp_config is not None:
            body['tcp_config'] = tcp_config

        r = self.api_call_with_auth('PUT', 'calc/inverse_kinematics', json.dumps(body))

        if r.status_code != 200:
            eva_error('inverse_kinematics error', r)
        return r.json()


    def calc_nudge(self, joints, direction, offset, tcp_config=None):
        body = {'joints': joints, 'direction': direction, 'offset': offset}
        if tcp_config is not None:
            body['tcp_config'] = tcp_config

        r = self.api_call_with_auth('PUT', 'calc/nudge', json.dumps(body))

        if r.status_code != 200:
            eva_error('calc_nudge error', r)
        return r.json()['nudge']['joints']


    def calc_pose_valid(self, joints, tcp_config=None):
        body = {'joints': joints}
        if tcp_config is not None:
            body['tcp_config'] = tcp_config

        r = self.api_call_with_auth('PUT', 'calc/pose_valid', json.dumps(body))

        if r.status_code != 200:
            eva_error('calc_pose_valid error', r)
        return r.json()['pose']['valid']


    def calc_rotate(self, joints, axis, offset, tcp_config=None):
        body = {'joints': joints, 'axis': axis, 'offset': offset}
        if tcp_config is not None:
            body['tcp_config'] = tcp_config

        r = self.api_call_with_auth('PUT', 'calc/rotate', json.dumps(body))

        if r.status_code != 200:
            eva_error('calc_rotate error', r)
        return r.json()
