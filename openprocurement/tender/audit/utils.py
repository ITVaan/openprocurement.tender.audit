import logging

from functools import partial
from cornice.resource import resource

from schematics.exceptions import ModelValidationError

from openprocurement.api.models import Revision
from openprocurement.api.utils import (
    error_handler,
    get_now,
    context_unpack,
    set_modetest_titles,
    get_revision_changes
)
from openprocurement.tender.audit.traversal import factory
from openprocurement.tender.audit.models import Audit


auditresource = partial(resource, error_handler=error_handler, factory=factory)

logger = logging.getLogger(__name__)


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
    except ModelValidationError, e:
        for i in e.message:
            request.errors.add('body', i, e.message[i])
        request.errors.status = 422
    except Exception, e:
        request.errors.add('body', 'data', str(e))
    else:
        logger.info('Saved audit {}: dateModified -> {}'.format(
            audit.id,
            audit.date_modified.isoformat()),
            extra=context_unpack(request, {'MESSAGE_ID': 'save_audit'}, {'AUDIT_REV': audit.rev}))
        return True


def extract_audit(request):
    db = request.registry.db
    audit_id = request.matchdict['audit_id']
    doc = db.get(audit_id)
    if doc is not None and doc.get('doc_type') == 'audit':
        request.errors.add('url', 'audit_id', 'Archived')
        request.errors.status = 410
        raise error_handler(request.errors)
    elif doc is None or doc.get('doc_type') != 'Audit':
        request.errors.add('url', 'audit_id', 'Not Found')
        request.errors.status = 404
        raise error_handler(request.errors)
    return request.audit_from_data(doc)





