

def create_audit_answer(self):
    orig_auth = self.app.authorization
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.post_json(
        '/audits/{}/answers'.format(self.audit_id),
        {'data': {"description": "Description", "answerType": "explanationConclusion"}}
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')

    answer = response.json['data']
    self.assertEqual(answer['description'], 'Description')

    # create similar answer
    response = self.app.post_json(
        '/audits/{}/answers'.format(self.audit_id),
        {'data': {"description": "Description", "answerType": "explanationConclusion"}}, status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')

    self.assertEqual(
        response.json['errors'][0]['description'][0],
        'An answer to a request for a explanation conclusion may only be given once'
    )

    self.app.authorization = orig_auth

    # Path answer
    orig_auth = self.app.authorization
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.patch_json(
        '/audits/{}/answers/{}?acc_token={}'.format(self.audit_id, answer['id'], self.audit_token),
        {'data': {'description': 'Description2'}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['description'], 'Description2')

    self.app.authorization = orig_auth



