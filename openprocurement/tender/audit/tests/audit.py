import unittest

from openprocurement.api.tests.base import snitch

from openprocurement.tender.audit.tests.base import BaseAuditWebTest
from openprocurement.tender.audit.tests.audit_blanks import patch_audit


class AuditResourceTest(BaseAuditWebTest):
    """ audit resource test """
    initial_auth = ('Basic', ('administrator', ''))

    test_patch_audit = snitch(patch_audit)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuditResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')


