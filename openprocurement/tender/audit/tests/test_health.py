# coding=utf-8
import webtest
from gevent import monkey

monkey.patch_all()
from openprocurement.tender.audit.tests.base import BaseWebTest


class HealthTestSuite(BaseWebTest):

    def test_health(self):
        response = self.app.get('/health', expect_errors=True)
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
