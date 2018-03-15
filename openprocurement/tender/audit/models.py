# coding=utf-8
import os
import re
from pytz import timezone
from datetime import datetime
from pkg_resources import get_distribution
from logging import getLogger
from requests import Session
from pyramid.security import Allow

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from iso8601 import parse_date, ParseError
from uuid import uuid4
from urlparse import urlparse, parse_qs
from string import hexdigits
from hashlib import algorithms, new as hash_new
from couchdb_schematics.document import SchematicsDocument
from schematics.exceptions import ConversionError, ValidationError
from schematics.models import Model as SchematicsModel
from schematics.transforms import whitelist, blacklist, export_loop, convert
from schematics.types import (StringType, FloatType, URLType, IntType,
                              BooleanType, BaseType, EmailType, MD5Type, DecimalType as BaseDecimalType)
from schematics.types.compound import (ModelType, DictType,
                                       ListType as BaseListType)
from openprocurement.api.models import (Model, ListType, Revision, Value,
                                        IsoDateTimeType)
from schematics.types.serializable import serializable

from openprocurement.api.utils import get_now, set_parent, get_schematics_document
from openprocurement.api.models import Item as BaseItem
from openprocurement.api.models import (
    plain_role, schematics_default_role, schematics_embedded_role
)
from openprocurement.api.constants import (
    CPV_CODES, ORA_CODES, TZ, DK_CODES, CPV_BLOCK_FROM, ATC_CODES, INN_CODES, ATC_INN_CLASSIFICATIONS_FROM,
)

from openprocurement.api.models import Contract as BaseContract
from openprocurement.api.models import Document as BaseDocument
from openprocurement.api.models import Organization as BaseOrganization
from openprocurement.api.models import ContactPoint as BaseContactPoint
from openprocurement.api.models import CPVClassification as BaseCPVClassification
# from openprocurement.tender.core.models import Administrator_role
from openprocurement.api.validation import validate_items_uniq

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

# TODO audit admin

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
    """ Contract Document """
    documentType = StringType(choices=["startMonitoring", "suit", "stopMonitoring"])


class Answer(Model):
    """Answer to complaint"""

    description = StringType()
    documents = ListType(ModelType(Document), default=list())
    dateCreated = IsoDateTimeType()
    response_to = id = MD5Type(required=False)


class Offense(Answer):
    id = MD5Type(required=True, default=lambda: uuid4().hex)
    status = StringType(choices=['fixed', 'not_fixed', 'partially_fixed'], default='not_fixed')
    typical_offenses = ListType(StringType)


class Conclusion(Answer):
    status = StringType(choices=['appealed', 'not_appealed'], default='not_appealed')


class Audit(SchematicsDocument):
    """ audit """

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    revisions = ListType(ModelType(Revision), default=list())
    author = ModelType(Organization, required=True)  # author of claim
    title = StringType(required=True)  # title of the claim
    date_created = IsoDateTimeType(default=get_now)
    date_published = IsoDateTimeType()
    date_modified = IsoDateTimeType()
    date_finished = IsoDateTimeType()
    _attachments = DictType(DictType(BaseType), default=dict())  # couchdb attachments
    tender_id = StringType(required=True)
    owner_token = StringType(default=lambda: uuid4().hex)
    owner = StringType()
    mode = StringType(choices=['test'])
    status = StringType(choices=['terminated', 'draft', 'published'], default='draft')
    changes = ListType(ModelType(Change), default=list())
    documents = ListType(ModelType(Document), default=list())
    termination_details = StringType()
    answers = ListType(ModelType(Answer))
    conclusions = ListType(ModelType(Conclusion))
    offenses = ListType(ModelType(Offense))

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
        return dict([('{}_{}'.format(self.owner, self.owner_token), 'audit_owner'),
                     ('{}_{}'.format(self.owner, self.tender_token), 'tender_owner')])

    def __acl__(self):
        acl = [
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_audit'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_audit_documents'),
            (Allow, '{}_{}'.format(self.owner, self.tender_token), 'generate_credentials')
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

    @serializable(serialized_name='amountPaid', serialize_when_none=False, type=ModelType(Value))
    def audit_amountPaid(self):
        if self.amountPaid:
            return Value(dict(amount=self.amountPaid.amount,
                              currency=self.value.currency,
                              valueAddedTaxIncluded=self.value.valueAddedTaxIncluded))
