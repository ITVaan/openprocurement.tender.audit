# # -*- coding: utf-8 -*-
# from email.header import Header
#
#
# def create_audit_document(self):
#     response = self.app.get('/audits/{}/documents'.format(self.audit_id))
#     self.assertEqual(response.status, '200 OK')
#     self.assertEqual(response.content_type, 'application/json')
#     self.assertEqual(response.json, {'data': []})
#
#     response = self.app.post('/audits/{}/documents?acc_token={}'.format(
#         self.audit_id, self.audit_token), upload_files=[('file', u'укр.doc', 'content')])
#     self.assertEqual(response.status, '201 Created')
#     self.assertEqual(response.content_type, 'application/json')
#
#
# def put_audit_document(self):
#     response = self.app.post(
#         '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
#         upload_files=[('file', 'name.doc', 'content')]
#     )
#     self.assertEqual(response.status, '201 Created')
#     self.assertEqual(response.content_type, 'application/json')
#     doc_id = response.json['data']['id']
#
#     response = self.app.put(
#         '/audits/{}/documents/{}?acc_token={}'.format(self.audit_id, doc_id, self.audit_token),
#         'content3',
#         content_type='application/msword'
#     )
#     self.assertEqual(response.status, '200 OK')
#     self.assertEqual(response.content_type, 'application/json')
#     self.assertEqual(doc_id, response.json["data"]["id"])
#
#
# def patch_audit_document(self):
#     response = self.app.post(
#         '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
#         upload_files=[('file', str(Header(u'укр.doc', 'utf-8')), 'content')]
#     )
#     self.assertEqual(response.status, '201 Created')
#     self.assertEqual(response.content_type, 'application/json')
#
#     doc_id = response.json["data"]['id']
#
#     self.assertIn(doc_id, response.headers['Location'])
#     self.assertEqual(u'укр.doc', response.json['data']['title'])
#     self.assertEqual(response.json['data']['documentOf'], 'audit')
#     self.assertNotIn('documentType', response.json['data'])
#
#     response = self.app.patch_json(
#         '/audits/{}/documents/{}?acc_token={}'.format(self.audit_id, doc_id, self.audit_token), {"data": {
#             'description': 'document description',
#             'documentType': 'startMonitoring'
#         }}
#     )
#
#     self.assertEqual(response.status, '200 OK')
#     self.assertEqual(response.content_type, 'application/json')
