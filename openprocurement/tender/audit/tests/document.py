import unittest
from openprocurement.api.tests.base import snitch

from openprocurement.tender.audit.tests.base import BaseAuditWebTest

from openprocurement.tender.audit.tests.document_blanks import (
    not_found,
    create_audit_document,
    put_audit_document,
    patch_audit_document,
    create_audit_document_json_invalid,
    create_audit_document_json,
    put_audit_document_json
)


class AuditDocumentResourceTest(BaseAuditWebTest):
    docservice = False
    initial_auth = ('Basic', ('broker', ''))

    test_not_found = snitch(not_found)
    test_create_audit_document = snitch(create_audit_document)
    test_put_audit_document = snitch(put_audit_document)
    test_patch_audit_document = snitch(patch_audit_document)


class AuditDocumentWithDSResourceTest(AuditDocumentResourceTest):
    docservice = True
    test_create_audit_document_json_invalid = snitch(create_audit_document_json_invalid)
    test_create_audit_document_json = snitch(create_audit_document_json)
    test_put_audit_document_json = snitch(put_audit_document_json)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuditDocumentResourceTest))
    suite.addTest(unittest.makeSuite(AuditDocumentWithDSResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')


