from uuid import uuid4


def create_audit_answer_invalid(self):
    response = self.app.post('/audits/{}/answers'.format(self.audit_id), 'data', status=415)
    self.assertEqual(response.status, '415 Unsupported Media Type')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['location'], u'header')
    self.assertEqual(response.json['errors'][0]['name'], u'Content-Type')
    self.assertEqual(
        response.json['errors'][0]['description'],
        u'Content-Type header should be one of [\'application/json\']'
    )

    response = self.app.post(
        '/audits/{}/answers'.format(self.audit_id), 'data', content_type='application/json', status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'], [{
            u'description': u'No JSON object could be decoded', u'location': u'body', u'name': u'data'
        }]
    )

    response = self.app.post_json('/audits/{}/answers'.format(self.audit_id), 'data', status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'], [{
            u'description': u'Data not available', u'location': u'body', u'name': u'data'
        }]
    )

    response = self.app.post_json('/audits/{}/answers'.format(self.audit_id), {'not_data': {}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'],
        [{u'description': u'Data not available', u'location': u'body', u'name': u'data'}]
    )

    response = self.app.post_json('/audits/{}/answers'.format(self.audit_id), {'data': []}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'],
        [{u'description': u'Data not available', u'location': u'body', u'name': u'data'}]
    )

    response = self.app.post_json(
        '/audits/some_audit_id/answers',
        {'data': {'description': 'Description', 'answerType': 'explanationConclusion'}}, status=404
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'][0],
        {u'description': u'Not Found', u'location': u'url', u'name': u'audit_id'}
    )

    response = self.app.post_json(
        '/audits/{}/answers'.format(self.audit_id),
        {'data': {'description': 'Description', 'answerType': 'some_answer_type'}}, status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'][0],
        {u'description': [
            u"Value must be one of ['startMonitoringDecision', 'requestExplanation', "
            u"'responseConclusion', 'explanationConclusion', 'stopMonitoringDecision']."
        ], u'location': u'body', u'name': u'answerType'}
    )


def create_audit_answer(self):
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
        response.json['errors'][0],
        {u'description': [
            u'An answer to a request for a explanation conclusion may only be given once'
        ], u'location': u'body', u'name': u'answers'}
    )


