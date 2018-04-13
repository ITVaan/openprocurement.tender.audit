# coding=utf-8
from logging import getLogger
from unittest import TestCase

from openprocurement.tender.audit.tests.base import BaseWebTest
from openprocurement.tender.audit.utils import save_audit, audit_from_data

from pyramid import testing
from openprocurement.tender.audit.models import Audit

logger = getLogger(__name__)


class TestAuditModel(BaseWebTest):
    def test_create_audit(self):
        mock_audit = Audit.get_mock_object()
        audit_data = mock_audit.to_primitive()
        mock_audit_2 = audit_from_data(None, audit_data, True)
        self.assertEqual(mock_audit, mock_audit_2)
