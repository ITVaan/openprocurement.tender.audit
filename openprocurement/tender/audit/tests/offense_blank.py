

def create_audit_offense(self):
    orig_auth = self.app.authorization
    self.app.authorization = ('Basic', ('broker', ''))

    response = self.app.post_json(
        '/audits/{}/offenses'.format(self.audit_id),
        {'data': {"description": "Description offense", "typical_offenses": [
            'corruptionDescription', 'corruptionProcurementMethodType'
        ]}}
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')

    offense = response.json['data']
    self.assertEqual(offense['description'], 'Description offense')
    self.assertEqual(len(offense['typical_offenses']), 2)
    self.assertEqual(offense['status'], 'not_fixed')

    response = self.app.patch_json(
        '/audits/{}/offenses/{}?acc_token={}'.format(self.audit_id, offense['id'], self.audit_token),
        {'data': {'description': 'Description offense 2', 'status': 'fixed'}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['description'], 'Description offense 2')
    self.assertEqual(response.json['data']['status'], 'fixed')

    self.app.authorization = orig_auth

