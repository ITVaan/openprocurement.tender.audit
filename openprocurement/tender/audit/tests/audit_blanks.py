from copy import deepcopy

from openprocurement.tender.audit.tests.base import test_tender_data


def create_audit_invalid(self):
    response = self.app.post('/audits', 'data', status=415)
    self.assertEqual(response.status, '415 Unsupported Media Type')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['location'], u'header')
    self.assertEqual(response.json['errors'][0]['name'], u'Content-Type')
    self.assertEqual(
        response.json['errors'][0]['description'],
        u'Content-Type header should be one of [\'application/json\']'
    )

    response = self.app.post('/audits', 'data', content_type='application/json', status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'], [{
            u'description': u'No JSON object could be decoded', u'location': u'body', u'name': u'data'
        }]
    )

    response = self.app.post_json('/audits', 'data', status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'], [{
            u'description': u'Data not available', u'location': u'body', u'name': u'data'
        }]
    )

    response = self.app.post_json('/audits', {'not_data': {}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'],
        [{u'description': u'Data not available', u'location': u'body', u'name': u'data'}]
    )

    response = self.app.post_json('/audits', {'data': []}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'],
        [{u'description': u'Data not available', u'location': u'body', u'name': u'data'}]
    )

    data = deepcopy(self.initial_data)
    response = self.app.post_json('/audits', {'data': data}, status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description'], 'Not Found')

    response = self.app.post_json('/tenders', {'data': test_tender_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    tender = response.json['data']
    tender_id = tender['id']

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


def create_audit(self):
    data = deepcopy(self.initial_data)
    data.update({'tender_id': self.tender_id})

    response = self.app.post_json('/audits', {'data': data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')

    audit = response.json['data']
    self.assertEqual(audit['title'], 'Test title')
    self.assertEqual(audit['procurement_stage'], [u'planing'])
    self.assertEqual(audit['grounds'], [u'indicator'])
    self.assertEqual(audit['status'], 'draft')

    response = self.app.get('/audits/{}'.format(audit['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(set(response.json['data']), set(audit))
    self.assertEqual(response.json['data'], audit)


def audit_status_change(self):
    orig_auth = self.app.authorization
    self.app.authorization = ('Basic', ('broker', ''))

    response = self.app.get('/audits/{}'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], 'draft')

    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, 'some_token'),
        {'data': {'status': 'published'}}, status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')

    self.app.authorization = orig_auth

    response = self.app.patch_json(
        '/audits/{}'.format(self.audit_id),
        {'data': {'status': 'some_status'}}, status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'][0],
        {
            u'description': [u"Value must be one of ['terminated', 'draft', 'published']."],
            u'location': u'body',
            u'name': u'status'
        }
    )

    response = self.app.patch_json(
        '/audits/{}'.format(self.audit_id), {'data': {'status': 'terminated'}},
        status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'][0], "Can't change audit status from 'draft' to 'terminated'"
    )

    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token), {'data': {'status': 'published'}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], 'published')

    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token), {'data': {'status': 'draft'}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], 'published')

    response = self.app.get('/audits/{}'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    audit = response.json['data']

    self.assertIn('date_published', audit)
    self.assertNotIn('documents', audit)


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
    self.assertNotIn('date_published', audit)

    response = self.app.get('/audits/{}'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['title'], 'New Title')

    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {'grounds': 'some_ground'}}, status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'][0],
        {
            "location": "body",
            "name": "grounds",
            "description": [[
                "Value must be one of ['indicator', 'authorities', 'media', 'fiscal', 'public']."
            ]]
        }
    )

    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token), {'data': {'grounds': ['media']}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    response = self.app.get('/audits/{}'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    audit = response.json['data']

    self.assertEqual(audit['grounds'], ['indicator'])

    response = self.app.get('/audits/{}/documents'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json, {'data': []})

    response = self.app.post(
        '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        upload_files=[('file', 'document.doc', 'content')], status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')

    orig_auth = self.app.authorization
    self.app.authorization = ('Basic', ('broker', ''))

    response = self.app.post(
        '/audits/{}/documents'.format(self.audit_id),
        upload_files=[('file', 'document.doc', 'content')], status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')

    response = self.app.post(
        '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        upload_files=[('file', 'document.doc', 'content')]
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json['data']['id']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.get('/audits/{}/documents'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(len(response.json['data']), 1)
    self.assertEqual(response.json['data'][0]['title'], 'document.doc')

    response = self.app.post(
        '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        upload_files=[('file', 'document1.doc', 'content')]
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json['data']['id']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.get('/audits/{}/documents'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(len(response.json['data']), 2)
    self.assertEqual(response.json['data'][1]['title'], 'document1.doc')

    response = self.app.get('/audits/{}/answers'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json, {'data': []})

    response = self.app.post_json(
        '/audits/{}/answers'.format(self.audit_id),
        {'data': {'document_id': doc_id, 'description': 'Description', 'answerType': 'some_answer_type'}},
        status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'],
        [{
            "location": "body",
            "name": "answerType",
            "description": [
                "Value must be one of ['startMonitoringDecision', 'requestExplanation', "
                "'responseConclusion', 'explanationConclusion', 'stopMonitoringDecision']."
            ]
        }]
    )

    response = self.app.post_json(
        '/audits/{}/answers'.format(self.audit_id),
        {'data': {
            'document_id': doc_id, 'description': 'Description', 'answerType': 'startMonitoringDecision'
        }}
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')

    response = self.app.get('/audits/{}/answers'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    answers = response.json['data']

    self.assertEqual(len(answers), 1)
    self.assertEqual(answers[0]['description'], 'Description')
    self.assertEqual(answers[0]['answerType'], 'startMonitoringDecision')

    self.app.authorization = orig_auth


def create_audit_with_documents(self):
    data = deepcopy(self.initial_data)

    orig_auth = self.app.authorization
    self.app.authorization = ('Basic', ('broker', ''))

    response = self.app.post_json('/tenders', {"data": test_tender_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    tender = response.json['data']
    tender_id = tender['id']

    self.app.authorization = orig_auth

    data.update({'tender_id': tender_id})

    response = self.app.post_json('/audits', {"data": data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    audit = response.json['data']
    self.assertEqual(audit['status'], 'draft')

    for index, doc in enumerate(self.documents):
        self.assertEqual(response.json['data']['documents'][index]['id'], self.documents[index]['id'])
        self.assertEqual(response.json['data']['documents'][index]['datePublished'], self.documents[index]['datePublished'])
        self.assertEqual(response.json['data']['documents'][index]['dateModified'], self.documents[index]['dateModified'])

    self.assertIn('Signature=', response.json['data']['documents'][-1]['url'])
    self.assertIn('KeyID=', response.json['data']['documents'][-1]['url'])
    self.assertNotIn('Expires=', response.json['data']['documents'][-1]['url'])

    audit = self.db.get(audit['id'])
    self.assertIn('Prefix=ce536c5f46d543ec81ffa86ce4c77c8b%2F9c8b66120d4c415cb334bbad33f94ba9', audit['documents'][-1]['url'])
    self.assertIn('/da839a4c3d7a41d2852d17f90aa14f47?', audit['documents'][-1]['url'])
    self.assertIn('Signature=', audit['documents'][-1]['url'])
    self.assertIn('KeyID=', audit['documents'][-1]['url'])
    self.assertNotIn('Expires=', audit['documents'][-1]['url'])




