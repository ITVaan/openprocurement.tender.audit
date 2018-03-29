# coding=utf-8
from openprocurement.api.utils import (
    APIResource, json_view, upload_file, context_unpack, get_file, update_file_content_type
)
from openprocurement.api.validation import validate_file_upload, validate_file_update, validate_patch_document_data

from openprocurement.tender.audit.utils import auditresource, save_audit, apply_patch


@auditresource(
    name='Audit Documents', collection_path='/audits/{audit_id}/documents',
    path='/audits/{audit_id}/documents/{document_id}', description='Audit related binary files (PDFs, etc.)'
)
class AuditDocumentResource(APIResource):
    @json_view(permission='view_audit')
    def get(self):
        """Audit Document Read"""
        if self.request.params.get('download'):
            return get_file(self.request)

        document = self.request.validated['document']
        document_data = document.serialize("view")

        document_data['previousVersions'] = [
            i.serialize("view")
            for i in self.request.validated['documents']
            if i.url != document.url
        ]

        return {'data': document_data}

    @json_view(permission='view_audit')
    def collection_get(self):
        """Audit Documents List"""
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in self.context.documents]
        else:
            collection_data = sorted(dict(
                [(i.id, i.serialize('view')) for i in self.context.documents]
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
            document_route = self.request.matched_route.name.replace('collection_', '')
            self.request.response.headers['Location'] = self.request.current_route_url(
                _route_name=document_route, document_id=document.id, _query={}
            )

            return {'data': document.serialize('view')}

    @json_view(permission='upload_audit_documents', validators=(validate_file_update,))
    def put(self):
        """Audit Document Update"""
        document = upload_file(self.request)
        self.request.validated['audit'].documents.append(document)
        if save_audit(self.request):
            self.LOGGER.info(
                'Updated audit document {}'.format(self.request.context.id),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'audit_document_put'})
            )
            return {'data': document.serialize('view')}

    @json_view(
        content_type="application/json", permission='upload_audit_documents', validators=(validate_patch_document_data,)
    )
    def patch(self):
        """Audit Document Update"""
        if apply_patch(self.request, src=self.request.context.serialize()):
            update_file_content_type(self.request)
            self.LOGGER.info(
                'Updated audit document {}'.format(self.request.context.id),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'audit_document_patch'})
            )
            return {'data': self.request.context.serialize('view')}
