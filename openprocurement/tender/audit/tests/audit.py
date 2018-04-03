import unittest

from openprocurement.api.tests.base import snitch

from openprocurement.tender.audit.tests.base import BaseAuditWebTest
from openprocurement.tender.audit.tests.audit_blanks import create_invalid_audit, create_audit, patch_audit


class AuditResourceTest(BaseAuditWebTest):
    """ audit resource test """
    initial_auth = ('Basic', ('administrator', ''))

    test_create_invalid_audit = snitch(create_invalid_audit)
    test_create_audit = snitch(create_audit)
    test_patch_audit = snitch(patch_audit)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuditResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')


