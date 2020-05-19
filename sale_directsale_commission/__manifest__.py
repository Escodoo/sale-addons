# Copyright 2020 Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sale Directsale Commission',
    'summary': """
        Enable to generate commissions This module enable the feature sale_directsale use the oca/commission modules to calculate commissions about the direct sales service and generate commission service invoices.""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Escodoo,Odoo Community Association (OCA)',
    'website': 'www.escodoo.com.br',
    'depends': [
        'sale_commission',
    ],
    'data': [
        # 'views/sale_commission_settlement.xml',
        'views/sale_commission_settlement_view.xml',
        'wizards/wizard_settle.xml',
        'wizards/wizard_invoice.xml',
    ],
    'demo': [
    ],
}
