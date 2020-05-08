# Copyright 2020 Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sale Margin Supplierinfo Cost',
    'summary': """
        Change value of purchase_price to supplierinfo.price""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Escodoo,Odoo Community Association (OCA)',
    'website': 'www.escodoo.com.br',
    'depends': [
        'sale_margin',
    ],
    'data': [
        'views/sale_order_line.xml',
    ],
    'demo': [
    ],
}
