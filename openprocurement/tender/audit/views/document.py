from openprocurement.api.utils import APIResource, json_view, upload_file, context_unpack
from openprocurement.api.validation import validate_file_upload

from openprocurement.tender.audit.utils import auditresource, save_audit


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

    @json_view(permission='upload_audit_documents', validators=(validate_file_upload,))
    def collection_post(self):
        """Audit Document Upload"""
        document = upload_file(self.request)
        self.context.documents.append(document)

        if save_audit(self.request):
            self.LOGGER.info(
                'Created audit document {}'.format(document.id), 
                extra=context_unpack(
                    self.request, {'MESSAGE_ID': 'audit_document_create'}, {'document_id': document.id}
                )
            )

            self.request.response.status = 201
            document_route = self.request.matched_route.name.replace("collection_", "")
            self.request.response.headers['Location'] = self.request.current_route_url(
                _route_name=document_route, document_id=document.id, _query={}
            )

            return {'data': document.serialize("view")}
