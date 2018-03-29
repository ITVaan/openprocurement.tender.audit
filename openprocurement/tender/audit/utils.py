import logging

from functools import partial
from json import dumps

from cornice.resource import resource

from schematics.exceptions import ModelValidationError
from ConfigParser import ConfigParser
from hashlib import sha512

from openprocurement.api.models import Revision
from openprocurement.api.utils import (
    error_handler,
    get_now,
    context_unpack,
    set_modetest_titles,
    get_revision_changes,
    apply_data_patch
)
from openprocurement.tender.audit.traversal import factory
from openprocurement.tender.audit.models import Audit

#
#
#
# def error_handler(request, status, error):
#     params = {
#         'ERROR_STATUS': status
#     }
#     for key, value in error.items():
#         params['ERROR_{}'.format(key)] = str(value)
#     logger.info('Error on processing request "{}"'.format(dumps(error)),
#                 extra=context_unpack(request, {'MESSAGE_ID': 'error_handler'}, params))
#     request.response.status = status
#     request.response.content_type = 'application/json'
#     return {
#         "status": "error",
#         "errors": [error]
#     }

auditresource = partial(resource, error_handler=error_handler, factory=factory)

logger = logging.getLogger(__name__)

USERS = {}


def read_users(filename):
    logger.info(u"Read users {}".format(filename))
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
    except ModelValidationError as e:
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


def auth_check(username, password, request):
    res = []
    if username in USERS:
        res.append('g:{}'.format(USERS[username]['group']))
        logger.info("res = {}".format(res))
    return res


def extract_audit(request):
    db = request.registry.db
    audit_id = request.matchdict['audit_id']
    doc = db.get(audit_id)
    if doc is None or doc.get('doc_type') != 'Audit':
        request.errors.add('url', 'audit_id', 'Not Found')
        request.errors.status = 404
        raise error_handler(request.errors)
    return request.audit_from_data(doc)


def check_tender_exists(request, tender_id):
    db = request.registry.db
    doc = db.get(tender_id)

    if doc is None or doc.get('doc_type') != 'Tender':
        request.errors.add('url', 'tender_id', 'Not Found')
        request.errors.status = 404
        raise error_handler(request.errors)

    return True


def apply_patch(request, data=None, save=True, src=None):
    data = request.validated['data'] if data is None else data
    patch = data and apply_data_patch(src or request.context.serialize(), data)
    if patch:
        request.context.import_data(patch)
        if save:
            return save_audit(request)
