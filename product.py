#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval

__all__ = ['Product']
__metaclass__ = PoolMeta


class Product:
    __name__ = 'product.template'
    project_template = fields.Many2One('project.work', 'Project Template',
        domain=[('template', '=', True)], states={
            'invisible': Eval('type') != 'service',
            }, on_change_with=['type', 'project_template'], depends=['type'])

    def on_change_with_project_template(self):
        if self.type != 'service':
            return None
        return self.project_template.id if self.project_template else None
