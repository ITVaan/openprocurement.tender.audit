# -*- coding: utf-8 -*-
from logging import getLogger
from pkg_resources import get_distribution

from openprocurement.tender.audit.utils import audit_from_data

PKG = get_distribution(__package__)
LOGGER = getLogger(PKG.project_name)


def includeme(config):
    LOGGER.info('Init tender audit plugin.')
    config.scan("openprocurement.tender.audit.views")
    config.registry.tender_id = {}
    config.add_request_method(audit_from_data)
