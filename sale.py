#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from trytond.model import fields, ModelSQL, Model
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.pyson import Eval, Bool

__all__ = ['Sale', 'SaleLine', 'ConfigurationCompany', 'Configuration']
__metaclass__ = PoolMeta

PROJECT_METHODS = [
    ('manual', 'Manual'),
    ('order', 'On Order Processed'),
    ('individual', 'Individual'),
    ]


class ConfigurationCompany(ModelSQL):
    'Sale Configuration Per Company'
    __name__ = 'sale.configuration.company'
    company = fields.Many2One('company.company', 'Company', required=True,
        ondelete='CASCADE')
    sale_project_method = fields.Selection(PROJECT_METHODS, 'Project Method')


class Configuration:
    __name__ = 'sale.configuration'
    sale_project_method = fields.Function(fields.Selection(PROJECT_METHODS,
            'Project Method', states={
                'required': Bool(Eval('context', {}).get('company')),
                }), 'get_company_config', setter='set_company_config')

    @classmethod
    def get_company_config(self, configs, names):
        pool = Pool()
        CompanyConfig = pool.get('sale.configuration.company')

        company_id = Transaction().context.get('company')
        company_configs = CompanyConfig.search([
                ('company', '=', company_id),
                ])

        res = {}
        for fname in names:
            res[fname] = {
                configs[0].id: None,
                }
            if company_configs:
                val = getattr(company_configs[0], fname)
                if isinstance(val, Model):
                    val = val.id
                res[fname][configs[0].id] = val
        return res

    @classmethod
    def set_company_config(self, configs, name, value):
        pool = Pool()
        CompanyConfig = pool.get('sale.configuration.company')

        company_id = Transaction().context.get('company')
        company_configs = CompanyConfig.search([
                ('company', '=', company_id),
                ])
        if company_configs:
            company_config = company_configs[0]
        else:
            company_config = CompanyConfig(company=company_id)
        setattr(company_config, name, value)
        company_config.save()


class Sale():
    __name__ = 'sale.sale'
    project_method = fields.Selection([
            ('manual', 'Manual'),
            ('order', 'On Order Processed'),
            ('individual', 'Individual'),
            ], 'Project Method', required=True,
        states={
            'readonly': Eval('state') != 'draft',
            },
        depends=['state'])
    project_state = fields.Selection([
            ('none', 'None'),
            ('waiting', 'Waiting'),
            ('done', 'Done'),
            ('exception', 'Exception'),
            ], 'Project State', readonly=True, required=True)

    @staticmethod
    def default_project_method():
        Config = Pool().get('sale.configuration')
        config = Config(1)
        return config.sale_project_method

    @staticmethod
    def default_project_state():
        return 'none'

    @classmethod
    def process(cls, sales):
        super(Sale, cls).process(sales)
        with Transaction().set_user(0, set_context=True):
            for sale in sales:
                if sale.project_method == 'order':
                    for line in sale.lines:
                        line.create_work()


class SaleLine():
    'Sale Line'
    __name__ = 'sale.line'

    party = fields.Function(fields.Many2One('party.party', 'Party'),
        'get_party', searcher='search_party')
    work = fields.Many2One('project.work', 'Work Effort', readonly=True)
    checked = fields.Boolean('Checked')
    discarded = fields.Boolean('Discarded')

    @classmethod
    def __setup__(cls):
        super(SaleLine, cls).__setup__()
        cls._buttons.update({
                'create_works': {
                    'invisible': Bool(Eval('work')) | Eval('discarded')},
                })

    def get_party(self, name):
        return self.sale.party.id

    @classmethod
    def search_party(cls, name, clause):
        return [('sale.party',) + tuple(clause[1:])]

    @classmethod
    def copy(cls, sales, default=None):
        if default is None:
            default = {}
        default['work'] = None
        return super(SaleLine, cls).copy(sales, default)

    def create_work(self):
        '''
        Creates a work for a line based on default template
        '''
        pool = Pool()
        Work = pool.get('project.work')
        Config = pool.get('project.template.configuration')

        if (self.work or not self.product.project_template
                or self.sale.project_method == 'manual'):
            return

        with Transaction().set_context(party=self.sale.party,
                address=self.sale.shipment_address):
            work, = Work.create_from_template([self.product.project_template],
                self.description, self.quantity)
            work.list_price = self.unit_price
            work.project_invoice_method = 'effort'
            work.save()
        self.work = work
        self.save()

    @classmethod
    def create_works(cls, lines):
        for line in lines:
            line.create_work()
