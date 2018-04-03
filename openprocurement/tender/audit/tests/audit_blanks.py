from copy import deepcopy

from openprocurement.tender.audit.tests.base import test_tender_data


def create_invalid_audit(self):
    data = deepcopy(self.initial_data)
    response = self.app.post_json('/audits', {'data': data}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description'], 'Forbidden')

    orig_auth = self.app.authorization
    self.app.authorization = ('Basic', ('broker', ''))

    response = self.app.post_json('/audits', {'data': data}, status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description'], 'Not Found')

    response = self.app.post_json('/tenders', {"data": test_tender_data})
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

    self.app.authorization = orig_auth


def create_audit(self):
    data = deepcopy(self.initial_data)
    data.update({'tender_id': self.tender_id})

    orig_auth = self.app.authorization
    self.app.authorization = ('Basic', ('broker', ''))

    response = self.app.post_json('/audits', {'data': data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')

    audit = response.json['data']
    self.assertEqual(audit['title'], 'Test title')
    self.assertEqual(audit['procurement_stage'], [u'planing'])
    self.assertEqual(audit['grounds'], [u'indicator'])
    self.assertEqual(audit['status'], 'draft')

    self.app.authorization = orig_auth


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

    # invalid change status
    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token), {'data': {'status': 'terminated'}},
        status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'][0], "Can't change audit status from 'draft' to 'terminated'"
    )

    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token), {'data': {'status': 'some_status'}},
        status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'][0],
        "Value must be one of ['terminated', 'draft', 'published']."
    )

    # change audit status to 'published'
    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token), {'data': {'status': 'published'}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], 'published')

    response = self.app.get('/audits/{}'.format(self.audit_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['title'], 'New Title')

    audit = response.json['data']

    self.assertIn('date_published', audit)
    self.assertNotIn('documents', audit)

    # change audit status on previous
    response = self.app.patch_json(
        '/audits/{}?acc_token={}'.format(self.audit_id, self.audit_token), {'data': {'status': 'draft'}}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], 'published')






