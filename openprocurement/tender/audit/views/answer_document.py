from openprocurement.api.utils import (
    APIResource, json_view, upload_file, context_unpack, get_file, update_file_content_type
)
from openprocurement.api.validation import validate_file_upload, validate_file_update, validate_patch_document_data

from openprocurement.tender.audit.utils import auditresource, save_audit, apply_patch
from openprocurement.tender.audit.validation import validate_audit_document_operation_not_in_allowed_audit_status


@auditresource(
    name='Audit Answer Documents',
    collection_path='/audits/{audit_id}/answers/{answer_id}/documents',
    path='/audits/{audit_id}/answers/{answer_id}/documents/{document_id}',
    description='Audit answers documents'
)
class AuditAnswerDocumentResource(APIResource):
    @json_view(permission='view_audit')
    def collection_get(self):
        """Audit Answer Documents List"""
        if self.request.params.get('all', ''):
            collection_data = [i.serialize('view') for i in self.context.documents]
        else:
            collection_data = sorted(
                dict(
                    [(i.id, i.serialize('view')) for i in self.context.documents]
                ).values(), key=lambda i: i['dateModified']
            )
        return {'data': collection_data}

    @json_view(permission='view_audit')
    def get(self):
        """Audit Answer Document Read"""
        if self.request.params.get('download'):
            return get_file(self.request)

        document = self.request.validated['document']
        document_data = document.serialize('view')

        document_data['previousVersions'] = [
            i.serialize('view') for i in self.request.validated['documents'] if i.url != document.url
        ]

        return {'data': document_data}

    @json_view(permission='upload_audit_documents', validators=(
            validate_file_upload, validate_audit_document_operation_not_in_allowed_audit_status
    ))
    def collection_post(self):
        """Audit Answer Document Upload"""
        document = upload_file(self.request)
        self.context.documents.append(document)

        if save_audit(self.request):
            self.LOGGER.info(
                'Create audit answer document {}'.format(document.id),
                extra=context_unpack(
                    self.request, {'MESSAGE_ID': 'audit_answer_document_create'}, {'document_id': document.id}
                )
            )
            self.request.response.status = 201
            document_route = self.request.matched_route.name.replace('collection_', '')
            self.request.response.headers['Location'] = self.request.current_route_url(
                _route_name=document_route, document_id=document.id, _query={}
            )
            return {'data': document.serialize('view')}

    @json_view(permission='edit_audit', validators=(
            validate_file_update, validate_audit_document_operation_not_in_allowed_audit_status
    ))
    def put(self):
        document = upload_file(self.request)
        self.request.validated['answer'].documents.append(document)

        if save_audit(self.request):
            self.LOGGER.info(
                'Updated audit answer document {}'.format(self.request.context.id),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'audit_answer_document_put'})
            )
            return {'data': document.serialize('view')}

    @json_view(
        content_type="application/json", permission='edit_audit', validators=(
                validate_patch_document_data, validate_audit_document_operation_not_in_allowed_audit_status
        )
    )
    def patch(self):
        """Audit Answer Document Update"""
        if apply_patch(self.request, src=self.request.context.serialize()):
            update_file_content_type(self.request)
            self.LOGGER.info(
                'Updated audit answer document {}'.format(self.request.context.id),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'audit_answer_document_patch'})
            )
            return {'data': self.request.context.serialize('view')}



