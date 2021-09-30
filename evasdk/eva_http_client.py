import json
import time
import logging
import requests
import importlib.util
from typing import Union
from .robot_state import RobotState
from .eva_errors import eva_error, EvaError, EvaAutoRenewError
from .version import __version__, sdk_is_compatible_with_robot

# TODO: too big, install it manually if you want it
has_pyt3d = importlib.util.find_spec('pytransform3d')
if has_pyt3d:
    import pytransform3d.rotations as pyrot  # type: ignore

# TODO add more granular logs using __logger
# TODO lots of sleeps in control_* de to the robot state being updated slowly after starting an action, can this be improved?
# TODO technically, the default request timeout of the API is 60s, should we update `request_timeout`?


class EvaHTTPClient:
    __N_DIGITS = 8

    """
    Eva HTTP client

     - host_ip (string):                The IP address of an Eva, i.e. 192.168.1.245
     - api_token (string):              A valid API token for accessing Eva, retrievable from the Choreograph config page
     - custom_logger (logging.Logger):  An *optional* logger, if not supplied the client will instantiate its own
     - request_timeout (float):         An *optional* time in seconds to wait for a request to resolve, defaults to 5
     - renew_period (int):              An *optional* time in seconds between renew session requests, defaults to 20 minutes
    """
    def __init__(self, host_ip, api_token, custom_logger=None, request_timeout=5, renew_period=60 * 20):
        self.host_ip = host_ip
        self.api_token = api_token
        self.request_timeout = request_timeout

        if custom_logger is not None:
            self.__logger = custom_logger
        else:
            self.__logger = logging.getLogger('evasdk.EvaHTTPClient:{}'.format(host_ip))

        self.session_token = None
        self.renew_period = renew_period
        self.__last_renew = time.time()

        if not 0 < renew_period < 30 * 60:
            raise ValueError('Session must be renewed before expiring (30 minutes)')


    def api_call_with_auth(self, *args, **kwargs):

        r = self.__api_request(*args, **kwargs)

        # Try creating a new session if we get an auth error and retrying the failed request
        if r.status_code == 401:
            self.__logger.debug('Creating a new session and retrying failed request')
            self.auth_create_session()
            return self.__api_request(*args, **kwargs)

        if self.renew_period < time.time() - self.__last_renew < 30 * 60:
            self.__logger.debug('Automatically renewing session')
            try:
                self.auth_renew_session()
            except EvaError as e:
                raise EvaAutoRenewError('Failed to automatically renew, got error {}'.format(str(e)))

        return r

    def api_call_no_auth(self, method, path, payload=None, **kwargs):
        return self.__api_request(method, path, payload=payload, add_auth=False, **kwargs)

    def __api_request(self, method, path, payload=None, headers={}, timeout=None, version='v1', add_auth=True):
        if headers:
            headers = headers.copy()

        if add_auth:
            headers['Authorization'] = f'Bearer {self.session_token}'
        headers['User-Agent'] = f'Automata EvaSDK/{__version__} (Python)'

        api_path = path
        if version is not None:
            api_path = f'{version}/{path}'

        return requests.request(
            method, 'http://{}/api/{}'.format(self.host_ip, api_path),
            data=payload, headers=headers,
            timeout=(timeout or self.request_timeout),
        )

    # API VERSIONS
    def api_versions(self):
        r = self.api_call_no_auth('GET', 'versions', version=None)
        if r.status_code != 200:
            eva_error('api_versions request error', r)
        return r.json()

    def name(self):
        r = self.api_call_no_auth('GET', 'name')
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

        err = self._check_version_compatibility()
        if err is not None:
            self.__logger.error(f'incompatible SDK: {err}')

        r = self.api_call_no_auth('POST', 'auth', payload=json.dumps({'token': self.api_token}))

        if r.status_code != 200:
            eva_error('auth_create_session request error', r)

        self.__last_renew = time.time()
        self.session_token = r.json()['token']
        self.__logger.debug('Created session token {}'.format(self.session_token))
        return self.session_token


    def auth_invalidate_session(self):
        self.__logger.debug('Invalidating session token {}'.format(self.session_token))
        # Bypass api_call_with_auth to avoid getting in a 401 loop
        r = self.__api_request('DELETE', 'auth')

        if r.status_code != 204:
            eva_error('auth_invalidate_session request error', r)

        self.session_token = None


    # DATA
    def data_snapshot(self):
        r = self.api_call_with_auth('GET', 'data/snapshot')
        if r.status_code != 200:
            eva_error('data_snapshot request error', r)
        return r.json()['snapshot']


    def data_snapshot_property(self, prop):
        snapshot = self.data_snapshot()
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
            headers={'Content-Type': 'application/x.automata-update'}, timeout=120
        )
        if r.status_code != 200:
            eva_error('config_update error', r)
        return r.json()


    # GPIO
    def gpio_set(self, pin, status):
        r = self._globals_edit(keys='outputs.' + pin, values=status)
        if r.status_code != 200:
            eva_error('gpio_set error', r)


    def gpio_get(self, pin, pin_type):
        if (pin not in ['a0', 'a1', 'd0', 'd1', 'd2', 'd3', 'ee_d0', 'ee_d1', 'ee_a0', 'ee_a1']):
            eva_error('gpio_get error, no such pin ' + pin)
        if (pin_type not in ['input', 'output']):
            eva_error('gpio_get error, pin_type must be "input" or "output"')
        return self.data_snapshot_property('global.{}s'.format(pin_type))[pin]


    def _globals_edit(self, keys, values):
        data = {'changes': []}
        if (isinstance(keys, list) and isinstance(values, list)):
            data['changes'] = [{'key': k, 'value': v} for k, v in zip(keys, values)]
        else:
            data['changes'].append({'key': keys, 'value': values})
        data = json.dumps(data)
        return self.api_call_with_auth('POST', 'data/globals', data)


    def globals_edit(self, keys, values):
        r = self._globals_edit(keys, values)
        if r.status_code != 200:
            eva_error('globals_edit error', r)
        return r.json()


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
        r = self.api_call_with_auth('POST', 'toolpaths/{}/use'.format(toolpathId), timeout=300)
        if r.status_code != 200:
            eva_error('toolpaths_use_saved error', r)


    def toolpaths_use(self, toolpathRepr):
        r = self.api_call_with_auth('POST', 'toolpath/use', json.dumps({'toolpath': toolpathRepr}), timeout=300)
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
            robot_state = RobotState(self.data_snapshot()['control']['state'])

            if robot_state == RobotState.ERROR:
                eva_error('Eva is in error control state')
            if robot_state == RobotState.COLLISION:
                eva_error('Eva has encountered a collision. Please acknowledge collision.')
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


    def control_run(self, loop=1, wait_for_ready=True, mode='teach'):
        r = self.api_call_with_auth('POST', 'controls/run', json.dumps({'mode': mode, 'loop': loop}))
        if r.status_code != 200:
            eva_error('control_run error', r)
        elif wait_for_ready:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.READY)


    def control_go_to(self, joints, wait_for_ready=True, max_speed=None, time_sec=None, mode='teach'):
        body = {'joints': joints, 'mode': mode}
        if max_speed is not None:
            body['max_speed'] = max_speed
        if time is not None:
            body['time'] = time_sec

        r = self.api_call_with_auth('POST', 'controls/go_to', json.dumps(body))
        if r.status_code != 200:
            eva_error('control_go_to error', r)
        elif wait_for_ready:
            time.sleep(0.1)     # sleep for small period to avoid race condition between cache updating and reading state
            self.control_wait_for(RobotState.READY)


    def control_pause(self, wait_for_paused=True):
        r = self.api_call_with_auth('POST', 'controls/pause')
        if r.status_code != 200:
            eva_error('control_pause error', r)
        elif wait_for_paused:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.PAUSED)


    def control_resume(self, wait_for_running=True):
        r = self.api_call_with_auth('POST', 'controls/resume')
        if r.status_code != 200:
            eva_error('control_resume error', r)
        elif wait_for_running:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.RUNNING)


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
        if r.status_code != 204:
            eva_error('control_reset_errors error', r)
        elif wait_for_ready:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.READY)

    # COLLISION DETECTION
    def control_configure_collision_detection(self, enabled, sensitivity):
        """
        Allows toggling on/off and setting the sensitivity of collision detection
        """
        if sensitivity not in ['low', 'medium', 'high']:
            raise ValueError('collision_detection error, no such sensitivity ' + sensitivity)
        if enabled not in [True, False]:
            raise ValueError('collision_detection error, must be True/False')
        r = self.api_call_with_auth('POST', 'controls/collision_detection',
                                    json.dumps({'enabled': enabled, 'sensitivity': sensitivity}))
        if r.status_code != 204:
            eva_error('control_collision_detection error', r)

    def control_acknowledge_collision(self, wait_for_ready=True):
        """
        When a collision is encountered, it must be acknowledged before the robot can be reset
        """
        r = self.api_call_with_auth('POST', 'controls/acknowledge_collision')
        if r.status_code != 204:
            eva_error('control_acknowledge_collision error', r)
        elif wait_for_ready:
            time.sleep(0.1)     # sleep for small period to avoid race condition between updating cache and reading state
            self.control_wait_for(RobotState.READY)

    # CALCULATIONS
    def __check_calculation(self, r, name, kind):
        res = r.json()
        if res[kind]['result'] != 'success':
            eva_error(f'{name} error: {res[kind]["error"]}')
        return res[kind]

    def calc_forward_kinematics(self, joints, fk_type=None, tcp_config=None):
        if fk_type is not None:
            self.__logger.warn('deprecated fk_type keyword, now all FK data is being returned')

        body = {'joints': joints}
        if tcp_config is not None:
            body['tcp_config'] = tcp_config

        r = self.api_call_with_auth('PUT', 'calc/forward_kinematics', json.dumps(body))

        if r.status_code != 200:
            eva_error('calc_forward_kinematics error', r)
        return self.__check_calculation(r, 'calc_forward_kinematics', 'fk')

    def __ensure_pyt3d(self):
        if not has_pyt3d:
            raise ImportError('''this feature is provided by `pytransform3d`, which we do not ship by default anymore due to its dependencies

If you require this feature, just install it yourself (e.g. `pip3 install pytransform3d`, add it to your `Pipfile`, etc)
''')

    def __normalize(self, vec):
        if has_pyt3d:
            return [round(num, self.__N_DIGITS) for num in pyrot.check_quaternion(vec)]
        norm = sum(vec)
        if norm == 0:
            norm = 1
        return [round(n / norm, self.__N_DIGITS) for n in vec]

    def calc_inverse_kinematics(self, guess, target_position, target_orientation, tcp_config=None,
                                orientation_type=None):
        """
        End-effector orientation (target_orientation) can be provided in several standard formats,
        by specifying the orinetation_type (default is None):
        - 'matrix': rotation matrix -> 3x3 array, in row major order
        - 'axis_angle': axis angle -> {'angle': float, 'x': float, 'y': float, 'z': float}
        - 'euler_zyx': {yaw, pitch, roll} Euler (Tait-Bryan) angles -> {'yaw': float, 'pitch': float, 'roll': float}
        - 'quat': quaternion -> {'w': float, 'x': float, 'y': float, 'z': float}
        - None: defaults to quaternion
        Conversion relies on pytransform3d library
        """
        quat_not_normed = None

        if orientation_type == 'matrix':
            self.__ensure_pyt3d()
            quat_not_normed = pyrot.quaternion_from_matrix(pyrot.check_matrix(target_orientation))
        elif orientation_type == 'axis_angle':
            self.__ensure_pyt3d()
            axis_angle = [target_orientation['x'], target_orientation['y'], target_orientation['z'],
                          target_orientation['angle']]
            quat_not_normed = pyrot.quaternion_from_axis_angle(pyrot.check_axis_angle(axis_angle))
        elif orientation_type == 'euler_zyx':
            self.__ensure_pyt3d()
            euler_zyx = [target_orientation['yaw'], target_orientation['pitch'], target_orientation['roll']]
            matrix = pyrot.matrix_from_euler_zyx(euler_zyx)
            quat_not_normed = pyrot.quaternion_from_matrix(pyrot.check_matrix(matrix))
        elif orientation_type == 'quat' or orientation_type is None:
            quat_not_normed = [target_orientation['w'], target_orientation['x'], target_orientation['y'],
                               target_orientation['z']]
        else:
            eva_error(f'calc_inverse_kinematics invalid "{orientation_type}" orientation_type')

        quat_normed = self.__normalize(quat_not_normed)
        quaternion = {'w': quat_normed[0], 'x': quat_normed[1], 'y': quat_normed[2], 'z': quat_normed[3]}

        body = {'guess': guess, 'position': target_position, 'orientation': quaternion}
        if tcp_config is not None:
            body['tcp_config'] = tcp_config

        r = self.api_call_with_auth('PUT', 'calc/inverse_kinematics', json.dumps(body))

        if r.status_code != 200:
            eva_error('inverse_kinematics error', r)
        return self.__check_calculation(r, 'calc_inverse_kinematics', 'ik')['joints']

    def calc_nudge(self, joints, direction, offset, tcp_config=None):
        body = {'joints': joints, 'direction': direction, 'offset': offset}
        if tcp_config is not None:
            body['tcp_config'] = tcp_config

        r = self.api_call_with_auth('PUT', 'calc/nudge', json.dumps(body))

        if r.status_code != 200:
            eva_error('calc_nudge error', r)
        return self.__check_calculation(r, 'calc_nudge', 'nudge')['joints']

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
        return self.__check_calculation(r, 'calc_rotate', 'rotate')['joints']


    def _check_version_compatibility(self) -> Union[str, None]:
        """Checks the current version of the application against that of Eva's software version.
        Returns:
            Union[str, None]: error message, None if versions are compatible.
        """
        version_r = self.api_call_no_auth('GET', 'versions', version=None)
        if version_r.status_code != 200:
            return 'request error when fetching versions'
        robot_version = version_r.json()['robot']
        err = sdk_is_compatible_with_robot(robot_version)
        if err is not None:
            return err
        return None
