# coding=utf-8
from email.header import Header

from openprocurement.tender.audit.tests.base import BaseAuditWebTest

from openprocurement.tender.audit.tests.document_blanks import (
    not_found,
    create_audit_document,
    put_audit_document,
    patch_audit_document,
    create_audit_document_json_invalid,
    create_audit_document_json,
    put_audit_document_json
)


class AuditDocumentResourceTest(BaseAuditWebTest):
    docservice = False
    initial_auth = ('Basic', ('broker', 'broker'))

    def test_create_audit_document(self):
        response = self.app.get('/audits/{}/documents'.format(self.audit_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json, {'data': []})

        response = self.app.post('/audits/{}/documents?acc_token={}'.format(
            self.audit_id, self.audit_token), upload_files=[('file', u'укр.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

    def test_put_audit_document(self):
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

    def test_patch_audit_document(self):
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


class AuditDocumentWithDSResourceTest(AuditDocumentResourceTest):
    docservice = True

    def test_create_audit_document_json(self):
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

# def suite():
#     suite = unittest.TestSuite()
#     suite.addTest(unittest.makeSuite(AuditDocumentResourceTest))
#     suite.addTest(unittest.makeSuite(AuditDocumentWithDSResourceTest))
#     return suite

# def suite():
#     suite = unittest.TestSuite()
#     suite.addTest(unittest.makeSuite(AuditDocumentResourceTest))
#     return suite
#
#
# if __name__ == '__main__':
#     unittest.main(defaultTest='suite')
