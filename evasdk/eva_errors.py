class EvaError(Exception):
    """Base class for all Eva errors"""


class EvaValidationError(EvaError, ValueError):
    """Error thrown when the request arguements are invalid"""


class EvaAuthError(EvaError, Exception):
    """Error thrown when request requires authentication"""


class EvaAdminError(EvaError, Exception):
    """Error thrown when request requires admin user rights"""


class EvaServerError(EvaError, Exception):
    """Error thrown when Eva returns an internal server error"""


class EvaDisconnectionError(EvaError, Exception):
    """Error thrown when Eva websocket connection is closed"""


class EvaLockError(EvaError, Exception):
    """Error thrown when Eva has robot lock issues"""


class EvaAutoRenewError(EvaError, Exception):
    """Error thrown when automatic session renewal fails but not the original request"""


class EvaWebsocketError(EvaError, Exception):
    """Error thrown when an issue related to the websocket stream happens"""


def eva_error(label, r=None):
    if r is not None:
        __handle_http_error(label, r)
    else:
        raise EvaError(label)


def __handle_http_error(label, r):
    error_string = '{}: status code {}'.format(label, r.status_code)
    try:
        r_json = r.json()
        if 'error' in r_json:
            error_string += ' with error [{}]'.format(r_json)
    except ValueError:
        pass

    if r.status_code == 401:
        raise EvaValidationError(error_string)
    elif r.status_code == 401:
        raise EvaAuthError(error_string)
    elif r.status_code == 403:
        raise EvaAdminError(error_string)
    elif 400 <= r.status_code < 500:
        raise EvaError(error_string)
    elif 500 <= r.status_code < 600:
        raise EvaServerError(error_string)
    else:
        raise EvaError(error_string)
