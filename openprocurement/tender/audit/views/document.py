from openprocurement.api.utils import APIResource, json_view

from openprocurement.tender.audit.utils import auditresource


@auditresource(
    name='Audit Documents', collection_path='/audits/{audit_id}/documents',
    path='/audits/{audit_id}/documents/{document_id}', description='Audit related binary files (PDFs, etc.)'
)
class AuditDocumentResource(APIResource):
    @json_view(permission='view_audit')
    def collection_get(self):
        """Audit Documents List"""
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in self.context.documents]
        else:
            collection_data = sorted(dict(
                [(i.id, i.serialize("view")) for i in self.context.documents]
            ).values(), key=lambda i: i['dateModified'])

        return {'data': collection_data}
