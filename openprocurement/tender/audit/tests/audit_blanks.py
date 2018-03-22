

def patch_audit(self):
    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token), {'data': {'title': 'New Title'}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['title'], 'New Title')


