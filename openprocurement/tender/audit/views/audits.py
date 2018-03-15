# coding=utf-8
from openprocurement.api.utils import opresource, APIResource, json_view
from openprocurement.tender.audit.models import Audit
from pyramid.view import view_config
from logging import getLogger
from openprocurement.tender.audit.design import audits_all_view

logger = getLogger("{}.init".format(__name__))


@opresource(name='Audits', path='/audits', description="Audit data")
class AuditResource(APIResource):
    def __init__(self, request, context):
        super(AuditResource, self).__init__(request, context)
        self.server = request.registry.couchdb_server
        self.update_after = request.registry.update_after

    @json_view()
    def get(self):
        res = audits_all_view(self.db)
        logger.info("res = {}". format(res))
        logger.info("res = {}". format(res.__dict__))
        for x in res:
            logger.info("x= {}".format(x))
        results = [
            (dict([(i, j) for i, j in x.value.items() + [('id', x.id), ('date_modified', x.key)]]), x.key)
            for x in res
        ]
        return {"data": []}


# @view_config(route_name='audits', renderer='json', request_method='POST')
# def post_audit(request):
#     """:return status of proxy server"""
#     logger.info("posting audit")
#     audit = Audit()
#     return ''
