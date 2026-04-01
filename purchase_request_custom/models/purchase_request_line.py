# Copyright 2023 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseRequestLine(models.Model):
    _inherit = "purchase.request.line"

    estimated_cost = fields.Float(
        compute="_compute_estimated_cost", store=True, tracking=True
    )

    estimated_unit_cost = fields.Float(
        compute="_compute_estimated_unit_cost",
        readonly=False,
        store=True,
        tracking=True,
    )

    target_value = fields.Float(
        string="Target Unit Price",
        compute="_compute_target",
        compute_sudo=True,
        store=True,
    )

    target_quantity = fields.Float(
        compute="_compute_target",
        compute_sudo=True,
        store=True,
    )

    target_above = fields.Boolean(
        compute="_compute_target",
        compute_sudo=True,
    )

    @api.depends(
        "product_qty",
        "product_id",
        "estimated_unit_cost",
    )
    def _compute_estimated_cost(self):
        """
        Calculate the estimated cost of the purchase request line.
        """
        for line in self:
            line.estimated_cost = line.product_qty * line.estimated_unit_cost

    @api.depends("product_id")
    def _compute_estimated_unit_cost(self):
        """
        Compute the estimated unit cost based on product's standard price.
        """
        for line in self:
            if line.product_id:
                line.estimated_unit_cost = line.product_id.standard_price
            else:
                line.estimated_unit_cost = 0.0

    @api.depends(
        "analytic_distribution",
        "estimated_unit_cost",
        "product_id",
    )
    def _compute_target(self):
        for record in self:
            product = False
            service = False
            price_unit = 0
            account_analytic = False
            target_above = False
            target_quantity = 0
            if record.product_id:
                distribution = record.analytic_distribution or {}
                account_ids = (
                    list(distribution.keys()) if isinstance(distribution, dict) else []
                )
                if account_ids:
                    account_analytic = self.env["account.analytic.account"].browse(
                        int(account_ids[0])
                    )
                if account_analytic:
                    blanket_order = record.env["sale.blanket.order"].search(
                        [("analytic_account_id", "=", account_analytic.id)],
                        limit=1,
                        order="id desc",
                    )

                    if blanket_order:
                        product = blanket_order.order_product_ids.search(
                            [
                                ("product_id", "=", record.product_id.id),
                                ("blanket_order_id", "=", blanket_order.id),
                            ],
                            limit=1,
                            order="write_date desc",
                        )
                        service = blanket_order.order_service_ids.search(
                            [
                                ("product_id", "=", record.product_id.id),
                                ("blanket_order_id", "=", blanket_order.id),
                            ],
                            limit=1,
                            order="write_date desc",
                        )
                        if product.id:
                            price_unit = product.price_unit
                            target_quantity = product.quantity
                        elif service.id:
                            price_unit = service.price_unit
                            target_quantity = service.quantity

            record.target_value = price_unit
            record.target_quantity = target_quantity
            if record.estimated_unit_cost > price_unit:
                target_above = True
            record.target_above = target_above
