# coding=utf-8
from pyramid.view import view_config
from logging import getLogger

logger = getLogger("{}.init".format(__name__))


@view_config(route_name='health', renderer='json', request_method='GET')
def health(request):
    """:return status of proxy server"""
    logger.info("sending health")
    return ''
