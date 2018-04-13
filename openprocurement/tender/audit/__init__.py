# -*- coding: utf-8 -*-
"""Main entry point
"""
import os

from openprocurement.api.subscribers import add_logging_context, set_logging_context, set_renderer
from couchdb.http import extract_credentials, Unauthorized
from libnacl.sign import Signer, Verifier
from openprocurement.api.auth import authenticated_role
from openprocurement.api.utils import request_params, forbidden
from openprocurement.tender.audit.design import sync_design
from pyramid.settings import asbool
from pkg_resources import get_distribution
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

    @property
    def uuid(self):
        """The uuid of the server.

        :rtype: basestring
        """
        if self._uuid is None:
            _, _, data = self.resource.get_json()
            self._uuid = data['uuid']
        return self._uuid


def main(global_config, **settings):
    LOGGER.info('Init tender audit plugin.')

    read_users(settings['auth.file'])
    config = Configurator(
        autocommit=True,
        settings=settings,
        authentication_policy=BasicAuthAuthenticationPolicy(auth_check, __name__),
        authorization_policy=ACLAuthorizationPolicy(),
        root_factory=Root,
        route_prefix="/api/2.4",
    )
    config.include('pyramid_exclog')
    config.include("cornice")
    config.add_forbidden_view(forbidden)
    config.add_request_method(request_params, 'params', reify=True)
    config.add_request_method(authenticated_role, reify=True)
    config.add_renderer('prettyjson', JSON(indent=4))
    config.add_renderer('jsonp', JSONP(param_name='opt_jsonp'))
    config.add_renderer('prettyjsonp', JSONP(indent=4, param_name='opt_jsonp'))
    config.add_subscriber(add_logging_context, NewRequest)
    config.add_subscriber(set_logging_context, ContextFound)
    config.add_subscriber(set_renderer, NewRequest)

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
    sync_design(db)
    config.registry.db = db
    config.registry.server_id = settings.get('id', '')
    config.registry.update_after = asbool(settings.get('update_after', True))
    config.registry.tender_id = {}
    config.add_request_method(extract_audit, 'audit', reify=True)
    config.add_request_method(audit_from_data)

    # Document Service key
    config.registry.docservice_url = settings.get('docservice_url')
    config.registry.docservice_username = settings.get('docservice_username')
    config.registry.docservice_password = settings.get('docservice_password')
    config.registry.docservice_upload_url = settings.get('docservice_upload_url')
    config.registry.docservice_key = dockey = Signer(settings.get('dockey', '').decode('hex'))
    config.registry.keyring = keyring = {}
    dockeys = settings.get('dockeys') if 'dockeys' in settings else dockey.hex_vk()
    for key in dockeys.split('\0'):
        keyring[key[:8]] = Verifier(key)

    # Include views
    config.add_route('health', '/health')
    config.scan("openprocurement.tender.audit.views")
    return config.make_wsgi_app()
