from openprocurement.api.utils import update_logging_context
from openprocurement.api.validation import validate_json_data, validate_data


def validate_audit_data(request):
    update_logging_context(request, {'audit_id': '__new__'})
    data = request.validated['json_data'] = validate_json_data(request)
    model = request.audit_from_data(data, create=False)
    return validate_data(request, model, data=data)
