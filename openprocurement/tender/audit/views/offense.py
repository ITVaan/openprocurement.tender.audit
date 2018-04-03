from openprocurement.api.utils import APIResource, json_view, set_ownership

from openprocurement.tender.audit.utils import auditresource, save_audit, context_unpack, apply_patch
from openprocurement.tender.audit.validation import validate_offense_data, validate_patch_offense_data


@auditresource(
    name='Audit offenses', collection_path='/audits/{audit_id}/offenses',
    path='/audits/{audit_id}/offenses/{offense_id}', description='Audit offenses'
)
class OffenseResource(APIResource):
    @json_view(permission='view_audit')
    def get(self):
        """
         Return Audit Offense
         """
        return {'data': self.request.validated['offense'].serialize('view')}

    @json_view(permission='view_audit')
    def collection_get(self):
        return {'data': [i.serialize('view') for i in self.request.validated['audit'].offenses]}

    @json_view(content_type='application/json', permission='create_audit', validators=(validate_offense_data,))
    def collection_post(self):
        audit = self.request.validated.get('audit')
        offense = self.request.validated.get('offense')

        set_ownership(offense, self.request)
        audit.offenses.append(offense)
        audit.modified = False

        if save_audit(self.request):
            self.LOGGER.info(
                'Create audit offense {}'.format(offense.id),
                extra=context_unpack(
                    self.request,
                    {'MESSAGE_ID': 'audit_offense_create'},
                    {'offense_id': offense.id}
                )
            )
            self.request.response.status = 201
            return {'data': offense.serialize('view')}

    @json_view(content_type='application/json', permission='edit_audit', validators=(validate_patch_offense_data,))
    def patch(self):
        audit = self.request.validated['audit']
        apply_patch(self.request, save=False, src=self.request.validated['offense'].serialize())

        if save_audit(self.request):
            self.LOGGER.info(
                'Updated audit {} offense {}'.format(audit.id, self.request.validated['offense'].get('id')),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'offense_patch'})
            )
            return {'data': self.request.context.serialize('view')}








