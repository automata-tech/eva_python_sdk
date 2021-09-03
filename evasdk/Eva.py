import logging

from .helpers import (strip_ip)
from .eva_http_client import EvaHTTPClient
from .eva_locker import EvaWithLocker
from .eva_ws import Websocket


class Eva:
    """
    The Eva class represents a self updating snapshot of Eva at any one time.
    Once initialised Eva connects to Eva via a websocket and keeps the current
    state of the robot using the websocket update messages.
    """
    def __init__(self, host_ip, token, request_timeout=5, renew_period=60 * 20):
        parsed_host_ip = strip_ip(host_ip)

        self.__http_client = EvaHTTPClient(parsed_host_ip, token, request_timeout=request_timeout,
                                           renew_period=renew_period)
        self.__logger = logging.getLogger('evasdk.Eva:{}'.format(host_ip))

        self.__eva_locker = EvaWithLocker(self)


    def set_request_timeout(self, request_timeout):
        """Sets default request timeout for API commands

        Args:
            request_timeout: time in seconds

        Returns:
            None
        """
        self.__http_client.request_timeout = request_timeout


    # ---------------------------------------------- Constants ----------------------------------------------
    __TEACH_RENEW_PERIOD = 3


    # --------------------------------------------- Websocket -----------------------------------------------
    def websocket(self):
        # Ensure we have a session token
        # might use the result in the future to give the initial state to consumers
        self.__http_client.data_snapshot()
        host_uri = f'ws://{self.__http_client.host_ip}/api/v1/data/stream'
        subprotocols = [f'SessionToken_{self.__http_client.session_token}', "object"]
        return Websocket(host_uri, subprotocols, timeout=self.__http_client.request_timeout)

    # --------------------------------------------- Lock Holder ---------------------------------------------
    def __enter__(self):
        self.__eva_locker.__enter__()
        return self


    def __exit__(self, type, value, traceback):
        self.__eva_locker.__exit__(type, value, traceback)


    # --------------------------------------------- HTTP HANDLERS ---------------------------------------------
    def api_call_with_auth(self, method, path, payload=None, headers={}, timeout=None, version='v1'):
        """Makes a direct API call to EVA to endpoints that require authentication

        Note:
            This is used within the SDK and will unlikely be used externally.
            You should not need to use this at all.

        Args:
            method: GET, POST, DELETE, etc
            path: URL path of API endpoint
            payload: dict payload
            headers: option to add additional headers
            timeout: time to wait in seconds before raising an exception
            version: API server version

        Returns:
            dict: containing results of API call

        Raises:
            EvaError: If it is not successful

        Example:
            >>> eva.api_call_with_auth('GET', 'controls/lock')
            {'owner': 'none', 'status': 'unlocked'}
        """
        self.__logger.debug('Eva.api_call_with_auth {} {}'.format(method, path))
        return self.__http_client.api_call_with_auth(method, path, payload=payload, headers=headers, timeout=timeout,
                                                     version=version)

    def api_call_no_auth(self, method, path, payload=None, headers={}, timeout=None, version='v1'):
        """Makes a direct API call to EVA to endpoints that do not require authentication

        Note:
            This is used within the SDK and will unlikely be used externally.
            You should not need to use this at all.

        Args:
            method: GET, POST, DELETE, etc
            path: URL path of API endpoint
            payload: dict payload
            headers: option to add additional headers
            timeout: time to wait in seconds before raising an exception
            version: API server version

        Returns:
            dict: containing results of API call

        Raises:
            EvaError: If it is not successful

        Example:
            >>> eva.api_call_no_auth('GET', 'name')
            {'name': 'Cunning Moscow Baker'}
        """
        self.__logger.debug('Eva.api_call_no_auth {} {}'.format(method, path))
        return self.__http_client.api_call_no_auth(method, path, payload=payload, headers=headers, timeout=timeout,
                                                   version=version)


    # Global
    def versions(self):
        """Gets the API versions supported by the server and the Choreograph version installed on the robot.

        Returns:
            dict: API version supported, robot choreograph version

        Raises:
            EvaError: If it is not successful

        Example:
            >>> eva.versions()
            {'APIs': ['v1'], 'robot': '4.10.0'}
        """
        self.__logger.debug('Eva.versions called')
        return self.__http_client.api_versions()

    def name(self):
        """Gets the name of the robot.

        Returns:
            dict: robot name

        Example:
            >>> eva.name()
            {'name': 'Cunning Moscow Baker'}
        """
        self.__logger.debug('Eva.name called')
        return self.__http_client.name()

    # Auth
    def auth_renew_session(self):
        """Renews the authenticated session token.

        Note:
            Should not need to be called as it is handled automatically whenever an api_call_with_auth() is used.

        Returns:
            None

        Raises:
            EvaError: If it is not successful
        """
        self.__logger.debug('Eva.auth_renew_session called')
        return self.__http_client.auth_renew_session()


    def auth_create_session(self):
        """Creates a session token token.

        Note:
            Should not need to be called as it is handled internally

        Returns:
            str: session_token

        Raises:
            EvaError: If it is not successful

        Example:
            >>> eva.auth_create_session()
            c8c3a36b-4fce-4df2-b795-6bf5629ff48d
        """
        self.__logger.debug('Eva.auth_create_session called')
        return self.__http_client.auth_create_session()


    def auth_invalidate_session(self):
        """Deletes/invalidates the API session token.

        Raises:
            EvaError: If it is not successful

        Returns:
            None
        """
        self.__logger.debug('Eva.auth_invalidate_session called')
        return self.__http_client.auth_invalidate_session()


    # Data
    def data_snapshot(self):
        """Returns a nested dictionary of the status of the robot.

        Returns:
            dict: Multiple nested dictionary

        Raises:
            EvaError: If it is not successful
        """
        self.__logger.debug('Eva.data_snapshot called')
        return self.__http_client.data_snapshot()


    def data_snapshot_property(self, prop):
        """Returns a property from the data_snapshot dict.

        Args:
            prop: property within the data_snapshot() nested dictionary

        Returns:
            dict: dictionary object specified

        Raises:
            EvaError: If the property is not found within the data_snapshot() dict

        Example:
            >>> eva.data_snapshot_property('control')
            {'loop_count': 0, 'loop_target': 0, 'run_mode': 'not_running', 'state': 'error'}
        """
        self.__logger.debug('Eva.data_snapshot_property called')
        return self.__http_client.data_snapshot_property(prop)


    def data_servo_positions(self):
        """Returns a list of current joint angles in radians

        Note:
            This function uses the data_snapshot_property() to return the servo positions
            from the data_snapshot() function.

        Returns:
            list: list of 6 joint angles in radians

        Raises:
            EvaError: If the property is not found within the data_snapshot() dict

        Example:
            >>> eva.data_servo_positions()
            [-0.004506206139, 0.20661434531, -0.441608190, -0.00038350690, -1.9729512929, 2.1852223873]
        """
        self.__logger.debug('Eva.data_servo_positions called')
        return self.__http_client.data_servo_positions()


    # Users
    def users_get(self):
        """Returns the list within a dictionary of users.

        Returns:
            dict: a list of dictionaries containing user id, email, and role.

        Raises:
            EvaError: If it is not successful

        Example:
            >>> eva.users_get()
            {'users': [{'id': 1, 'email': 'test@automata.tech', 'role': 'admin'},
             {'id': 2, 'email': 'euan@automata.tech', 'role': 'user'}]}
        """
        self.__logger.debug('Eva.users_get called')
        return self.__http_client.users_get()


    # Config
    def config_update(self, update):
        """Applies choreograph update file to robot.

        Note:
            Requires the lock. See example.

        Args:
            update: AUT / update file

        Returns:
            None

        Raises:
            EvaError: If it is not successful

        Example:
            >>> with open("rel-4.10.0.aup", 'rb') as update:
            >>>     with eva.lock():
            >>>         eva.config_update(update)
        """
        self.__logger.debug('Eva.config_update called')
        return self.__http_client.config_update(update)


    # GPIO
    def gpio_set(self, pin, status):
        """Changes the state of the output pin

        Args:
            pin: output pin name that is being changed
            status: state requested.

        Returns:
            None

        Raises:
            EvaError: If it is not successful

        Example:
            >>> robot.gpio_get('d0', 'output')
            False
            >>> robot.gpio_set('d0', True)
            >>> robot.gpio_get('d0', 'output')
            True
        """
        self.__logger.debug('Eva.gpio_set called')
        return self.__http_client.gpio_set(pin, status)


    def gpio_get(self, pin, pin_type):
        """Gets the state of output/input pin

        Args:
            pin: name of the pin
            pin_type: input or output pin type

        Returns:
            bool or float: depending on pin_type

        Raises:
            EvaError: gpio_get error, no such pin (if the pin does not exist)
            EvaError: gpio_get error, pin_type must be "input" or "output"

        Example:
            >>> robot.gpio_get('d0', 'output')
            True
            >>> robot.gpio_get('a0', 'input')
            0.018
        """
        self.__logger.debug('Eva.gpio_get called')
        return self.__http_client.gpio_get(pin, pin_type)

    def globals_edit(self, keys, values):
        """Allows editing of exposed global values

        Note:
            This is not used directly within the SDK.

        Args:
            keys: a list of keys to change
            values: a list of the associated valuea to change global to

        Returns:
            dict: of the data requested

        Raises:
            EvaError: If it is not successful
        """
        self.__logger.debug('Eva.globals_edit called')
        return self.__http_client.globals_edit(keys, values)

    # Toolpaths
    def toolpaths_list(self):
        """Gets a list of saved toolpaths on the robot

        Returns:
            list: a list of dictionaries containing toolpath id, name, and hash.

        Raises:
            EvaError: If it is not successful

        Example:
            >>> eva.toolpaths_list()
            [{'id': 1, 'name': 'test_1', 'hash': 'cacc3c5ca8ada838ee86f703487151edcbae4b9177cf138c8908d12b614b6313'},
            {'id': 2, 'name': 'test_2', 'hash': '9bedb2a17cfc965d8a208c2697fee1a5455c558ec8e5aadb2ce4b20dfa016363'}]
        """
        self.__logger.debug('Eva.toolpaths_list called')
        return self.__http_client.toolpaths_list()


    def toolpaths_retrieve(self, ID):
        """Retrieves the toolpath using toolpath ID on the robot

        Args:
            ID: id integer of the toolpath called upon

        Returns:
            dict: of the toolpath requested

        Raises:
            EvaError: If it is not successful

        Example:
            >>> eva.toolpath_retrieve(1)
            {'id': 1, 'name': 'test_1', 'hash': 'cacc3c5ca8ada838ee86f703487151edcbae4b9177cf138c8908d12b614b6313',
            'toolpath': {'metadata': {'version': 2, 'default_max_speed': 0.25, 'next_label_id': 2,
            'analog_modes': {'i0': 'voltage', 'i1': 'voltage', 'o0': 'voltage', 'o1': 'voltage'}, 'payload': 0},
            'waypoints': [{'joints': [0, 0.5235988, -1.7453293, 0, -1.9198622, 0], 'label_id': 1}],
            'timeline': [{'type': 'home', 'waypoint_id': 0}]}}
        """
        self.__logger.debug('Eva.toolpaths_retrieve called')
        return self.__http_client.toolpaths_retrieve(ID)


    def toolpaths_save(self, name, toolpath):
        """Saves a toolpath file to the robot

        Args:
            name: string to assign to the toolpath name
            toolpath: dictionary formatted toolpath data

        Returns:
            toolpathId: toolpath ID number on the toolpaths_list() if successful

        Raises:
            EvaError: If it is not successful
        """
        self.__logger.debug('Eva.toolpaths_save called')
        return self.__http_client.toolpaths_save(name, toolpath)


    def toolpaths_use_saved(self, toolpathId):
        """Sets the active toolpath from the toolpaths_list

        Args:
            toolpathId: id integer of the toolpath called upon

        Returns:
            None

        Raises:
            EvaError: If it is not successful
        """
        self.__logger.debug('Eva.toolpaths_use_saved called')
        return self.__http_client.toolpaths_use_saved(toolpathId)


    def toolpaths_use(self, toolpathRepr):
        """Sets the toolpath passed to it as the active toolpath which can be homed, run, paused, and stopped.

        Args:
            toolpathRepr: dictionary containing all toolpath data

        Returns:
            None

        Raises:
            EvaError: If it is not successful

        Note:
            This does not save the toolpath to the toolpaths_list
        """
        self.__logger.debug('Eva.toolpaths_use called')
        return self.__http_client.toolpaths_use(toolpathRepr)

    def toolpaths_delete(self, toolpathId):
        """Deletes a toolpath specified from the toolpaths stored on the robot

        Args:
            ID: id integer of the toolpath from the toolpaths list

        Returns:
            None
        """
        self.__logger.debug('Eva.toolpaths_delete called')
        return self.__http_client.toolpaths_delete(toolpathId)


    # Lock
    def lock_status(self):
        """Indicates status and owner of the lock

        Raises:
            EvaError: If it is not successful

        Returns:
            dict: containing lock user/owner & status of the lock

        Example:
            >>> eva.lock_status()
            {'owner': 'none', 'status': 'unlocked'}
        """
        self.__logger.debug('Eva.lock_status called')
        return self.__http_client.lock_status()


    def lock(self, wait=True, timeout=None):
        """Owns the lock/control of the robot

        Note:
            This is best called using the "with eva.lock():" method

        Args:
            wait: True/False to wait for lock availability
            timeout: time in seconds to wait for lock availability

        Returns:
            None

        Raises:
            EvaError: If it is not successful

        Example:
            >>> with eva.lock():
            >>>     eva.control_reset_errors()
        """
        self.__logger.debug('Eva.lock called')
        if wait:
            self.__http_client.lock_wait_for(timeout=timeout)
        else:
            self.__http_client.lock_lock()
        return self


    def lock_renew(self):
        """Renews the lock session

        Note:
            This is used within EvaWithLocker and does not need to be called separately

        Returns:
            None

        Raises:
            EvaError: If it is not successful
        """
        self.__logger.debug('Eva.lock_renew called')
        return self.__http_client.lock_renew()


    def unlock(self):
        """Closes the lock session cleanly

        Note:
            This is used within EvaWithLocker and does not need to be called separately

        Returns:
            None

        Raises:
            EvaError: If it is not successful
        """
        self.__logger.debug('Eva.unlock called')
        return self.__http_client.lock_unlock()


    # Control
    def control_wait_for_ready(self):
        """Waits for the robot to enter the "ready" state

        Note:
            This is handled through the control_wait_for_ready() function

        Returns:
            None
        """
        self.__logger.debug('Eva.control_wait_for_ready called')
        return self.__http_client.control_wait_for_ready()


    def control_wait_for(self, goal):
        """Waits for the robot to enter a state specified in RobotState

        Note:
            Check RobotState enum for list of states

        Args:
            goal: State to wait for before returning

        Raises:
            EvaError: If the robot enters the ERROR or COLLISION state

        Returns:
            None, once robot has reached specified state
        """
        self.__logger.debug('Eva.control_wait_for called')
        return self.__http_client.control_wait_for(goal)


    def control_home(self, wait_for_ready=True):
        """Sends robot to home/start position of the active toolpath

        Args:
            wait_for_ready: boolean value to wait for the robot state to enter READY before proceeding

        Returns:
            None

        Raises:
            EvaError: If it is not successful
        """
        self.__logger.debug('Eva.control_home called')
        with self.__eva_locker.set_renew_period(Eva.__TEACH_RENEW_PERIOD):
            return self.__http_client.control_home(wait_for_ready=wait_for_ready)


    def control_run(self, loop=1, wait_for_ready=True, mode='teach'):
        """Runs active toolpath for specified amount of loops

        Note:
            Teach mode is active by default, automatic mode must be specified for normal operation

        Args:
            loop: integer, number of loops to run toolpath for. 0 loops for continuous operation.
            wait_for_ready: boolean value to wait for the robot state to enter READY before proceeding
            mode: 'teach' or 'automatic', set to automatic for normal operation

        Returns:
            None

        Raises:
            EvaError: If it is not successful

        Example:
            >>> with eva.lock():
            >>>     eva.control_run(5, wait_for_ready=False, mode='automatic')
        """
        self.__logger.debug('Eva.control_run called')
        if mode == 'teach':
            with self.__eva_locker.set_renew_period(Eva.__TEACH_RENEW_PERIOD):
                return self.__http_client.control_run(loop=loop, wait_for_ready=wait_for_ready, mode=mode)
        else:
            return self.__http_client.control_run(loop=loop, wait_for_ready=wait_for_ready, mode=mode)


    def control_go_to(self, joints, wait_for_ready=True, max_speed=None, time_sec=None, mode='teach'):
        """Move robot to specified joint angles

        Args:
            joints: list of angles in RADIANS
            wait_for_ready: boolean value to wait for the robot state to enter READY before proceeding
            max_speed: speed in mm/s to travel to joint angles specified
            time_sec: time in seconds of duration to travel to joint angles specified
            mode: 'teach' by default, 'automatic' must be set for max_speed and time_sec to work effectively

        Returns:
            None

        Raises:
            EvaError: If it is not successful

        Example:
            >>> with eva.lock():
            >>>     control_go_to([0, 0, 0, 0, 0, 0], wait_for_ready=False, max_speed=250, mode='automatic')
        """
        self.__logger.info('Eva.control_go_to called')
        if mode == 'teach':
            with self.__eva_locker.set_renew_period(Eva.__TEACH_RENEW_PERIOD):
                return self.__http_client.control_go_to(joints, wait_for_ready=wait_for_ready, max_speed=max_speed,
                                                        time_sec=time_sec, mode=mode)
        else:
            return self.__http_client.control_go_to(joints, wait_for_ready=wait_for_ready, max_speed=max_speed,
                                                    time_sec=time_sec, mode=mode)


    def control_pause(self, wait_for_paused=True):
        """Pauses robot while in operation

        Note:
            Robot MUST be in running state when this is called

        Args:
            wait_for_paused: boolean value to wait for the robot to enter PAUSED state before proceeding

        Returns:
            None

        Raises:
            EvaError: If it is not successful

        Example:
            >>> with eva.lock():
            >>>     eva.control_pause()
        """
        self.__logger.debug('Eva.control_pause called')
        return self.__http_client.control_pause(wait_for_paused=wait_for_paused)


    def control_resume(self, wait_for_running=True):
        """Continues robot operation from PAUSED state

        Args:
            wait_for_running: boolean value to wait for the robot state to enter RUNNING before proceeding

        Returns:
            None

        Raises:
            EvaError: If it is not successful

        Example:
            >>> with eva.lock():
            >>>     eva.control_resume()
        """
        self.__logger.debug('Eva.control_resume called')
        return self.__http_client.control_resume(wait_for_running=wait_for_running)


    def control_cancel(self, wait_for_ready=True):
        """Cancels PAUSED state, robot will enter READY state after function call

        Note:
            Robot will need to be sent home before re-starting a toolpath

        Returns:
            None

        Args:
            wait_for_ready: boolean value to wait for the robot state to enter READY before proceeding

        Raises:
            EvaError: If it is not successful

        Example:
            >>> with eva.lock():
            >>>     eva.control_cancel()
        """
        self.__logger.debug('Eva.control_cancel called')
        return self.__http_client.control_cancel(wait_for_ready=wait_for_ready)


    def control_stop_loop(self, wait_for_ready=True):
        """Stops robot once it has reached the end of the current running loop

        Args:
            wait_for_ready: boolean value to wait for the robot state to enter READY before proceeding

        Returns:
            None

        Raises:
            EvaError: If it is not successful

        Example:
            >>> with eva.lock():
            >>>     eva.control_stop_loop()
        """
        self.__logger.debug('Eva.control_stop_loop called')
        return self.__http_client.control_stop_loop(wait_for_ready=wait_for_ready)


    def control_reset_errors(self, wait_for_ready=True):
        """Resets controller error state of the robot

        Note:
            An exception will be raised if no errors are present

        Args:
            wait_for_ready: boolean value to wait for the robot state to enter READY before proceeding

        Returns:
            None

        Raises:
            EvaError: If it is not successful

        Example:
            >>> with eva.lock():
            >>>     eva.control_reset_errors()
        """
        self.__logger.debug('Eva.control_reset_errors called')
        return self.__http_client.control_reset_errors(wait_for_ready=wait_for_ready)

    # Collision Detection
    def control_configure_collision_detection(self, enabled, sensitivity):
        """Sets the sensitivity of the collision detection function

        Args:
            enabled: True or False
            sensitivity: 'low', 'medium' or 'high' options of sensitivity

        Returns:
            None

        Raises:
            EvaError: If it is not successful
            ValueError: If sensitivity or enabled arguments are not valid

        Example:
            >>> with eva.lock():
            >>>     control_configure_collision_detection(True, 'medium')
        """
        self.__logger.debug('Eva.collision_detection called')
        return self.__http_client.control_configure_collision_detection(enabled=enabled, sensitivity=sensitivity)

    def control_acknowledge_collision(self, wait_for_ready=True):
        """Acknowledges collision incident ands sets the robot to READY state

        Args:
            wait_for_ready: boolean value to wait for the robot state to enter READY before proceeding

        Returns:
            None

        Raises:
            EvaError: If it is not successful

        Example:
            >>> with eva.lock():
            >>>     eva.control_acknowledge_collision()
        """
        self.__logger.debug('Eva.acknowledge_collision called')
        return self.__http_client.control_acknowledge_collision(wait_for_ready=wait_for_ready)

    # Calc
    def calc_forward_kinematics(self, joints, fk_type='both', tcp_config=None):
        """Gives the position of the robot and orientation of end-effector in 3D space

        Args:
            joints: a list of joint angles in RADIANS
            fk_type: 'position', 'orientation', 'both' are available FK types
            tcp_config: dict containing TCP configuration

        Returns:
            dict: containing 'result', 'success', and 'orientation'

        Raises:
            EvaError: If it is not successful

        Example:
            >>> eva.calc_forward_kinematics([0,0,0,0,0,0])
            {'result': 'success', 'position': {'x': -0.065000005, 'y': -8.960835e-09, 'z': 0.87839997},
            'orientation': {'w': 1, 'x': 0, 'y': 0, 'z': 0}}
        """
        self.__logger.debug('Eva.calc_forward_kinematics called')
        return self.__http_client.calc_forward_kinematics(joints, fk_type=fk_type, tcp_config=tcp_config)


    def calc_inverse_kinematics(self, guess, target_position, target_orientation, tcp_config=None,
                                orientation_type=None):
        """Gives a list of joint angles calculated from XYZ and end-effector orientation coordinates

        Args:
            guess: a list of joing angles in RADIANS near the area of operation, does not need to be precise
            target_position: dict containing XYZ coordinates
            target_orientation: dict containing WYZ (yaw, pitch, roll) of the end effector orientation
            tcp_config: dict containing TCP configuration
            orientation_type: 'matrix', 'axis_angle', 'euler_zyx', or 'quat' orientation types

        Returns:
            dict: containing 'ik' dict with joint angles (if successful) and 'result' of function call

        Raises:
            EvaError: If it is not successful

        Example:
            >>> eva_position = {'x': -0.065000005, 'y': -8.960835e-09, 'z': 0.87839997}
            >>> eva_orientation = {'w': 1, 'x': 0, 'y': 0, 'z': 0}
            >>> eva_guess = [0, 0, 0, 0, 0, 0]
            >>> robot.calc_inverse_kinematics(eva_guess, eva_position, eva_orientation)
            {'ik': {'joints': [0, 0, 0, 0, 0, 0], 'result': 'success'}}
        """
        self.__logger.debug('Eva.calc_inverse_kinematics called')
        return self.__http_client.calc_inverse_kinematics(guess, target_position, target_orientation,
                                                          tcp_config=tcp_config, orientation_type=orientation_type)


    def calc_nudge(self, joints, direction, offset, tcp_config=None):
        """Calculates joint angles required to move robot a certain distance in XYZ space

        Raises:
            EvaError: If it is not successful

        Args:
            joints: a list of joint angles in RADIANS
            direction: 'x', 'y' or 'z' axis to move on
            offset: distance in METERS to move
            tcp_config: dict containing TCP configuration

        Returns:
            list: calculated joint angles to fulfill direction + offset

        Example:
            >>> robot.calc_nudge(eva_guess, direction='y', offset=0.1
            [-0.114060126, 0.2246457, -0.37865394, -9.745418e-07, 0.15400818, 0.11406111]
        """
        self.__logger.debug('Eva.calc_nudge called')
        return self.__http_client.calc_nudge(joints, direction, offset, tcp_config=tcp_config)


    def calc_pose_valid(self, joints, tcp_config=None):
        """Checks whether requested joint angles are able to be reached successfully

        Args:
            joints: a list of joint angles in RADIANS
            tcp_config: dict containing TCP configuration

        Returns:
            bool: True or False condition

        Raises:
            EvaError: If it is not successful

        Example:
            >>> eva.calc_pose_valid([0,0,0,1.7,0.5,-1])
            True
        """
        self.__logger.debug('Eva.calc_pose_valid called')
        return self.__http_client.calc_pose_valid(joints, tcp_config=tcp_config)


    def calc_rotate(self, joints, axis, offset, tcp_config=None):
        """Calculates joint angles required to rotate end-effector in a given direction

        Args:
            joints: a list of joint angles in RADIANS
            axis: 'x', 'y' or 'z' axis to rotate on
            offset: distance in METERS to move
            tcp_config: dict containing TCP configuration

        Returns:
            dict: containing rotate dict with joint angles and result dict of success/failure

        Raises:
            EvaError: If it is not successful

        Example:
            >>> robot.calc_rotate(eva_guess, axis='y', offset=0.1)
            {'rotate': {'joints': [-1.5598009e-06, -0.06286066, 0.14495611, 2.2529257e-06, -0.18224284, -7.145747e-07],
             'result': 'success'}}
        """
        self.__logger.debug('Eva.calc_rotate called')
        return self.__http_client.calc_rotate(joints, axis, offset, tcp_config=tcp_config)
