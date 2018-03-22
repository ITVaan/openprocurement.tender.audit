import unittest
from openprocurement.api.tests.base import snitch

from openprocurement.tender.audit.tests.base import BaseAuditWebTest

from openprocurement.tender.audit.tests.document_blanks import (
    create_audit_document, put_audit_document, patch_audit_document
)


class AuditDocumentResourceTest(BaseAuditWebTest):
    docservice = False
    initial_auth = ('Basic', ('broker', ''))

    test_create_audit_document = snitch(create_audit_document)
    test_put_audit_document = snitch(put_audit_document)
    test_patch_audit_document = snitch(patch_audit_document)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuditDocumentResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')


