import unittest

from copy import deepcopy
from uuid import uuid4

from openprocurement.api.tests.base import snitch

from openprocurement.tender.audit.tests.base import BaseAuditWebTest
# from openprocurement.tender.audit.tests.audit_blanks import create_invalid_audit, create_audit, patch_audit


class AuditResourceTest(BaseAuditWebTest):
    """ audit resource test """
    initial_auth = ('Basic', ('broker', '8aafad1c60719fe21144b71a79e86d9cfb254ace1fb1de2041551c2867111d9908ac59d5cd7c62d34e4a76bcee474719dabb8c5c97135016c0d9a6db179f8206'))

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
        # response = self.app.post_json('/tenders', {"data": test_tender_data})
        # self.assertEqual(response.status, '201 Created')
        # self.assertEqual(response.content_type, 'application/json')
        # tender = response.json['data']
        # tender_id = tender['id']
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
