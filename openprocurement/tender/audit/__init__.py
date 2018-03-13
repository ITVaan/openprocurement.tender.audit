# -*- coding: utf-8 -*-
from logging import getLogger
from pkg_resources import get_distribution

PKG = get_distribution(__package__)

LOGGER = getLogger(PKG.project_name)


def includeme(config):
    # from openprocurement.tender.api.utils import contract_from_data, extract_contract
    # from openprocurement.tender.api.design import add_design
    LOGGER.info('Init tender audit plugin.')
    # add_design()
    # config.add_request_method(extract_contract, 'contract', reify=True)
    # config.add_request_method(contract_from_data)
    config.scan("openprocurement.tender.audit.views")
