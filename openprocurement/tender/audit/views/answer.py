from openprocurement.api.utils import APIResource, json_view, set_ownership

from openprocurement.tender.audit.utils import auditresource, save_audit, context_unpack, apply_patch
from openprocurement.tender.audit.validation import validate_answer_data, validate_patch_answer_data


@auditresource(
    name='Audit answers', collection_path='/audits/{audit_id}/answers',
    path='/audits/{audit_id}/answers/{answer_id}', description='Audit answers'
)
class AnswersResource(APIResource):
    @json_view(permission='view_audit')
    def get(self):
        """ Return Audit Answer """
        return {'data': self.request.validated['answer'].serialize('view')}

    @json_view(permission='view_audit')
    def collection_get(self):
        """Audit Answers List"""
        return {'data': [i.serialize('view') for i in self.request.validated['audit'].answers]}

    @json_view(content_type='application/json', permission='create_audit', validators=(validate_answer_data,))
    def collection_post(self):
        audit = self.request.validated.get('audit')
        answer = self.request.validated['answer']
        set_ownership(answer, self.request)
        audit.answers.append(answer)
        audit.modified = False

        if save_audit(self.request):
            self.LOGGER.info(
                'Created audit answer {}'.format(answer.id),
                extra=context_unpack(
                    self.request,
                    {'MESSAGE_ID': 'audit_answer_create'},
                    {'answer_id': answer.id}
                )
            )
            self.request.response.status = 201
            return {'data': answer.serialize('view')}

    @json_view(content_type="application/json", permission='edit_audit', validators=(validate_patch_answer_data,))
    def patch(self):
        audit = self.request.validated['audit']
        apply_patch(self.request, save=False, src=self.request.validated['answer'].serialize())

        if save_audit(self.request):
            self.LOGGER.info(
                'Updated audit {} answer {}'.format(audit.id, self.request.validated['answer'].get('id')),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'answer_patch'})
            )
            return {'data': self.request.context.serialize('view')}






