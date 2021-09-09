import websocket  # type: ignore
import logging
import json
from threading import Thread, Condition
from .eva_errors import EvaWebsocketError
from .observer import Subject


logger = logging.getLogger(__name__)


class Websocket:
    """
    This class creates a context which runs a thread to monitor a websocket in the background.
    It follows the Observer pattern, which you can use to listen to specific event or `all` to get all of them.
    Note: notifications will be sent from a different thread so you will need to use a mutex or other synchronization mechanims.
    """

    def __init__(self, url, protocols, timeout=5):
        self.__thread = Thread(target=self.__run)
        self.__url = url
        self.__protocols = protocols
        self.__app = None
        self.__ws = None
        self.__cond = Condition()
        self.__timeout = timeout
        self.__subject = Subject()

    def __enter__(self):
        self.__thread.start()
        with self.__cond:
            connected = self.__cond.wait(timeout=self.__timeout)
            if not connected:
                raise EvaWebsocketError('could not connect to Eva\'s data stream')
        return self

    def __on_open(self, ws):
        logger.debug('ws_on_open')
        with self.__cond:
            self.__ws = ws
            self.__cond.notify_all()

    def __on_message(self, ws, raw):
        msg = json.loads(raw)
        if 'type' not in msg or msg['type'] != 'state_change':
            logger.debug('ws_on_message', msg)
        self.__subject.notify('all', msg)
        if 'type' in msg:
            self.__subject.notify(msg['type'], msg)
        else:
            logger.debug('missing message type', msg)

    def __on_error(self, ws, error):
        logger.debug('ws_on_error', error)
        with self.__cond:
            self.__ws = None

    def __on_close(self, ws, close_status_code, close_msg):
        logger.debug('ws_on_close', close_status_code, close_msg)
        with self.__cond:
            self.__ws = None

    def __exit__(self, type, value, traceback):
        if self.__app is not None:
            self.__app.keep_running = False
        self.__thread.join()

    def __run(self):
        self.__app = websocket.WebSocketApp(
            self.__url,
            subprotocols=self.__protocols,
            on_open=self.__on_open,
            on_message=self.__on_message,
            on_error=self.__on_error,
            on_close=self.__on_close,
        )
        self.__app.run_forever()

    def _send_raw(self, data):
        with self.__cond:
            if self.__ws is None:
                raise EvaWebsocketError('Eva\'s data stream has disconnected')
            self.__ws.send(json.dumps(data))

    def register(self, event, callback):
        self.__subject.register(event, callback)

    def deregister(self, event, callback):
        self.__subject.deregister(event, callback)
