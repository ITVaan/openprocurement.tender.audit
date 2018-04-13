# -*- coding: utf-8 -*-
from six import BytesIO
from urllib import quote

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
        audit = self.db.get(self.audit_id)
        self.assertIn(key, audit['documents'][-1]["url"])
        self.assertIn('Signature=', audit['documents'][-1]["url"])
        self.assertIn('KeyID=', audit['documents'][-1]["url"])
        self.assertNotIn('Expires=', audit['documents'][-1]["url"])
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

    response = self.app.post(
        '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        upload_files=[(
            'file', u'Рішення про початок моніторингу.pdf'.encode("ascii", "xmlcharrefreplace"), 'contentX'
        )], status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(
        response.json['errors'][0]['description'],
        u'Can\'t add document in current (terminated) audit status'
    )


def put_audit_document(self):
    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token), {'data': {'status': 'published'}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    body = u'--BOUNDARY\nContent-Disposition: form-data; name="file"; filename={}\nContent-Type: application/msword\n\ncontent\n'.format(u'\uff07')
    environ = self.app._make_environ()
    environ['CONTENT_TYPE'] = 'multipart/form-data; boundary=BOUNDARY'
    environ['REQUEST_METHOD'] = 'POST'
    req = self.app.RequestClass.blank(
        self.app._remove_fragment('/audits/{}/documents'.format(self.audit_id)), environ
    )
    req.environ['wsgi.input'] = BytesIO(body.encode('utf8'))
    req.content_length = len(body)
    response = self.app.do_request(req, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], 'could not decode params')

    body = u'''--BOUNDARY\nContent-Disposition: form-data; name="file"; filename*=utf-8''{}\nContent-Type: application/msword\n\ncontent\n'''.format(
        quote('Рішення про початок моніторингу.doc')
    )
    environ = self.app._make_environ()
    environ['CONTENT_TYPE'] = 'multipart/form-data; boundary=BOUNDARY'
    environ['REQUEST_METHOD'] = 'POST'
    req = self.app.RequestClass.blank(
        self.app._remove_fragment('/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token)),
        environ
    )
    req.environ['wsgi.input'] = BytesIO(body.encode(req.charset or 'utf8'))
    req.content_length = len(body)
    response = self.app.do_request(req)
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(u'Рішення про початок моніторингу.doc', response.json['data']['title'])
    doc_id = response.json['data']['id']
    date_modified = response.json["data"]['dateModified']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.put(
        '/audits/{}/documents/{}?acc_token={}'.format(self.audit_id, doc_id, self.audit_token),
        upload_files=[('file', 'name  name.doc', 'content2')]
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])

    if self.docservice:
        self.assertIn('Signature=', response.json['data']['url'])
        self.assertIn('KeyID=', response.json['data']['url'])
        self.assertNotIn('Expires=', response.json['data']['url'])
        key = response.json['data']['url'].split('/')[-1].split('?')[0]
        audit = self.db.get(self.audit_id)
        self.assertIn(key, audit['documents'][-1]["url"])
        self.assertIn('Signature=', audit['documents'][-1]['url'])
        self.assertIn('KeyID=', audit['documents'][-1]['url'])
        self.assertNotIn('Expires=', audit['documents'][-1]['url'])
    else:
        key = response.json['data']['url'].split('?')[-1].split('=')[-1]

    if self.docservice:
        response = self.app.get('/audits/{}/documents/{}?download={}'.format(self.audit_id, doc_id, key))
        self.assertEqual(response.status, '302 Moved Temporarily')
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertNotIn('Expires=', response.location)
    else:
        response = self.app.get('/audits/{}/documents/{}?download={}'.format(self.audit_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content2')

    response = self.app.get('/audits/{}/documents/{}'.format(self.audit_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])
    self.assertEqual('name name.doc', response.json['data']['title'])
    date_modified2 = response.json['data']['dateModified']
    self.assertTrue(date_modified < date_modified2)
    self.assertEqual(date_modified, response.json['data']['previousVersions'][0]['dateModified'])

    response = self.app.get('/audits/{}/documents?all=true'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(date_modified, response.json['data'][0]['dateModified'])
    self.assertEqual(date_modified2, response.json['data'][1]['dateModified'])

    response = self.app.post(
        '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        upload_files=[('file', 'name.doc', 'content')]
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json['data']['id']
    date_modified = response.json['data']['dateModified']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.get('/audits/{}/documents'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(date_modified2, response.json['data'][0]['dateModified'])
    self.assertEqual(date_modified, response.json['data'][1]['dateModified'])

    response = self.app.put(
        '/audits/{}/documents/{}?acc_token={}'.format(self.audit_id, doc_id, self.audit_token), status=404,
        upload_files=[('invalid_name', 'name.doc', 'content')]
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'][0]['name'], 'file')
    self.assertEqual(response.json['errors'][0]['description'], 'Not Found')

    response = self.app.put(
        '/audits/{}/documents/{}?acc_token={}'.format(self.audit_id, doc_id, self.audit_token), 'content3',
        content_type='application/msword'
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])

    if self.docservice:
        self.assertIn('Signature=', response.json['data']['url'])
        self.assertIn('KeyID=', response.json['data']['url'])
        self.assertNotIn('Expires=', response.json['data']['url'])
        key = response.json['data']['url'].split('/')[-1].split('?')[0]
        audit = self.db.get(self.audit_id)
        self.assertIn(key, audit['documents'][-1]["url"])
        self.assertIn('Signature=', audit['documents'][-1]["url"])
        self.assertIn('KeyID=', audit['documents'][-1]["url"])
        self.assertNotIn('Expires=', audit['documents'][-1]["url"])
    else:
        key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

    if self.docservice:
        response = self.app.get('/audits/{}/documents/{}?download={}'.format(self.audit_id, doc_id, key))
        self.assertEqual(response.status, '302 Moved Temporarily')
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertNotIn('Expires=', response.location)
    else:
        response = self.app.get('/audits/{}/documents/{}?download={}'.format(self.audit_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content3')

    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {'status': 'terminated'}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'terminated')

    response = self.app.put(
        '/audits/{}/documents/{}?acc_token={}'.format(self.audit_id, doc_id, self.audit_token), 'contentX',
        content_type='application/msword', status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]['name'], 'data')
    self.assertEqual(
        response.json['errors'][0]['description'],
        u'Can\'t update document in current (terminated) audit status'
    )


def patch_audit_document(self):
    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {'status': 'published'}}
    )
    self.assertEqual(response.status, '200 OK')

    response = self.app.post(
        '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        upload_files=[('file', str(Header(u'Рішення про початок моніторингу.doc', 'utf-8')), 'content')]
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual(u'Рішення про початок моніторингу.doc', response.json['data']['title'])
    self.assertEqual(response.json['data']['documentOf'], 'audit')
    self.assertNotIn('documentType', response.json['data'])

    response = self.app.patch_json(
        '/audits/{}/documents/{}?acc_token={}'.format(self.audit_id, doc_id, self.audit_token),
        {'data': {'description': 'document description',
        'documentType': 'startMonitoring'
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])
    self.assertIn('documentType', response.json['data'])
    self.assertEqual(response.json['data']['documentType'], 'startMonitoring')

    response = self.app.patch_json(
        '/audits/{}/documents/{}?acc_token={}'.format(self.audit_id, doc_id, self.audit_token),
        {'data': {'documentType': None}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])
    self.assertNotIn('documentType', response.json['data'])

    response = self.app.get('/audits/{}/documents/{}'.format(self.audit_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])
    self.assertEqual('document description', response.json['data']['description'])

    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {'status': 'terminated'}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'terminated')

    response = self.app.patch_json(
        '/audits/{}/documents/{}?acc_token={}'.format(self.audit_id, doc_id, self.audit_token),
        {'data': {'description': 'document description X'}}, status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]['name'], 'data')
    self.assertEqual(
        response.json['errors'][0]['description'],
        u'Can\'t update document in current (terminated) audit status'
    )


def create_audit_document_json_invalid(self):
    response = self.app.post_json('/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {
            'title': u'Рішення про початок моніторингу.doc',
            'url': self.generate_docservice_url(),
            'format': 'application/msword',
        }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description'], 'This field is required.')

    response = self.app.post_json('/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {
            'title': u'Рішення про початок моніторингу.doc',
            'url': 'http://invalid.docservice.url/get/uuid',
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description'], 'Can add document only from document service.')

    response = self.app.post_json('/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {
            'title': u'Рішення про початок моніторингу.doc',
            'url': '/'.join(self.generate_docservice_url().split('/')[:4]),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description'], 'Can add document only from document service.')

    response = self.app.post_json('/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {
            'title': u'Рішення про початок моніторингу.doc',
            'url': self.generate_docservice_url().split('?')[0],
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description'], 'Can add document only from document service.')

    response = self.app.post_json('/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {
            'title': u'Рішення про початок моніторингу.doc',
            'url': self.generate_docservice_url().replace(self.app.app.registry.keyring.keys()[-1], '0' * 8),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description'], 'Document url expired.')

    response = self.app.post_json('/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {
            'title': u'Рішення про початок моніторингу.doc',
            'url': self.generate_docservice_url().replace('Signature=', 'Signature=ABC'),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description'], 'Document url signature invalid.')

    response = self.app.post_json('/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {
            'title': u'Рішення про початок моніторингу.doc',
            'url': self.generate_docservice_url().replace('Signature=', 'Signature=bw%3D%3D'),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description'], 'Document url invalid.')


def create_audit_document_json(self):
    response = self.app.post_json(
        '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {
            'title': u'Рішення про початок моніторингу.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword'
        }}
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json['data']['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual(u'Рішення про початок моніторингу.doc', response.json['data']['title'])
    self.assertIn('Signature=', response.json['data']['url'])
    self.assertIn('KeyID=', response.json['data']['url'])
    self.assertNotIn('Expires=', response.json['data']['url'])
    key = response.json['data']['url'].split('/')[-1].split('?')[0]
    audit = self.db.get(self.audit_id)
    self.assertIn(key, audit['documents'][-1]['url'])
    self.assertIn('Signature=', audit['documents'][-1]['url'])
    self.assertIn('KeyID=', audit['documents'][-1]['url'])
    self.assertNotIn('Expires=', audit['documents'][-1]['url'])

    response = self.app.get('/audits/{}/documents'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"][0]["id"])
    self.assertEqual(u'Рішення про початок моніторингу.doc', response.json['data'][0]['title'])

    response = self.app.get(
        '/audits/{}/documents/{}?download=some_id'.format(self.audit_id, doc_id), status=404
    )
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
    ])

    response = self.app.get('/audits/{}/documents/{}?download={}'.format(self.audit_id, doc_id, key))
    self.assertEqual(response.status, '302 Moved Temporarily')
    self.assertIn('http://localhost/get/', response.location)
    self.assertIn('Signature=', response.location)
    self.assertIn('KeyID=', response.location)
    self.assertNotIn('Expires=', response.location)

    response = self.app.get('/audits/{}/documents/{}'.format(self.audit_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])
    self.assertEqual(u'Рішення про початок моніторингу.doc', response.json['data']['title'])

    response = self.app.post_json(
        '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {
            'title': u'Рішення про початок моніторингу.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword'
        }}
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(u'Рішення про початок моніторингу.doc', response.json['data']['title'])
    doc_id = response.json['data']['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertNotIn('acc_token', response.headers['Location'])


def put_audit_document_json(self):
    response = self.app.post_json(
        '/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {
            'title': u'Рішення про початок моніторингу.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }}
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(u'Рішення про початок моніторингу.doc', response.json['data']['title'])
    doc_id = response.json['data']['id']
    date_modified = response.json['data']['dateModified']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.put_json(
        '/audits/{}/documents/{}?acc_token={}'.format(self.audit_id, doc_id, self.audit_token),
        {'data': {
            'title': u'audit.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])
    self.assertIn('Signature=', response.json["data"]["url"])
    self.assertIn('KeyID=', response.json["data"]["url"])
    self.assertNotIn('Expires=', response.json["data"]["url"])
    key = response.json["data"]["url"].split('/')[-1].split('?')[0]
    audit = self.db.get(self.audit_id)
    self.assertIn(key, audit['documents'][-1]["url"])
    self.assertIn('Signature=', audit['documents'][-1]["url"])
    self.assertIn('KeyID=', audit['documents'][-1]["url"])
    self.assertNotIn('Expires=', audit['documents'][-1]["url"])

    response = self.app.get('/audits/{}/documents/{}?download={}'.format(self.audit_id, doc_id, key))
    self.assertEqual(response.status, '302 Moved Temporarily')
    self.assertIn('http://localhost/get/', response.location)
    self.assertIn('Signature=', response.location)
    self.assertIn('KeyID=', response.location)
    self.assertNotIn('Expires=', response.location)

    response = self.app.get('/audits/{}/documents/{}'.format(self.audit_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])
    self.assertEqual('audit.doc', response.json['data']['title'])
    date_modified2 = response.json['data']['dateModified']
    self.assertTrue(date_modified < date_modified2)
    self.assertEqual(date_modified, response.json['data']['previousVersions'][0]['dateModified'])

    response = self.app.get('/audits/{}/documents?all=true'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(date_modified, response.json['data'][0]['dateModified'])
    self.assertEqual(date_modified2, response.json['data'][1]['dateModified'])

    response = self.app.post_json('/audits/{}/documents?acc_token={}'.format(self.audit_id, self.audit_token),
        {'data': {
            'title': u'audit.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json['data']['id']
    date_modified = response.json['data']['dateModified']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.get('/audits/{}/documents'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(date_modified2, response.json['data'][0]['dateModified'])
    self.assertEqual(date_modified, response.json['data'][1]['dateModified'])

    response = self.app.put_json(
        '/audits/{}/documents/{}?acc_token={}'.format(self.audit_id, doc_id, self.audit_token),
        {'data': {
            'title': u'audit.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json['data']['id'])
    self.assertIn('Signature=', response.json['data']['url'])
    self.assertIn('KeyID=', response.json['data']['url'])
    self.assertNotIn('Expires=', response.json['data']['url'])
    key = response.json['data']['url'].split('/')[-1].split('?')[0]
    audit = self.db.get(self.audit_id)
    self.assertIn(key, audit['documents'][-1]['url'])
    self.assertIn('Signature=', audit['documents'][-1]['url'])
    self.assertIn('KeyID=', audit['documents'][-1]['url'])
    self.assertNotIn('Expires=', audit['documents'][-1]['url'])

    response = self.app.get('/audits/{}/documents/{}?download={}'.format(self.audit_id, doc_id, key))
    self.assertEqual(response.status, '302 Moved Temporarily')
    self.assertIn('http://localhost/get/', response.location)
    self.assertIn('Signature=', response.location)
    self.assertIn('KeyID=', response.location)
    self.assertNotIn('Expires=', response.location)

