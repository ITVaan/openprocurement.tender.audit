import unittest

from openprocurement.api.tests.base import snitch

from openprocurement.tender.audit.tests.base import BaseAuditWebTest
from openprocurement.tender.audit.tests.answer_blank import create_audit_answer


class AuditAnswerResourceTest(BaseAuditWebTest):
    """ audit resource test """
    initial_auth = ('Basic', ('administrator', ''))

    test_create_audit_answer = snitch(create_audit_answer)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuditAnswerResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
