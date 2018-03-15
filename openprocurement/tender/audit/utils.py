# -*- coding: utf-8 -*-
from ConfigParser import ConfigParser
from hashlib import sha512
from json import dumps
from logging import getLogger

from pyramid.httpexceptions import exception_response
from pyramid.security import Allow, Everyone
from webob.multidict import NestedMultiDict
from pkg_resources import get_distribution

PKG = get_distribution(__package__)
LOGGER = getLogger(PKG.project_name)
VERSION = '{}.{}'.format(int(PKG.parsed_version._version.release[0]), int(PKG.parsed_version._version.release[1]))
USERS = {}
ROUTE_PREFIX = '/api/{}'.format(VERSION)
default_error_status = 403


class Root(object):
    __name__ = None
    __parent__ = None
    __acl__ = [
        (Allow, Everyone, 'view'),
    ]

    def __init__(self, request):
        self.request = request


def read_users(filename):
    LOGGER.info("Read users {}".format(filename))
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
    LOGGER.info("Update logging context params {}".format(params))
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
    LOGGER.info("Error handler request: {} status: {} error: {}".format(request, status, error))
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
    LOGGER.info("Request params {}".format(request))
    LOGGER.info("Request params get {}".format(request.GET))
    LOGGER.info("Request params post {}".format(request.POST))
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
    LOGGER.info("Params {}".format(params))
    return params


def set_logging_context(event):
    LOGGER.info("Set logging context {}".format(event))
    request = event.request
    params = dict()
    params['ROLE'] = str(request.authenticated_role)
    if request.params:
        params['PARAMS'] = str(dict(request.params))
    update_logging_context(request, params)


def set_renderer(event):
    LOGGER.info("Set renderer {}".format(event))
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
    LOGGER.info("auth check")
    if username in USERS and USERS[username]['password'] == sha512(password).hexdigest():
        return ['g:{}'.format(USERS[username]['group'])]


def forbidden(request):
    request.response.json_body = error_handler(request, 403,
                                               {"location": "url", "name": "permission", "description": "Forbidden"})
    return request.response


def read_json(name):
    LOGGER.info("Reading json")
    import os.path
    from json import loads
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(curr_dir, name)
    with open(file_path) as lang_file:
        data = lang_file.read()
    return loads(data)


def handle_error(request, response):
    LOGGER.info("handling error?")
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


def save_audit(audit, db):
    LOGGER.info("save {} in {}".format(audit, db))
    audit.store(db)

#
# def save_contract(request):
#     """ Save contract object to database
#     :param request:
#     :return: True if Ok
#     """
#     contract = request.validated['contract']
#
#     if contract.mode == u'test':
#         set_modetest_titles(contract)
#     patch = get_revision_changes(contract.serialize("plain"),
#                                  request.validated['contract_src'])
#     if patch:
#         contract.revisions.append(
#             Revision({'author': request.authenticated_userid,
#                       'changes': patch, 'rev': contract.rev}))
#         old_date_modified = contract.dateModified
#         contract.dateModified = get_now()
#         try:
#             contract.store(request.registry.db)
#         except ModelValidationError, e:  # pragma: no cover
#             for i in e.message:
#                 request.errors.add('body', i, e.message[i])
#             request.errors.status = 422
#         except Exception, e:  # pragma: no cover
#             request.errors.add('body', 'data', str(e))
#         else:
#             LOGGER.info('Saved contract {}: dateModified {} -> {}'.format(
#                 contract.id, old_date_modified and old_date_modified.isoformat(),
#                 contract.dateModified.isoformat()),
#                 extra=context_unpack(request, {'MESSAGE_ID': 'save_contract'},
#                                      {'CONTRACT_REV': contract.rev}))
#             return True
