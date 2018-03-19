# -*- coding: utf-8 -*-
from logging import getLogger
from pkg_resources import get_distribution

from openprocurement.tender.audit.utils import audit_from_data, extract_audit

PKG = get_distribution(__package__)
LOGGER = getLogger(PKG.project_name)


def includeme(config):
    LOGGER.info('Init tender audit plugin.')
    config.registry.tender_id = {}
    config.add_request_method(extract_audit, 'audit', reify=True)
    config.add_request_method(audit_from_data)
    config.scan("openprocurement.tender.audit.views")
