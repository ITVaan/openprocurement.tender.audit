import unittest

from copy import deepcopy
from uuid import uuid4

from openprocurement.api.tests.base import snitch

from openprocurement.tender.audit.tests.base import BaseAuditWebTest
# from openprocurement.tender.audit.tests.audit_blanks import create_invalid_audit, create_audit, patch_audit


class AuditResourceTest(BaseAuditWebTest):
    """ audit resource test """
    initial_auth = ('Basic', ('broker', '8aafad1c60719fe21144b71a79e86d9cfb254ace1fb1de2041551c2867111d9908ac59d5cd7c62d34e4a76bcee474719dabb8c5c97135016c0d9a6db179f8206'))

    def test_patch_audit(self):
        orig_auth = self.app.authorization
        self.app.authorization = ('Basic', ('broker', 'broker'))
        response = self.app.patch_json(
            '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token),
            {'data': {'title': 'New Title'}},
            # headers={"Authorization": "Basic YnJva2VyOmJyb2tlcg=="}
            # headers={"Authorization": "Basic YnJva2VyOmJyb2tlcg=="}
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['title'], 'New Title')
        self.app.authorization = orig_auth

    def test_patch_audit_2(self):
        response = self.app.get('/audits/{}'.format(self.audit_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['title'], 'Test title')
    # test_create_invalid_audit = snitch(create_invalid_audit)
    # test_create_audit = snitch(create_audit)
    # test_patch_audit = snitch(patch_audit)

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
        self.assertEqual(response.json['errors'][0]['description'][0], "Can't update audit in 'draft' status")

        response = self.app.patch_json(
            '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token), {'data': {'status': 'published'}}
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'published')


    # test_patch_audit = snitch(patch_audit)

#
# def suite():
#     suite = unittest.TestSuite()
#     suite.addTest(unittest.makeSuite(AuditResourceTest))
#     return suite
#
#
# if __name__ == '__main__':
#     unittest.main(defaultTest='suite')


