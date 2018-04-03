# -*- coding: utf-8 -*-
from email.header import Header


def not_found(self):
    response = self.app.get('/audits/some_id/documents', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'], 'Not Found')
    self.assertEqual(response.json['errors'][0]['name'], 'audit_id')

    response = self.app.post('/audits/some_id/documents', status=404, upload_files=[
        ('file', 'name.doc', 'content')
    ])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'], 'Not Found')
    self.assertEqual(response.json['errors'][0]['name'], 'audit_id')

    response = self.app.post(
        '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token), status=404,
        upload_files=[('invalid_name', 'name.doc', 'content')]
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'], 'Not Found')
    self.assertEqual(response.json['errors'][0]['name'], 'file')

    response = self.app.put('/audits/some_id/documents/some_id', status=404, upload_files=[
        ('file', 'name.doc', 'content2')
    ])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'], 'Not Found')
    self.assertEqual(response.json['errors'][0]['name'], 'audit_id')

    response = self.app.get('/audits/some_id/documents/some_id', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'], 'Not Found')
    self.assertEqual(response.json['errors'][0]['name'], 'audit_id')

    response = self.app.get('/audits/{}/documents/some_id'.format(
        self.audit_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['description'], 'Not Found')
    self.assertEqual(response.json['errors'][0]['name'], 'document_id')


def create_audit_document(self):
    response = self.app.get('/audits/{}/documents'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json, {'data': []})

    response = self.app.post(
        '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        upload_files=[('file', u'Рішення про початок моніторингу.pdf', 'content')]
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')

    doc_id = response.json['data']['id']

    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual(u'Рішення про початок моніторингу.pdf', response.json['data']['title'])
    self.assertEqual(response.json["data"]["documentOf"], "audit")

    if self.docservice:
        self.assertIn('Signature=', response.json["data"]["url"])
        self.assertIn('KeyID=', response.json["data"]["url"])
        self.assertNotIn('Expires=', response.json["data"]["url"])
        key = response.json["data"]["url"].split('/')[-1].split('?')[0]
        contract = self.db.get(self.audit_id)
        self.assertIn(key, contract['documents'][-1]["url"])
        self.assertIn('Signature=', contract['documents'][-1]["url"])
        self.assertIn('KeyID=', contract['documents'][-1]["url"])
        self.assertNotIn('Expires=', contract['documents'][-1]["url"])
    else:
        key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

    response = self.app.get('/audits/{}/documents'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data'][0]['id'])
    self.assertEqual(u'Рішення про початок моніторингу.pdf', response.json['data'][0]['title'])

    response = self.app.get(
        '/audits/{}/documents/{}?download=some_id'.format(self.audit_id, doc_id), status=404
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'],
        [{u'description': u'Not Found', u'location': u'url', u'name': u'download'}]
    )

    if self.docservice:
        response = self.app.get(
            '/audits/{}/documents/{}?download={}'.format(self.audit_id, doc_id, key)
        )
        self.assertEqual(response.status, '302 Moved Temporarily')
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertNotIn('Expires=', response.location)
    else:
        response = self.app.get(
            '/audits/{}/documents/{}?download={}'.format(self.audit_id, doc_id, key)
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/pdf')
        self.assertEqual(response.content_length, 7)
        self.assertEqual(response.body, 'content')

    response = self.app.get(
        '/audits/{}/documents/{}'.format(self.audit_id, doc_id)
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])
    self.assertEqual(u'Рішення про початок моніторингу.pdf', response.json['data']['title'])

    response = self.app.post(
        '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        upload_files=[(
            'file', u'Рішення про початок моніторингу.pdf'.encode("ascii", "xmlcharrefreplace"), 'content'
        )]
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(u'Рішення про початок моніторингу.pdf', response.json['data']['title'])
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertNotIn('acc_token', response.headers['Location'])

    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {'status': 'terminated'}}, status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'][0],
        "Can't change audit status from 'draft' to 'terminated'"
    )

    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {'status': 'published'}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'published')

    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {'status': 'terminated'}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'terminated')


def create_audit_document_json(self):
    response = self.app.post_json(
        '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {
            'title': u'Рішення про початок моніторингу.pdf',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/pdf',
            'description': u'Рішення про початок моніторингу'
        }}
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    document = response.json["data"]
    # doc_id = document['id']
    self.assertEqual(document['description'], u'Рішення про початок моніторингу')


def put_audit_document(self):
    response = self.app.post(
        '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        upload_files=[('file', 'name.doc', 'content')]
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json['data']['id']

    response = self.app.put(
        '/audits/{}/documents/{}?acc_token={}'.format(self.audit_id, doc_id, self.audit_token),
        'content3',
        content_type='application/msword'
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])


def patch_audit_document(self):
    response = self.app.post(
        '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        upload_files=[('file', str(Header(u'укр.doc', 'utf-8')), 'content')]
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')

    doc_id = response.json["data"]['id']

    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual(u'укр.doc', response.json['data']['title'])
    self.assertEqual(response.json['data']['documentOf'], 'audit')
    self.assertNotIn('documentType', response.json['data'])

    response = self.app.patch_json(
        '/audits/{}/documents/{}?acc_token={}'.format(self.audit_id, doc_id, self.audit_token), {"data": {
            'description': 'document description',
            'documentType': 'startMonitoring'
        }}
    )

    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
