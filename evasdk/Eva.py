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
        self.__logger.debug('Eva.api_call_with_auth {} {}'.format(method, path))
        return self.__http_client.api_call_with_auth(method, path, payload=payload, headers=headers, timeout=timeout,
                                                     version=version)

    def api_call_no_auth(self, method, path, payload=None, headers={}, timeout=None, version='v1'):
        self.__logger.debug('Eva.api_call_no_auth {} {}'.format(method, path))
        return self.__http_client.api_call_no_auth(method, path, payload=payload, headers=headers, timeout=timeout,
                                                   version=version)


    # Global
    def versions(self):
        """Gets the version of the API server and the Choreograph version installed on the robot.

        Returns:
            dict: API server version, robot choreograph version

        Example:
            >>> print(eva.versions())
            {'APIs': ['v1'], 'robot': '4.10.0'}
        """
        self.__logger.debug('Eva.versions called')
        return self.__http_client.api_versions()

    def name(self):
        """Gets the name of the robot.

        Returns:
            dict: robot name

        Example:
            >>> print(eva.name())
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
            EvaError: If status code on API request is not 204
        """
        self.__logger.debug('Eva.auth_renew_session called')
        return self.__http_client.auth_renew_session()


    def auth_create_session(self):
        """Creates a session token token.

        Note:
            Should not need to be called as it is handled

        Returns:
            str: session_token

        Raises:
            EvaError: If status code on API request is not 200

        Example:
            >>> print(eva.auth_create_session())
            c8c3a36b-4fce-4df2-b795-6bf5629ff48d
        """
        self.__logger.debug('Eva.auth_create_session called')
        return self.__http_client.auth_create_session()


    def auth_invalidate_session(self):
        """Deletes/invalidates the API session token.

        Raises:
            EvaError: If status code on API request is not 204

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
            EvaError: If status code on API request is not 200
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
            >>> print(eva.data_snapshot_property('control'))
            {'loop_count': 0, 'loop_target': 0, 'run_mode': 'not_running', 'state': 'error'}
        """
        self.__logger.debug('Eva.data_snapshot_property called')
        return self.__http_client.data_snapshot_property(prop)


    def data_servo_positions(self):
        """Returns the servo positions of each joint.

        Note:
            This function uses the data_snapshot_property() to return the servo positions
            from the data_snapshot() function.

        Returns:
            list: 6 position list containing joint angles in RADIANS

        Raises:
            EvaError: If the property is not found within the data_snapshot() dict

        Example:
            >>> print(eva.data_servo_positions())
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
            EvaError: If status code on API request is not 200

        Example:
            >>> print(eva.users_get())
            {'users': [{'id': 1, 'email': 'test@automata.tech', 'role': 'admin'},
             {'id': 2, 'email': 'euan@automata.tech', 'role': 'user'}]}
        """
        self.__logger.debug('Eva.users_get called')
        return self.__http_client.users_get()


    # Config
    def config_update(self, update):
        """Applies choreograph update to robot.

        Args:
            update: AUT / update file

        Raises:
            EvaError: If status code on API request is not 200
        """
        self.__logger.debug('Eva.config_update called')
        return self.__http_client.config_update(update)


    # GPIO
    def gpio_set(self, pin, status):
        self.__logger.debug('Eva.gpio_set called')
        return self.__http_client.gpio_set(pin, status)


    def gpio_get(self, pin, pin_type):
        self.__logger.debug('Eva.gpio_get called')
        return self.__http_client.gpio_get(pin, pin_type)

    def globals_edit(self, keys, values):
        self.__logger.debug('Eva.globals_edit called')
        return self.__http_client.globals_edit(keys, values)

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
        with self.__eva_locker.set_renew_period(Eva.__TEACH_RENEW_PERIOD):
            return self.__http_client.control_home(wait_for_ready=wait_for_ready)


    def control_run(self, loop=1, wait_for_ready=True, mode='teach'):
        self.__logger.debug('Eva.control_run called')
        if mode == 'teach':
            with self.__eva_locker.set_renew_period(Eva.__TEACH_RENEW_PERIOD):
                return self.__http_client.control_run(loop=loop, wait_for_ready=wait_for_ready, mode=mode)
        else:
            return self.__http_client.control_run(loop=loop, wait_for_ready=wait_for_ready, mode=mode)


    def control_go_to(self, joints, wait_for_ready=True, max_speed=None, time_sec=None, mode='teach'):
        self.__logger.info('Eva.control_go_to called')
        if mode == 'teach':
            with self.__eva_locker.set_renew_period(Eva.__TEACH_RENEW_PERIOD):
                return self.__http_client.control_go_to(joints, wait_for_ready=wait_for_ready, max_speed=max_speed,
                                                        time_sec=time_sec, mode=mode)
        else:
            return self.__http_client.control_go_to(joints, wait_for_ready=wait_for_ready, max_speed=max_speed,
                                                    time_sec=time_sec, mode=mode)


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

    # Collision Detection
    def control_configure_collision_detection(self, enabled, sensitivity):
        self.__logger.debug('Eva.collision_detection called')
        return self.__http_client.control_configure_collision_detection(enabled=enabled, sensitivity=sensitivity)

    def control_acknowledge_collision(self, wait_for_ready=True):
        self.__logger.debug('Eva.acknowledge_collision called')
        return self.__http_client.control_acknowledge_collision(wait_for_ready=wait_for_ready)

    # Calc
    def calc_forward_kinematics(self, joints, fk_type='both', tcp_config=None):
        self.__logger.debug('Eva.calc_forward_kinematics called')
        return self.__http_client.calc_forward_kinematics(joints, fk_type=fk_type, tcp_config=tcp_config)


    def calc_inverse_kinematics(self, guess, target_position, target_orientation, tcp_config=None,
                                orientation_type=None):
        self.__logger.debug('Eva.calc_inverse_kinematics called')
        return self.__http_client.calc_inverse_kinematics(guess, target_position, target_orientation,
                                                          tcp_config=tcp_config, orientation_type=orientation_type)


    def calc_nudge(self, joints, direction, offset, tcp_config=None):
        self.__logger.debug('Eva.calc_nudge called')
        return self.__http_client.calc_nudge(joints, direction, offset, tcp_config=tcp_config)


    def calc_pose_valid(self, joints, tcp_config=None):
        self.__logger.debug('Eva.calc_pose_valid called')
        return self.__http_client.calc_pose_valid(joints, tcp_config=tcp_config)


    def calc_rotate(self, joints, axis, offset, tcp_config=None):
        self.__logger.debug('Eva.calc_rotate called')
        return self.__http_client.calc_rotate(joints, axis, offset, tcp_config=tcp_config)
