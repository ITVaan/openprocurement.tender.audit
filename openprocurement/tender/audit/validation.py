# coding=utf-8
from schematics.exceptions import ModelValidationError, ModelConversionError

from openprocurement.api.utils import update_logging_context, error_handler, apply_data_patch
from openprocurement.api.validation import validate_json_data

from openprocurement.tender.audit.utils import check_tender_exists
from openprocurement.tender.audit.models import Audit
from logging import getLogger

logger = getLogger("{}.init".format(__name__))


def validate_data(request, model, partial=False, data=None):
    logger.info("validating data")
    if data is None:
        logger.info("validating audit data; request role {}".format(request.context.get_role()))
        data = validate_json_data(request)
    try:
        if partial and isinstance(request.context, model):
            initial_data = request.context.serialize()
            m = model(initial_data)
            new_patch = apply_data_patch(initial_data, data)
            if new_patch:
                m.import_data(new_patch, partial=True, strict=True)
            m.__parent__ = request.context.__parent__
            m.validate()
            role = request.context.get_role()
            method = m.to_patch
        else:
            m = model(data)
            m.__parent__ = request.context
            m.validate()
            method = m.serialize
            role = 'create'
    except (ModelValidationError, ModelConversionError) as e:
        for i in e.message:
            request.errors.add('body', i, e.message[i])
        request.errors.status = 422
        raise error_handler(request.errors)
    except ValueError as e:
        request.errors.add('body', 'data', e.message)
        request.errors.status = 422
        raise error_handler(request.errors)
    else:
        if hasattr(type(m), '_options') and role not in type(m)._options.roles:
            logger.info("403 will be returned because role {}".format(role))
            request.errors.add('url', 'role', 'Forbidden')
            request.errors.status = 403
            raise error_handler(request.errors)
        else:
            # data = method(role)
            request.validated['data'] = data
            if not partial:
                m = model(data)
                m.__parent__ = request.context
                request.validated[model.__name__.lower()] = m
        data = method(role)
    return data


def validate_audit_data(request):
    update_logging_context(request, {'audit_id': '__new__'})
    data = request.validated['json_data'] = validate_json_data(request)

    # check_tender_exists(request, data.get('tender_id'))
    model = request.audit_from_data(data, create=False)
    # logger.info("validating audit data; request role {}".format(request.context.get_role()))

    return validate_data(request, model, data=data)


def validate_patch_audit_data(request):
    logger.info("validating patch audit; request role {}".format(request.context.get_role()))
    return validate_data(request, Audit, True)

