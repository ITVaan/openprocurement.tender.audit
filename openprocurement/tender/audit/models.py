# coding=utf-8
from pyramid.security import Allow

from uuid import uuid4

from couchdb_schematics.document import SchematicsDocument
from schematics.exceptions import ValidationError
from schematics.transforms import whitelist, blacklist
from schematics.types import StringType, BaseType, MD5Type
from schematics.types.compound import ModelType, DictType
from openprocurement.api.models import Model, ListType, Revision, IsoDateTimeType
from schematics.types.serializable import serializable

from openprocurement.api.utils import get_now, set_parent, get_schematics_document
from openprocurement.api.models import Item as BaseItem
from openprocurement.api.models import (
    plain_role, schematics_default_role, schematics_embedded_role
)

from openprocurement.api.models import Document as BaseDocument, Value as BaseValue, Period as BasePeriod
from openprocurement.api.models import Organization as BaseOrganization
from openprocurement.api.models import ContactPoint as BaseContactPoint
# from openprocurement.tender.core.models import Administrator_role

item_edit_role = whitelist(
    'description', 'description_en', 'description_ru', 'unit', 'deliveryDate',
    'deliveryAddress', 'deliveryLocation', 'quantity', 'id')


class Item(BaseItem):
    class Options:
        roles = {
            'edit_active': item_edit_role,
            'view': schematics_default_role,
            'embedded': schematics_embedded_role,
        }


audit_create_role = (whitelist(
    'id', 'awardID', 'auditID', 'auditNumber', 'title', 'title_en',
    'title_ru', 'description', 'description_en', 'description_ru', 'status',
    'period', 'value', 'dateSigned', 'items', 'suppliers',
    'procuringEntity', 'owner', 'tender_token', 'tender_id', 'mode'
))

audit_edit_role = (whitelist(
    'title', 'title_en', 'title_ru', 'description', 'description_en',
    'description_ru', 'status', 'period', 'value', 'items', 'amountPaid',
    'terminationDetails', 'audit_amountPaid',
))

audit_view_role = (whitelist(
    'id', 'awardID', 'auditID', 'dateModified', 'auditNumber', 'title',
    'title_en', 'title_ru', 'description', 'description_en', 'description_ru',
    'status', 'period', 'value', 'dateSigned', 'documents', 'items',
    'suppliers', 'procuringEntity', 'owner', 'mode', 'tender_id', 'changes',
    'amountPaid', 'terminationDetails', 'audit_amountPaid',
))

# audit_administrator_role = (Administrator_role + whitelist('suppliers', ))


class ContactPoint(BaseContactPoint):
    availableLanguage = StringType()


class Organization(BaseOrganization):
    """An organization."""
    contactPoint = ModelType(ContactPoint, required=True)
    additionalContactPoints = ListType(ModelType(ContactPoint, required=True), required=False)


class ProcuringEntity(Organization):
    """An organization."""

    class Options:
        roles = {
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
            'edit_active': schematics_default_role + blacklist("kind"),
        }

    kind = StringType(choices=['general', 'special', 'defense', 'other'])


class Change(Model):
    class Options:
        roles = {
            'create': whitelist('rationale', 'rationale_ru', 'rationale_en', 'rationaleTypes', 'auditNumber',
                                'dateSigned'),
            'edit': whitelist('rationale', 'rationale_ru', 'rationale_en', 'rationaleTypes', 'auditNumber', 'status',
                              'dateSigned'),
            'view': schematics_default_role,
            'embedded': schematics_embedded_role,
        }

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    status = StringType(choices=['pending', 'active'], default='pending')
    date = IsoDateTimeType(default=get_now)
    rationale = StringType(required=True, min_length=1)
    rationale_en = StringType()
    rationale_ru = StringType()
    rationaleTypes = ListType(StringType(choices=['volumeCuts', 'itemPriceVariation',
                                                  'qualityImprovement', 'thirdParty',
                                                  'durationExtension', 'priceReduction',
                                                  'taxRate', 'fiscalYearExtension'],
                                         required=True), min_size=1, required=True)
    auditNumber = StringType()
    dateSigned = IsoDateTimeType()

    def validate_dateSigned(self, data, value):
        if value and value > get_now():
            raise ValidationError(u"audit signature date can't be in the future")


