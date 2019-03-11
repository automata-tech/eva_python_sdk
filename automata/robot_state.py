import enum

# TODO add static method for init that gives a nice exception on ValueException
class RobotState(enum.Enum):
    READY = 'ready'
    PAUSED = 'paused'
    ERROR = 'error'
    RUNNING = 'running'
    STOPPING = 'stopping'
    JOGGING = 'jogging'
    BACKDRIVING = 'backdriving'
