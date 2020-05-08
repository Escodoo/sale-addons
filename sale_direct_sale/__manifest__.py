# Copyright 2020 Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sale Direct Sale',
    'summary': """
        This module enable to create sale order for invoicing and delivery direct supplier.""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Escodoo,Odoo Community Association (OCA)',
    'website': 'www.escodoo.com.br',
    'depends': [
        'sale',
        'sale_management',
        'sale_margin',
        'sale_margin_supplierinfo_cost',
        'product_pricelist_supplierinfo',
        # 'stock_picking_sale_order_link',
        # 'stock_dropshipping_from_sale_order'
    ],
    'data': [
        'views/sale_order.xml',
    ],
    'demo': [
    ],
}