class Document(BaseDocument):
    """ Audit Document """
    documentType = StringType(choices=["startMonitoring", "suit", "stopMonitoring", ""])
    documentOf = StringType(
        required=True, choices=['audit', 'change'], default='audit'
    )


class Answer(Model):
    """Answer to complaint"""

    description = StringType()
    documents = ListType(ModelType(Document), default=list())
    dateCreated = IsoDateTimeType()


class Offense(Answer):
    status = StringType(choices=['fixed', 'not_fixed', 'partially_fixed'], default='not_fixed')
    typical_offenses = ListType(StringType(choices=[
        'corruptionDescription', 'corruptionProcurementMethodType', 'corruptionPublicDisclosure',
        'corruptionBiddingDocuments', 'documentsForm', 'corruptionAwarded', 'corruptionCancelled',
        'corruptionContracting', 'corruptionChanges', 'other'
    ]), required=True)


class Tender(SchematicsDocument, Model):
    title = StringType(required=True)
    value = ModelType(BaseValue, required=True)
    tenderID = StringType()
    date_published = IsoDateTimeType()
    procurementMethodType = StringType()


class Conclusion(Answer):
    audit_id = StringType(required=True)
    tender = ModelType(Tender, required=True)
    status = StringType(choices=['appealed', 'not_appealed'], default='not_appealed')
    customer = ModelType(Organization, required=True)
    procurementMethodType = StringType()
    grounds = ListType(StringType(choices=['indicator', 'authorities', 'media', 'fiscal', 'public']), default=list())
    period = ModelType(BasePeriod)
    monitoring_results = StringType()
    obligation = StringType()


class Audit(SchematicsDocument, Model):
    """ audit """
    revisions = ListType(ModelType(Revision), default=list())
    author = ModelType(Organization, required=True)  # author of claim
    title = StringType(required=True)  # title of the claim
    date_created = IsoDateTimeType(default=get_now)
    date_published = IsoDateTimeType()
    date_modified = IsoDateTimeType()
    date_finished = IsoDateTimeType()
    _attachments = DictType(DictType(BaseType), default=dict())  # couchdb attachments
    tender_id = StringType(required=True)
    procurementMethodType = StringType()
    grounds = ListType(
        StringType(choices=['indicator', 'authorities', 'media', 'fiscal', 'public']), required=True
    )
    procurement_stage = ListType(StringType(choices=['planing', 'awarding', 'contracting']), required=True)
    period = ModelType(BasePeriod)
    owner_token = StringType(default=lambda: uuid4().hex)
    owner = StringType()
    mode = StringType(choices=['test'])
    status = StringType(choices=['terminated', 'draft', 'published'], default='draft')
    changes = ListType(ModelType(Change), default=list())
    documents = ListType(ModelType(Document), default=list())
    termination_details = StringType()

    class Options:
        roles = {
            'plain': plain_role,
            'create': audit_create_role,
            'edit_active': audit_edit_role,
            'edit_terminated': whitelist(),
            'view': audit_view_role,
            # 'Administrator': audit_administrator_role,
            'default': schematics_default_role,
        }

    def __local_roles__(self):
        return dict([('{}_{}'.format(self.owner, self.owner_token), 'audit_owner')])

    def __acl__(self):
        acl = [
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_audit'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_audit_documents')
        ]
        return acl

    def import_data(self, raw_data, **kw):
        """
        Converts and imports the raw data into the instance of the model
        according to the fields in the model.
        :param raw_data:
            The data to be imported.
        """
        data = self.convert(raw_data, **kw)
        del_keys = [k for k in data.keys() if
                    data[k] == self.__class__.fields[k].default or data[k] == getattr(self, k)]
        for k in del_keys:
            del data[k]

        self._data.update(data)
        return self

    def get_role(self):
        root = self.__parent__
        request = root.request
        if request.authenticated_role == 'Administrator':
            role = 'Administrator'
        else:
            role = 'edit_{}'.format(request.context.status)
        return role

    @serializable(serialized_name='id')
    def doc_id(self):
        """A property that is serialized by schematics exports."""
        return self._id


