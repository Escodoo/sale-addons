# Copyright 2020 Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sale Commission Supplier Agent Type',
    'summary': """
        This module enable a new agent type called supplier and force generate invoices in_refund type.""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Escodoo,Odoo Community Association (OCA)',
    'website': 'www.escodoo.com.br',
    'depends': [
        'sale_commission',
    ],
    'data': [
        'views/sale_commission_settlement.xml',
    ],
    'demo': [
    ],
}
