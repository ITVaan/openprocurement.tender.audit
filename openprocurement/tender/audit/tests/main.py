# -*- coding: utf-8 -*-

import unittest

from openprocurement.tender.audit.tests import document


def suite():
    suite = unittest.TestSuite()
    suite.addTest(document.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
