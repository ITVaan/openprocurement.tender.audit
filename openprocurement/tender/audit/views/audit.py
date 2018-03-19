from openprocurement.api.utils import (
    APIResource, json_view, context_unpack
)

from openprocurement.tender.audit.utils import auditresource, save_audit
from openprocurement.tender.audit.validation import validate_audit_data


@auditresource(name='Audits', path='/audits', description='Audits')
class AuditsResource(APIResource):
    def __init__(self, request, context):
        super(AuditsResource, self).__init__(request, context)

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
                'data': audit.serialize("view"),
                'access': {
                    'token': audit.owner_token
                }
            }


@auditresource(name='Audit', path='/audits/{audit_id}', description='Audit')
class AuditResource(AuditsResource):
    @json_view(permission='view_audit')
    def get(self):
        return {'data': self.request.validated['audit'].serialize('view')}



