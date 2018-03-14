# -*- coding: utf-8 -*-
from ConfigParser import ConfigParser
from hashlib import sha512
from json import dumps
from logging import getLogger

from pyramid.httpexceptions import exception_response
from pyramid.security import Allow, Everyone
from webob.multidict import NestedMultiDict

from reports.brokers.utils import VERSION, default_error_status

USERS = {}
LOGGER = getLogger(__name__)


class Root(object):
    __name__ = None
    __parent__ = None
    __acl__ = [
        (Allow, Everyone, 'view'),
    ]

    def __init__(self, request):
        self.request = request


def read_users(filename):
    config = ConfigParser()
    config.read(filename)
    for i in config.sections():
        USERS.update(dict([
            (
                j,
                {
                    'password': k,
                    'group': i
                }
            )
            for j, k in config.items(i)
        ]))


def update_logging_context(request, params):
    if not request.__dict__.get('logging_context'):
        request.logging_context = {}

    for x, j in params.items():
        request.logging_context[x.upper()] = j


def context_unpack(request, msg, params=None):
    if params:
        update_logging_context(request, params)
    logging_context = request.logging_context
    journal_context = msg
    for key, value in logging_context.items():
        journal_context["JOURNAL_" + key] = value
    return journal_context


def error_handler(request, status, error):
    params = {
        'ERROR_STATUS': status
    }
    for key, value in error.items():
        params['ERROR_{}'.format(key)] = str(value)
    LOGGER.info('Error on processing request "{}"'.format(dumps(error)),
                extra=context_unpack(request, {'MESSAGE_ID': 'error_handler'}, params))
    request.response.status = status
    request.response.content_type = 'application/json'
    return {
        "status": "error",
        "errors": [error]
    }


def add_logging_context(event):
    request = event.request
    params = {
        'API_VERSION': VERSION,
        'TAGS': 'python,api',
        'USER': str(request.authenticated_userid or ''),
        'ROLE': str(request.authenticated_role or ''),
        'CURRENT_URL': request.url,
        'CURRENT_PATH': request.path_info,
        'REMOTE_ADDR': request.remote_addr or '',
        'USER_AGENT': request.user_agent or '',
        'REQUEST_METHOD': request.method,
        'REQUEST_ID': request.environ.get('REQUEST_ID', ''),
        'CLIENT_REQUEST_ID': request.headers.get('X-Client-Request-ID', ''),
    }

    request.logging_context = params


def request_params(request):
    try:
        params = NestedMultiDict(request.GET, request.POST)
    except UnicodeDecodeError:
        response = exception_response(422)
        response.body = dumps(error_handler(request, response.code,
                                            {"location": "body",
                                             "name": "data",
                                             "description": "could not decode params"}))
        response.content_type = 'application/json'
        raise response
    except Exception as e:
        response = exception_response(422)
        response.body = dumps(error_handler(request, response.code,
                                            {"location": "body",
                                             "name": str(e.__class__.__name__),
                                             "description": str(e)}))
        response.content_type = 'application/json'
        raise response
    return params


def set_logging_context(event):
    request = event.request
    params = dict()
    params['ROLE'] = str(request.authenticated_role)
    if request.params:
        params['PARAMS'] = str(dict(request.params))
    update_logging_context(request, params)


def set_renderer(event):
    request = event.request
    try:
        json = request.json_body
    except ValueError:
        json = {}
    pretty = isinstance(json, dict) and json.get('options', {}).get('pretty') or request.params.get('opt_pretty')
    accept = request.headers.get('Accept')
    jsonp = request.params.get('opt_jsonp')
    if jsonp and pretty:
        request.override_renderer = 'prettyjsonp'
        return True
    if jsonp:
        request.override_renderer = 'jsonp'
        return True
    if pretty:
        request.override_renderer = 'prettyjson'
        return True
    if accept == 'application/yaml':
        request.override_renderer = 'yaml'
        return True


def auth_check(username, password):
    if username in USERS and USERS[username]['password'] == sha512(password).hexdigest():
        return ['g:{}'.format(USERS[username]['group'])]


def forbidden(request):
    request.response.json_body = error_handler(request, 403,
                                               {"location": "url", "name": "permission", "description": "Forbidden"})
    return request.response


def read_json(name):
    import os.path
    from json import loads
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(curr_dir, name)
    with open(file_path) as lang_file:
        data = lang_file.read()
    return loads(data)


def handle_error(request, response):
    if response.headers['Content-Type'] != 'application/json':
        return error_handler(request, default_error_status,
                             {"location": "request", "name": "ip", "description": [{u'message': u'Forbidden'}]})
    if response.status_code == 429:
        seconds_to_wait = response.headers.get('Retry-After')
        request.response.headers['Retry-After'] = seconds_to_wait
        return error_handler(request, 429, {"location": "body", "name": "data",
                                            "description": [{u'message': u'Retry request after {} seconds.'.format(
                                                seconds_to_wait)}]})
    elif response.status_code == 502:
        return error_handler(request, default_error_status, {"location": "body", "name": "data",
                                                             "description": [
                                                                 {u'message': u'Service is disabled or upgrade.'}]})
    return error_handler(request, default_error_status, {"location": "body", "name": "data",
                                                         "description": response.json()['errors']})
