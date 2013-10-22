#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['Sale', 'SaleLine']

__metaclass__ = PoolMeta


class Sale():
    'Sale'
    __name__ = 'sale.sale'

    @classmethod
    def process(cls, sales):
        super(Sale, cls).process(sales)
        with Transaction().set_user(0, set_context=True):
            for sale in sales:
                for line in sale.lines:
                    line.create_works()


class SaleLine():
    'Sale Line'
    __name__ = 'sale.line'

    create_work = fields.Boolean('Create Work')
    work = fields.Many2One('project.work', 'Work Effort', readonly=True)

    @classmethod
    def __setup__(cls):
        super(SaleLine, cls).__setup__()
        cls._error_messages.update({
                'default_template': ('A default template must be defined.'),
                })

    @staticmethod
    def default_create_work():
        return True

    @classmethod
    def copy(cls, sales, default=None):
        if default is None:
            default = {}
        default['work'] = None
        return super(SaleLine, cls).copy(sales, default)

    def create_works(self):
        '''
        Creates a work for a line based on default template
        '''
        pool = Pool()
        Work = pool.get('project.work')
        Config = pool.get('project.template.configuration')

        config = Config(1)
        if not config.default_template:
            self.raise_user_error('default_template')

        if self.work or not self.create_work:
            return

        with Transaction().set_context(party=self.sale.party,
                address=self.sale.shipment_address):
            work, = Work.create_from_template([config.default_template],
                self.description, self.quantity)

        self.work = work
        self.save()
