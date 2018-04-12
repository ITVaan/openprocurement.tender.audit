import unittest

from copy import deepcopy

from copy import deepcopy
from uuid import uuid4

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

    def test_create_invalid_audit(self):
        data = deepcopy(self.initial_data)
        response = self.app.post_json('/audits', {'data': data}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]['description'], 'Forbidden')

    def test_create_audit_404(self):
        data = deepcopy(self.initial_data)
        orig_auth = self.app.authorization
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/audits', {'data': data}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]['description'], 'Not Found')

    def test_create_audit_422(self):
        data = deepcopy(self.initial_data)
        orig_auth = self.app.authorization
        self.app.authorization = ('Basic', ('broker', ''))
        tender_id = uuid4().hex

        del data['grounds']

        data.update({'tender_id': tender_id})
        response = self.app.post_json('/audits', {'data': data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]['description'][0], 'This field is required.')

        data.update({'grounds': 'some_ground'})
        response = self.app.post_json('/audits', {'data': data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]['description'][0],
            ["Value must be one of ['indicator', 'authorities', 'media', 'fiscal', 'public']."]
        )

        data.update({'grounds': 'indicator', 'procurement_stage': 'some_stage'})
        response = self.app.post_json('/audits', {'data': data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]['description'][0],
            ["Value must be one of ['planing', 'awarding', 'contracting']."]
        )

        data.update({'procurement_stage': 'planing', 'status': 'some_status'})
        response = self.app.post_json('/audits', {'data': data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]['description'][0],
            "Value must be one of ['terminated', 'draft', 'published']."
        )

        self.app.authorization = orig_auth

    def test_patch_audit(self):
        orig_auth = self.app.authorization
        self.app.authorization = ('Basic', ('broker', 'broker'))
        response = self.app.patch_json(
            '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token),
            {'data': {'title': 'New Title'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['title'], 'New Title')
        self.app.authorization = orig_auth

    def test_patch_audit_2(self):
        response = self.app.get('/audits/{}'.format(self.audit_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['title'], 'Test title')

        audit = response.json['data']

        response = self.app.patch_json(
            '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token), {'data': {'title': 'New Title'}}
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['title'], 'New Title')

        self.assertEqual(audit['status'], 'draft')

        response = self.app.patch_json(
            '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token), {'data': {'status': 'terminated'}},
            status=422
        )
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.json['errors'][0]['description'][0], "Can't change audit status from 'draft' to 'terminated'")

        response = self.app.patch_json(
            '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token), {'data': {'status': 'published'}}
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'published')


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


