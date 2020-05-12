# Copyright 2020 Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    service_to_commission_invoice = fields.Boolean("Commission Invoice Automatically", help="If ticked, each time you sell this product through a SO, a RfQ is automatically created to buy the product. Tip: don't forget to set a vendor on the product.")

    _sql_constraints = [
        ('service_to_commission_invoice', "CHECK((type != 'service' AND service_to_commission_invoice != true) or (type = 'service'))", 'Product that is not a service can not create RFQ.'),
    ]

    @api.onchange('type')
    def _onchange_product_type(self):
        if self.type != 'service':
            self.service_to_commission_invoice = False

    @api.onchange('expense_policy')
    def _onchange_expense_policy(self):
        if self.expense_policy != 'no':
            self.service_to_commission_invoice = False
