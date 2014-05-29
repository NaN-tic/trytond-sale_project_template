#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.

from trytond.pool import Pool
from .sale import *
from .product import *


def register():
    Pool.register(
        Sale,
        SaleLine,
        Work,
        Product,
        ConfigurationCompany,
        Configuration,
        module='sale_project_template', type_='model')
