# Copyright 2025 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleBlanketOrderLine(models.Model):
    _inherit = "sale.blanket.order.line"

    contracted_quantity = fields.Float(
        readonly=True,
        help="Total quantity contracted based on the associated order lines.",
    )
