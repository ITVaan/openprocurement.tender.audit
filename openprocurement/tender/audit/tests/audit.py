import unittest

from copy import deepcopy

from openprocurement.api.tests.base import snitch

from openprocurement.tender.audit.tests.base import BaseAuditWebTest, BaseWebTest, test_audit_data, documents
from openprocurement.tender.audit.tests.audit_blanks import (
    create_audit_invalid,
    create_audit,
    audit_status_change,
    patch_audit,
    create_audit_with_documents
)


class AuditResourceTests(BaseAuditWebTest):
    initial_auth = ('Basic', ('broker', ''))

    test_create_invalid_audit = snitch(create_audit_invalid)
    test_create_audit = snitch(create_audit)


class AuditResource4BrokersTest(BaseAuditWebTest):
    """ audit resource test """
    initial_auth = ('Basic', ('administrator', ''))

    test_audit_status_change = snitch(audit_status_change)
    test_patch_audit = snitch(patch_audit)


class AuditDocumentsWithDSResourceTest(BaseWebTest):
    docservice = True
    initial_data = deepcopy(test_audit_data)
    documents = deepcopy(documents)
    initial_data['documents'] = documents

    test_create_audit_with_documents = snitch(create_audit_with_documents)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuditResourceTest))
    suite.addTest(unittest.makeSuite(AuditResource4BrokersTest))
    suite.addTest(unittest.makeSuite(AuditDocumentsWithDSResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')