def change_audit_answerType(self):
    response = self.app.post_json(
        '/audits/{}/answers'.format(self.audit_id),
        {'data': {"description": "Description", "answerType": "explanationConclusion"}}
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')

    answer = response.json['data']
    self.assertEqual(answer['description'], 'Description')

    response = self.app.get('/audits/{}/answers'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    answers = response.json['data']

    self.assertEqual(answers[0]['answerType'], 'explanationConclusion')

    response = self.app.patch_json(
        '/audits/{}/answers/some_id?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {'answerType': 'some_answerType'}}, status=404
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0], {u'description': u'Not Found', u'location': u'url', u'name': u'answer_id'}
    )

    response = self.app.patch_json(
        '/audits/{}/answers/{}?acc_token={}'.format(self.audit_id, answer['id'], self.audit_token),
        {'data': {'answerType': 'some_answerType'}}, status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'][0],
        {u'description': [
            u"Value must be one of ['startMonitoringDecision', 'requestExplanation', "
            u"'responseConclusion', 'explanationConclusion', 'stopMonitoringDecision']."
        ], u'location': u'body', u'name': u'answerType'}
    )

    response = self.app.patch_json(
        '/audits/{}/answers/{}?acc_token={}'.format(self.audit_id, answer['id'], self.audit_token),
        {'data': {'answerType': 'startMonitoringDecision'}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertNotEqual(response.json['data']['answerType'], 'startMonitoringDecision')
    self.assertEqual(response.json['data']['answerType'], 'explanationConclusion')


def path_audit_answer(self):
    document_id = uuid4().hex

    response = self.app.post_json(
        '/audits/{}/answers'.format(self.audit_id),
        {'data': {
            "description": "Description", "answerType": "explanationConclusion", 'document_id': document_id
        }}
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    answer = response.json['data']
    self.assertEqual(answer['description'], 'Description')
    self.assertIn(answer['document_id'], document_id)

    response = self.app.get('/audits/{}/answers/{}'.format(self.audit_id, answer['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['description'], 'Description')
    self.assertIn('document_id', response.json['data'])
    self.assertEqual(response.json['data']['document_id'], document_id)

    response = self.app.patch_json(
        '/audits/{}/answers/{}?acc_token={}'.format(self.audit_id, answer['id'], self.audit_token),
        {'data': {'description': 'Description2'}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['description'], 'Description2')

    response = self.app.patch_json(
        '/audits/{}/answers/{}?acc_token={}'.format(self.audit_id, answer['id'], self.audit_token),
        {'data': {'document_id': uuid4().hex}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['document_id'], document_id)


def not_found(self):
    response = self.app.post(
        '/audits/some_id/answers/some_id/documents', status=404, upload_files=[('file', 'name.doc', 'content')]
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'], [{u'description': u'Not Found', u'location': u'url', u'name': u'audit_id'}]
    )

    response = self.app.post(
        '/audits/{}/answers/some_id/documents'.format(self.audit_id),
        status=404,
        upload_files=[('file', 'name.doc', 'content')]
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'], [{u'description': u'Not Found', u'location': u'url', u'name': u'answer_id'}]
    )

    response = self.app.post(
        '/audits/{}/answers/{}/documents?acc_token={}'.format(self.audit_id, self.answer_id, self.audit_token),
        status=404,
        upload_files=[('invalid_value', 'name.doc', 'content')]
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'], [{u'description': u'Not Found', u'location': u'body', u'name': u'file'}]
    )

    response = self.app.get('/audits/some_id/answers/some_id/documents', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'], [{u'description': u'Not Found', u'location': u'url', u'name': u'audit_id'}]
    )

    response = self.app.get('/audits/{}/answers/some_id/documents'.format(self.audit_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'], [{u'description': u'Not Found', u'location': u'url', u'name': u'answer_id'}]
    )

    response = self.app.get('/audits/some_id/answers/some_id/documents/some_id', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'], [{u'description': u'Not Found', u'location': u'url', u'name': u'audit_id'}]
    )

    response = self.app.get('/audits/{}/answers/some_id/documents/some_id'.format(self.audit_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'][0], {u'description': u'Not Found', u'location': u'url', u'name': u'answer_id'}
    )

    response = self.app.get(
        '/audits/{}/answers/{}/documents/some_id'.format(self.audit_id, self.answer_id), status=404
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'][0], {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
    )

    response = self.app.put(
        '/audits/some_id/answers/some_id/documents/some_id',
        upload_files=[('file', 'name.doc', 'content2')], status=404
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'][0], {u'description': u'Not Found', u'location': u'url', u'name': u'audit_id'}
    )

    response = self.app.put(
        '/audits/{}/answers/some_id/documents/some_id'.format(self.audit_id),
        upload_files=[('file', 'name.doc', 'content2')], status=404
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'][0], {u'description': u'Not Found', u'location': u'url', u'name': u'answer_id'}
    )

    response = self.app.put(
        '/audits/{}/answers/{}/documents/some_id'.format(self.audit_id, self.answer_id),
        upload_files=[('file', 'name.doc', 'content2')], status=404
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'][0], {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
    )

    self.app.authorization = ('Basic', ('invalid', ''))
    response = self.app.put(
        '/audits/{}/answers/{}/documents/some_id'.format(self.audit_id, self.answer_id),
        upload_files=[('file', 'name.doc', 'content2')], status=404
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
    ])


def create_audit_answer_document(self):
    response = self.app.post(
        '/audits/{}/answers/{}/documents?acc_token={}'.format(self.audit_id, self.answer_id, self.audit_token),
        upload_files=[('file', 'name.doc', 'content')]
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json['data']['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual('name.doc', response.json['data']['title'])
    key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

    response = self.app.get(
        '/audits/{}/answers/{}/documents?acc_token={}'.format(self.audit_id, self.answer_id, self.audit_token)
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data'][0]['id'])
    self.assertEqual('name.doc', response.json['data'][0]['title'])

    response = self.app.get(
        '/audits/{}/answers/{}/documents?all=true&acc_token={}'.format(
            self.audit_id, self.answer_id, self.audit_token
        )
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data'][0]['id'])
    self.assertEqual('name.doc', response.json['data'][0]['title'])

    response = self.app.get(
        '/audits/{}/answers/{}/documents/{}?download=some_id&acc_token={}'.format(
            self.audit_id, self.answer_id, doc_id, self.audit_token
        ), status=404
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'][0], {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
    )

    if self.docservice:
        response = self.app.get(
            '/audits/{}/answers/{}/documents/{}?download={}&acc_token={}'.format(
                self.audit_id, self.answer_id, doc_id, key, self.audit_token
            )
        )
        self.assertEqual(response.status, '302 Moved Temporarily')
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertIn('Expires=', response.location)
    else:
        response = self.app.get(
            '/audits/{}/answers/{}/documents/{}?download={}&acc_token={}'.format(
                self.audit_id, self.answer_id, doc_id, key, self.audit_token
            )
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 7)
        self.assertEqual(response.body, 'content')

    response = self.app.get(
        '/audits/{}/answers/{}/documents/{}?acc_token={}'.format(
            self.audit_id, self.answer_id, doc_id, self.audit_token
        )
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])
    self.assertEqual('name.doc', response.json['data']['title'])

    response = self.app.get('/audits/{}/answers/{}/documents/{}'.format(self.audit_id, self.answer_id, doc_id))
    self.assertEqual(response.status, '200 OK')

    if self.docservice:
        self.assertIn('http://localhost/get/', response.json['data']['url'])
        self.assertIn('Signature=', response.json['data']['url'])
        self.assertIn('KeyID=', response.json['data']['url'])
        self.assertNotIn('Expires=', response.json['data']['url'])
    else:
        self.assertIn('download=', response.json['data']['url'])

    response = self.app.get(
        '/audits/{}/answers/{}/documents/{}?download={}&acc_token={}'.format(
            self.audit_id, self.answer_id, doc_id, key, self.audit_token
        )
    )

    if self.docservice:
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertIn('Expires=', response.location)
    else:
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 7)
        self.assertEqual(response.body, 'content')


def put_audit_answer_document(self):
    response = self.app.post(
        '/audits/{}/answers/{}/documents?acc_token={}'.format(self.audit_id, self.answer_id, self.audit_token),
        upload_files=[('file', 'name.doc', 'content')]
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json['data']['id']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.put(
        '/audits/{}/answers/{}/documents/{}?acc_token={}'.format(self.audit_id, self.answer_id, doc_id, self.audit_token),
        status=404,
        upload_files=[('invalid_name', 'name.doc', 'content')]
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'][0], {u'description': u'Not Found', u'location': u'body', u'name': u'file'}
    )

    response = self.app.put(
        '/audits/{}/answers/{}/documents/{}?acc_token={}'.format(
            self.audit_id, self.answer_id, doc_id, self.audit_token
        ), upload_files=[('file', 'name.doc', 'content2')]
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])
    key = response.json['data']['url'].split('?')[-1]

    response = self.app.get(
        '/audits/{}/answers/{}/documents/{}?{}&acc_token={}'.format(
            self.audit_id, self.answer_id, doc_id, key, self.audit_token
        )
    )
    if self.docservice:
        self.assertEqual(response.status, '302 Moved Temporarily')
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertIn('Expires=', response.location)
    else:
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content2')

    response = self.app.get(
        '/audits/{}/answers/{}/documents/{}?acc_token={}'.format(
            self.audit_id, self.answer_id, doc_id, self.audit_token
        )
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])
    self.assertEqual('name.doc', response.json['data']['title'])

    response = self.app.put(
        '/audits/{}/answers/{}/documents/{}?acc_token={}'.format(
            self.audit_id, self.answer_id, doc_id, self.audit_token
        ), 'content3', content_type='application/msword'
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])
    key = response.json['data']['url'].split('?')[-1]

    response = self.app.get(
        '/audits/{}/answers/{}/documents/{}?{}&acc_token={}'.format(
            self.audit_id, self.answer_id, doc_id, key, self.audit_token
        )
    )

    if self.docservice:
        self.assertEqual(response.status, '302 Moved Temporarily')
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertIn('Expires=', response.location)
    else:
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content3')


def patch_audit_answer_document(self):
    response = self.app.post(
        '/audits/{}/answers/{}/documents?acc_token={}'.format(
            self.audit_id, self.answer_id, self.audit_token
        ), upload_files=[('file', 'name.doc', 'content')]
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json['data']['id']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.patch_json(
        '/audits/{}/answers/{}/documents/{}?acc_token={}'.format(
            self.audit_id, self.answer_id, doc_id, self.audit_token
        ), {'data': {'description': 'document description'}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])

    response = self.app.get(
        '/audits/{}/answers/{}/documents/{}?acc_token={}'.format(
            self.audit_id, self.answer_id, doc_id, self.audit_token
        )
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])
    self.assertEqual('document description', response.json['data']['description'])
