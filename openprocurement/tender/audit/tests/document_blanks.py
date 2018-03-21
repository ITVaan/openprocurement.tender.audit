# -*- coding: utf-8 -*-


def create_audit_document(self):
    response = self.app.get('/audits/{}/documents'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json, {"data": []})

    response = self.app.post('/audits/{}/documents?acc_token={}'.format(
        self.audit_id, self.audit_token), upload_files=[('file', u'укр.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')


