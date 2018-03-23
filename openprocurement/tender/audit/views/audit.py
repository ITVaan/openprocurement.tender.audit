from openprocurement.api.utils import (
    APIResource, json_view, context_unpack
)

from openprocurement.tender.audit.utils import auditresource, save_audit, apply_patch
from openprocurement.tender.audit.validation import validate_audit_data, validate_patch_audit_data
from openprocurement.tender.audit.design import audits_all_view
from logging import getLogger


logger = getLogger("{}.init".format(__name__))

@auditresource(name='Audits', path='/audits', description='Audits')
class AuditsResource(APIResource):
    def __init__(self, request, context):
        super(AuditsResource, self).__init__(request, context)

    @json_view(content_type='application/json', permission='view_audit')
    def get(self):
        res = audits_all_view(self.db)
        for x in res:
            logger.info("x= {}".format(x))
        results = [
            (dict([(i, j) for i, j in x.value.items() + [('id', x.id), ('date_modified', x.key)]]), x.key)
            for x in res
        ]

        return {"data": results}

    @json_view(content_type='application/json', permission='create_audit', validators=(validate_audit_data,))
    def post(self):
        audit = self.request.validated.get('audit')
        for i in self.request.validated['json_data'].get('documents', []):
            doc = type(audit).documents.model_class(i)
            doc.__parent__ = audit
            audit.documents.append(doc)
        self.request.validated['audit'] = audit
        self.request.validated['audit_src'] = {}
        if save_audit(self.request):
            self.LOGGER.info(
                'Created audit {}, (TenderID: {})'.format(audit.id, audit.tender_id),
                extra=context_unpack(
                    self.request,
                    {'MESSAGE_ID': 'audit_create'},
                    {'audit_id': audit.id, 'tenderID': audit.tender_id or ''}
                )
            )
            self.request.response.status = 201
            return {
                'data': audit.serialize('plain'),
                'access': {
                    'token': audit.owner_token
                }
            }


@auditresource(name='Audit', path='/audits/{audit_id}', description='Audit')
class AuditResource(AuditsResource):
    @json_view(permission='view_audit')
    def get(self):
        return {'data': self.request.validated['audit'].serialize('view')}

    @json_view(permission='edit_audit', validators=(validate_patch_audit_data,))
    def patch(self):
        """
        Audit Edit (partial)
        """
        audit = self.request.validated['audit']
        apply_patch(self.request, save=False, src=self.request.validated['audit_src'])

        if save_audit(self.request):
            self.LOGGER.info(
                'Updated audit {}'.format(audit.id),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'audit_patch'})
            )
            return {'data': audit.serialize('view')}



