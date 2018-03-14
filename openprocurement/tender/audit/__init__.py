# -*- coding: utf-8 -*-
"""Main entry point
"""
if 'test' not in __import__('sys').argv[0]:
    import gevent.monkey

    gevent.monkey.patch_all()

from logging import getLogger

from reports.brokers.utils import ROUTE_PREFIX

LOGGER = getLogger("{}.init".format(__name__))


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
    config.add_forbidden_view(forbidden)
    config.add_request_method(request_params, 'params', reify=True)
    config.add_request_method(authenticated_role, reify=True)
    config.add_renderer('prettyjson', JSON(indent=4))
    config.add_renderer('jsonp', JSONP(param_name='opt_jsonp'))
    config.add_renderer('prettyjsonp', JSONP(indent=4, param_name='opt_jsonp'))
    config.add_subscriber(add_logging_context, NewRequest)
    config.add_subscriber(set_logging_context, ContextFound)
    config.add_subscriber(set_renderer, NewRequest)
    # Include views
    config.add_route('health', '/health')
    # config.scan("reports.brokers.api.views")
    return config.make_wsgi_app()
