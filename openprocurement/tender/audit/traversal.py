from openprocurement.api.traversal import get_item

from pyramid.security import (
    ALL_PERMISSIONS,
    Allow,
    Everyone,
)


class Root(object):
    __name__ = None
    __parent__ = None
    __acl__ = [
        (Allow, Everyone, 'view_listing'),
        (Allow, Everyone, 'view_audit'),
        (Allow, 'broker', 'create_audit'),
        (Allow, 'broker', 'edit_active'),
        (Allow, 'broker', 'edit_audit'),
        (Allow, 'broker', 'upload_audit_documents'),
        (Allow, 'g:Administrator', 'edit_audit'),
        (Allow, 'g:admins', ALL_PERMISSIONS),
    ]

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db


def factory(request):
    request.validated['audit_src'] = dict()
    root = Root(request)

    if not request.matchdict or not request.matchdict.get('audit_id'):
        return root
    request.validated['audit_id'] = request.matchdict['audit_id']
    audit = request.audit
    audit.__parent__ = root
    request.validated['audit'] = request.validated['db_doc'] = audit

    if request.method != 'GET':
        request.validated['audit_src'] = audit.serialize('plain')
    if request.matchdict.get('answer_id'):
        answer = get_item(audit, 'answer', request)
        if request.matchdict.get('document_id'):
            return get_item(answer, 'document', request)
        else:
            return answer
    elif request.matchdict.get('offense_id'):
        return get_item(audit, 'offense', request)
    elif request.matchdict.get('document_id'):
        return get_item(audit, 'document', request)
    elif request.matchdict.get('change_id'):
        return get_item(audit, 'change', request)
    request.validated['id'] = request.matchdict['audit_id']

    return audit

