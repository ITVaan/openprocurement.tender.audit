# -*- coding: utf-8 -*-
from ConfigParser import ConfigParser
from hashlib import sha512
from json import dumps
from logging import getLogger

from pyramid.httpexceptions import exception_response
from pyramid.security import Allow, Everyone
from webob.multidict import NestedMultiDict
from pkg_resources import get_distribution
from functools import partial
from cornice.resource import resource

from schematics.exceptions import ValidationError

from openprocurement.api.models import Revision
from openprocurement.api.utils import (
    get_now,
    set_modetest_titles,
    get_revision_changes
)
from openprocurement.tender.audit.traversal import factory
from openprocurement.tender.audit.models import Audit


PKG = get_distribution(__package__)
logger = getLogger(PKG.project_name)
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
    logger.info("Read users {}".format(filename))
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
    logger.info("Update logging context params {}".format(params))
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
    logger.info("Error handler request: {} status: {} error: {}".format(request, status, error))
    params = {
        'ERROR_STATUS': status
    }
    for key, value in error.items():
        params['ERROR_{}'.format(key)] = str(value)
    logger.info('Error on processing request "{}"'.format(dumps(error)),
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
    logger.info("Request params {}".format(request))
    logger.info("Request params get {}".format(request.GET))
    logger.info("Request params post {}".format(request.POST))
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
    logger.info("Params {}".format(params))
    return params


def set_logging_context(event):
    logger.info("Set logging context {}".format(event))
    request = event.request
    params = dict()
    params['ROLE'] = str(request.authenticated_role)
    if request.params:
        params['PARAMS'] = str(dict(request.params))
    update_logging_context(request, params)


def set_renderer(event):
    logger.info("Set renderer {}".format(event))
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
    logger.info("auth check")
    if username in USERS and USERS[username]['password'] == sha512(password).hexdigest():
        return ['g:{}'.format(USERS[username]['group'])]


def forbidden(request):
    request.response.json_body = error_handler(request, 403,
                                               {"location": "url", "name": "permission", "description": "Forbidden"})
    return request.response


def read_json(name):
    logger.info("Reading json")
    import os.path
    from json import loads
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(curr_dir, name)
    with open(file_path) as lang_file:
        data = lang_file.read()
    return loads(data)


def handle_error(request, response):
    logger.info("handling error?")
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


auditresource = partial(resource, error_handler=error_handler, factory=factory)


def audit_from_data(request, data, raise_error=True, create=True):
    if create:
        return Audit(data)
    return Audit


def save_audit(request):
    """
    Save audit object to database
    :param request:
    :return: True
    """
    audit = request.validated['audit']

    if audit.mode == u'test':
        set_modetest_titles(audit)
    path = get_revision_changes(audit.serialize('plain'), request.validated['audit_src'])

    if path:
        audit.revisions.append(
            Revision({'author': request.authenticated_userid, 'changes': path, 'rev': audit.rev})
        )

    audit.date_modified = get_now()
    try:
        audit.store(request.registry.db)
    except ValidationError as e:
        for i in e.message:
            request.errors.add('body', i, e.message[i])
        request.errors.status = 422
    except Exception as e:
        request.errors.add('body', 'data', str(e))
    else:
        logger.info('Saved audit {}: dateModified -> {}'.format(
            audit.id,
            audit.date_modified.isoformat()),
            extra=context_unpack(request, {'MESSAGE_ID': 'save_audit'}, {'AUDIT_REV': audit.rev}))
        return True
