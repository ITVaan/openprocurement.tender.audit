import unittest

from openprocurement.api.tests.base import snitch

from openprocurement.tender.audit.tests.base import BaseAuditWebTest
from openprocurement.tender.audit.tests.offense_blank import create_audit_offense


class AuditOffenseResourceTest(BaseAuditWebTest):
    """ audit resource test """
    initial_auth = ('Basic', ('administrator', ''))

    test_create_audit_offense = snitch(create_audit_offense)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuditOffenseResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')