import enum


# TODO add static method for init that gives a nice exception on ValueException
class RobotState(enum.Enum):
    READY = 'ready'
    PAUSED = 'paused'
    ERROR = 'error'
    RUNNING = 'running'
    STOPPING = 'stopping'
    BACKDRIVING = 'backdriving'
    UPDATING = 'updating'
    DISABLED = 'disabled'
    SHUTTING_DOWN = 'shutting_down'
    COLLISION = 'collision'
