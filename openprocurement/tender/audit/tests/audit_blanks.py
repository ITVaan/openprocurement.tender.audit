

def patch_audit(self):
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
    self.assertEqual(response.json['errors'][0]['description'][0], "Can't update audit in 'draft' status")

    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token), {'data': {'status': 'published'}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'published')


