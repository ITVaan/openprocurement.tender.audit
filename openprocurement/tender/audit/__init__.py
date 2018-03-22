# -*- coding: utf-8 -*-
"""Main entry point
"""
import os

from couchdb.http import extract_credentials, Unauthorized
# from openprocurement.tender.audit.design import sync_design
from pyramid.settings import asbool
from pkg_resources import get_distribution
# from auth import authenticated_role
from traversal import Root
from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.events import NewRequest, ContextFound
from pyramid.renderers import JSON, JSONP
from openprocurement.tender.audit.utils import audit_from_data, extract_audit, auth_check, read_users
from logging import getLogger
from couchdb import Server as CouchdbServer, Session
    # ROUTE_PREFIX, VERSION

PKG = get_distribution(__package__)
LOGGER = getLogger(PKG.project_name)

class Server(CouchdbServer):
    _uuid = None

def main(global_config, **settings):
    LOGGER.info('Init tender audit plugin.')

    read_users(settings['auth.file'])
    config = Configurator(
        autocommit=True,
        settings=settings,
        authentication_policy=BasicAuthAuthenticationPolicy(auth_check, __name__),
        authorization_policy=ACLAuthorizationPolicy(),
        root_factory=Root,
        route_prefix="/api",
    )
    config.include('pyramid_exclog')
    config.include("cornice")

    db_name = os.environ.get('DB_NAME', settings['couchdb.db_name'])
    server = Server(settings.get('couchdb.url'), session=Session(retry_delays=range(10)))
    if 'couchdb.admin_url' not in settings and server.resource.credentials:
        try:
            server.version()
        except Unauthorized:
            server = Server(extract_credentials(settings.get('couchdb.url'))[0])
    config.registry.couchdb_server = server
    if db_name not in server:
        server.create(db_name)
    db = server[db_name]
    # sync_design(db)
    config.registry.db = db
    config.registry.tender_id = {}
    config.add_request_method(extract_audit, 'audit', reify=True)
    config.add_request_method(audit_from_data)

    # Include views
    config.add_route('health', '/health')
    config.scan("openprocurement.tender.audit.views")
    return config.make_wsgi_app()
