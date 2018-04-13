# coding=utf-8
import os

from couchdb_schematics.document import DocumentMeta
from openprocurement.tender.audit import read_users, audit_from_data, auth_check
from logging import getLogger

from openprocurement.tender.audit.models import Audit
from openprocurement.tender.audit.tests.base import test_audit_data, BaseWebTest
from openprocurement.tender.audit.utils import USERS, extract_audit

logger = getLogger(__name__)


class TestUtils(BaseWebTest):
    def setUp(self):
        super(TestUtils, self).setUp()

    def test_read_users(self):
        read_users(os.path.dirname(__file__)+'/auth.ini')
        logger.info("USERS = {}".format(USERS))
        self.assertIsNotNone(USERS)

    def test_audit_from_data(self):
        data = test_audit_data
        audit = audit_from_data(request=None, data=data)
        self.assertEqual(type(audit), Audit)

    def test_audit_from_data_nocreate(self):
        data = test_audit_data
        audit = audit_from_data(request=None, data=data, create=False)
        self.assertEqual(type(audit), DocumentMeta)

    def test_auth_check(self):
        read_users(os.path.dirname(__file__)+'/auth.ini')
        res = auth_check('broker', 'broker', None)
        self.assertEqual(res[0], "g:brokers")

    # def test_extract_audit(self):
    #     request = Request()
    #     extract_audit(request)

