# -*- coding: utf-8 -*-
"""Main entry point
"""
import os

from couchdb.http import extract_credentials, Unauthorized
from openprocurement.tender.audit.design import sync_design
from pyramid.settings import asbool

if 'test' not in __import__('sys').argv[0]:
    import gevent.monkey

    gevent.monkey.patch_all()

from logging import getLogger
from couchdb import Server as CouchdbServer, Session
from openprocurement.tender.audit.utils import ROUTE_PREFIX, VERSION

LOGGER = getLogger("{}.init".format(__name__))


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
    from auth import authenticated_role
    from utils import (forbidden, add_logging_context, set_logging_context, auth_check,
                       request_params, set_renderer, Root, read_users)
    from pyramid.authentication import BasicAuthAuthenticationPolicy
    from pyramid.authorization import ACLAuthorizationPolicy
    from pyramid.config import Configurator
    from pyramid.events import NewRequest, ContextFound
    from pyramid.renderers import JSON, JSONP

    LOGGER.info('Start edr api')
    read_users(settings['auth.file'])
    config = Configurator(
        autocommit=True,
        settings=settings,
        authentication_policy=BasicAuthAuthenticationPolicy(auth_check, __name__),
        authorization_policy=ACLAuthorizationPolicy(),
        root_factory=Root,
        route_prefix=ROUTE_PREFIX,
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

    # Include views
    config.add_route('health', '/health')
    config.scan("openprocurement.tender.audit.views")
    return config.make_wsgi_app()
