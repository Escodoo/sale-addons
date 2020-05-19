# Copyright 2020 Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sale Direct Sale Comission Invoicing',
    'summary': """
        This module enable to create comission invoice similar when the sale generate a purchase order this necessary""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Escodoo,Odoo Community Association (OCA)',
    'website': 'www.escodoo.com.br',
    'depends': [
        'sale',
        'sale_directsale',
        'purchase',


    ],
    'data': [
        'views/sale_directsale_commission_profile.xml',
        'data/product_data.xml',
        'views/product_template.xml',
        'views/sale_order.xml',
    ],
    'demo': [
        'demo/sale_directsale_commission_profile.xml',
    ],
}