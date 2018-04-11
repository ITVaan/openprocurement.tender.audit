import unittest

from openprocurement.api.tests.base import snitch

from openprocurement.tender.audit.tests.base import BaseAuditWebTest
from openprocurement.tender.audit.tests.answer_blank import (
    create_audit_answer,
    create_audit_answer_invalid,
    change_audit_answerType,
    path_audit_answer,
    not_found,
    create_audit_answer_document,
    put_audit_answer_document,
    patch_audit_answer_document
)


class AuditAnswerResourceTest(BaseAuditWebTest):
    """ audit resource test """
    initial_auth = ('Basic', ('broker', ''))
    test_create_audit_answer_invalid = snitch(create_audit_answer_invalid)
    test_create_audit_answer = snitch(create_audit_answer)
    test_change_audit_answerType = snitch(change_audit_answerType)
    test_path_audit_answer = snitch(path_audit_answer)


class AuditAnswerDocumentResourceTest(BaseAuditWebTest):
    def setUp(self):
        super(AuditAnswerDocumentResourceTest, self).setUp()

        # Create answer
        response = self.app.post_json(
            '/audits/{}/answers'.format(self.audit_id),
            {'data': {"description": "Description", "answerType": "explanationConclusion"}}
        )
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        answer = response.json['data']
        self.answer_id = answer['id']

    test_not_found = snitch(not_found)
    test_create_audit_answer_document = snitch(create_audit_answer_document)
    test_put_audit_answer_document = snitch(put_audit_answer_document)
    test_patch_audit_answer_document = snitch(patch_audit_answer_document)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuditAnswerResourceTest))
    suite.addTest(unittest.makeSuite(AuditAnswerDocumentResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
