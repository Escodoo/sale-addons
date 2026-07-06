# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

BLANKET_SALE_ORDER_SUBTOTAL_LINE = "Blanket Sale Order subtotal line"


class ResCompany(models.Model):
    _inherit = "res.company"

    blanket_sale_order_subtotal_line_truncation_digits = fields.Integer(
        string="Blanket Sale Order Subtotal Line Truncation Precision",
        compute="_compute_blanket_sale_order_subtotal_line_truncation_digits",
        inverse="_inverse_blanket_sale_order_subtotal_line_truncation_digits",
        help="Number of decimals kept when truncating the blanket order "
        "line subtotal (e.g. 4 = 0.0001).",
    )

    def _compute_blanket_sale_order_subtotal_line_truncation_digits(self):
        precision_get = self.env["decimal.precision"].precision_get
        for company in self:
            company.blanket_sale_order_subtotal_line_truncation_digits = precision_get(
                BLANKET_SALE_ORDER_SUBTOTAL_LINE
            )

    def _inverse_blanket_sale_order_subtotal_line_truncation_digits(self):
        precision = self.env["decimal.precision"].search(
            [("name", "=", BLANKET_SALE_ORDER_SUBTOTAL_LINE)], limit=1
        )
        for company in self:
            precision.digits = (
                company.blanket_sale_order_subtotal_line_truncation_digits
            )
