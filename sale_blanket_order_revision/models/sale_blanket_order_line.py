# Copyright 2025 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleBlanketOrderLine(models.Model):
    _inherit = "sale.blanket.order.line"

    contracted_quantity = fields.Float(
        readonly=True,
        help="Total quantity contracted based on the associated order lines.",
    )
    initial_original_uom_qty = fields.Float(
        string="Initial Original Quantity",
        readonly=True,
        copy=False,
        help="Original quantity as first defined on the blanket order, "
        "before any revision. Unlike Original Quantity, this value is "
        "never overwritten by later revisions or invoicing.",
    )
    accumulated_contracted_quantity = fields.Float(
        readonly=True,
        copy=False,
        help="Sum of the contracted quantity of this revision and all "
        "previous revisions of the blanket order.",
    )
