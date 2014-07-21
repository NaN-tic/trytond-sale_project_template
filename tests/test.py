#!/usr/bin/env python
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_view, test_depends
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction


class TestCase(unittest.TestCase):
    '''
    Test sale_project_template module.
    '''

    def setUp(self):
        trytond.tests.test_tryton.install_module('sale_project_template')
        self.company = POOL.get('company.company')
        self.config = POOL.get('sale.configuration')

    def test0005views(self):
        '''
        Test views.
        '''
        test_view('sale_project_template')

    def test0006depends(self):
        '''
        Test depends.
        '''
        test_depends()

    def test0010_set_default_project_method(self):
        with Transaction().start(DB_NAME, USER,
                context=CONTEXT) as transaction:
            #This is needed in order to get default values for other test
            #executing in the same database
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin'),
                    ])
            with transaction.set_context(company=company.id):
                config = self.config(1)
                config.sale_project_method = 'order'
                config.save()
            transaction.cursor.commit()


def suite():
    suite = trytond.tests.test_tryton.suite()
    from trytond.modules.company.tests import test_company
    for test in test_company.suite():
        if test not in suite:
            suite.addTest(test)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    return suite
