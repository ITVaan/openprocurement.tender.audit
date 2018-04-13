# coding=utf-8
from openprocurement.api.utils import error_handler
from logging import getLogger

from openprocurement_client.client import TendersClientSync

logger = getLogger(__name__)


def check_tender_exists_local(request, tender_id):
    db = request.registry.db
    doc = db.get(tender_id)

    if doc is None or doc.get('doc_type') != 'Tender':
        request.errors.add('url', 'tender_id', 'Not Found')
        request.errors.status = 404
        raise error_handler(request.errors)

    return True


def check_tender_exists_api(request, tender_id):
    ro_api_server = "localhost"
    api_version = "2.4"
    tenders_sync_client = TendersClientSync('', host_url=ro_api_server, api_version=api_version)
    try:
        response = tenders_sync_client.request("GET", path='{}/{}'.format(tenders_sync_client.prefix_path,
                                                                          tender_id))
    except Exception as e:
        if getattr(e, "status_int", False) == 429:
            logger.info("Waiting tender {}".format(tender_id))
        elif getattr(e, "status_int", False) == 404:
            request.errors.add('url', 'tender_id', 'Not Found')
            request.errors.status = 404
            raise error_handler(request.errors)
        else:
            logger.warning('Fail to get tender info {}'.format(tender_id))
            logger.exception("Message: {}".format(e.message))
    return True
