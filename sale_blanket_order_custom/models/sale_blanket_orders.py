# Copyright 2023 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round


class SaleBlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    sale_order_plan_ids = fields.One2many(
        comodel_name="sale.blanket.order.sale.order.plan",
        inverse_name="sale_id",
        string="Sale Order Plan",
        copy=False,
    )
    use_sale_order_plan = fields.Boolean(
        default=False,
        copy=False,
    )
    ip_sale_order_plan = fields.Boolean(
        string="Sale Order Plan In Process",
        compute="_compute_ip_sale_order_plan",
        help="At least one order plan line pending to create sale order",
    )
    order_product_ids = fields.One2many(
        "sale.blanket.order.product",
        "blanket_order_id",
        string="Blanket Order Products Costs",
    )

    order_service_ids = fields.One2many(
        "sale.blanket.order.service",
        "blanket_order_id",
        string="Blanket Order Services Costs",
    )

    total_product_costs = fields.Monetary(
        "Total Product Cost Target", compute="_compute_total_product_costs"
    )

    total_service_costs = fields.Monetary(
        "Total Service Cost Target", compute="_compute_total_service_costs"
    )

    total_costs = fields.Monetary(
        string="Total Cost Target (Products Costs + Services Costs)",
        compute="_compute_total_costs",
        store=True,
    )

    account_analytic_line_ids = fields.One2many(
        comodel_name="account.analytic.line",
        compute="_compute_account_analytic_line_ids",
        string="Analytic Line",
        required=False,
    )

    account_analytic_line_count = fields.Integer(
        compute="_compute_account_analytic_line_ids",
    )

    mis_cash_flow_forecast_line_ids = fields.One2many(
        comodel_name="mis.cash_flow.forecast_line",
        compute="_compute_mis_cash_flow_forecast_line_ids",
        string="Forecast Line",
        required=False,
    )

    mis_cash_flow_forecast_line_count = fields.Integer(
        compute="_compute_mis_cash_flow_forecast_line_ids",
        string="Forecast Line Count",
    )

    def _compute_mis_cash_flow_forecast_line_ids(self):
        ForecastLine = self.env["mis.cash_flow.forecast_line"]
        forecast_lines = ForecastLine.sudo().search(
            [
                ("res_model", "=", self._name),
                ("res_id", "in", self.ids),
            ]
        )

        result = dict.fromkeys(self.ids, ForecastLine)
        for forecast in forecast_lines:
            result[forecast.res_id] |= forecast

        for rec in self:
            rec.mis_cash_flow_forecast_line_ids = result[rec.id]
            rec.mis_cash_flow_forecast_line_count = len(
                rec.mis_cash_flow_forecast_line_ids
            )

    def _compute_account_analytic_line_ids(self):
        for rec in self:
            account_analytic_line = self.env["account.analytic.line"]
            account_analytic_lines = account_analytic_line.search(
                [
                    ("account_id", "=", rec.analytic_account_id.id),
                ]
            )
            rec.account_analytic_line_ids = account_analytic_lines
            rec.account_analytic_line_count = len(rec.account_analytic_line_ids)

    def _compute_ip_sale_order_plan(self):
        for rec in self:
            has_order_plan = rec.use_sale_order_plan and rec.sale_order_plan_ids
            to_order = rec.sale_order_plan_ids.filtered(lambda line: not line.ordered)
            if rec.state == "open" and has_order_plan and to_order:
                rec.ip_sale_order_plan = True
                continue
            rec.ip_sale_order_plan = False

    @api.constrains("state")
    def _check_order_plan(self):
        for rec in self:
            if rec.state != "draft":
                if rec.sale_order_plan_ids.filtered(lambda line: not line.percent):
                    raise ValidationError(
                        _("Please fill percentage for all order plan lines")
                    )

    def action_confirm(self):
        if self.filtered(lambda r: r.use_sale_order_plan and not r.sale_order_plan_ids):
            raise UserError(_("Use Order Plan selected, but no plan created"))
        return super().action_confirm()

    def create_order_plan(
        self, num_installment, installment_date, interval, interval_type
    ):
        self.ensure_one()
        self.sale_order_plan_ids.unlink()
        order_plans = []
        Decimal = self.env["decimal.precision"]
        prec = Decimal.precision_get("Product Unit of Measure")
        percent = float_round(1.0 / num_installment * 100, prec)
        percent_last = 100 - (percent * (num_installment - 1))
        # Normal
        for i in range(num_installment):
            this_installment = i + 1
            if num_installment == this_installment:
                percent = percent_last
            vals = {
                "installment": this_installment,
                "plan_date": installment_date,
                "order_type": "installment",
                "percent": percent,
            }
            order_plans.append((0, 0, vals))
            installment_date = self._next_date(
                installment_date, interval, interval_type
            )
        self.write({"sale_order_plan_ids": order_plans})
        return True

    def remove_order_plan(self):
        self.ensure_one()
        self.sale_order_plan_ids.unlink()
        return True

    @api.model
    def _next_date(self, installment_date, interval, interval_type):
        installment_date = fields.Date.from_string(installment_date)
        if interval_type == "month":
            next_date = installment_date + relativedelta(months=+interval)
        elif interval_type == "year":
            next_date = installment_date + relativedelta(years=+interval)
        else:
            next_date = installment_date + relativedelta(days=+interval)
        next_date = fields.Date.to_string(next_date)
        return next_date

    def _create_sale_order(self):
        order_plan_id = self._context.get("order_plan_id")
        available_lines = self.line_ids.filtered(
            lambda line: line.remaining_uom_qty > 0
        )
        if not available_lines:
            return self.env["sale.order"]
        plan = None
        if order_plan_id:
            plan = self.env["sale.blanket.order.sale.order.plan"].browse(order_plan_id)
            plan._compute_last()
        calculated_before = False
        lines = []
        for line in available_lines:
            if plan and not plan.last:
                plan_qty = line.original_uom_qty * (plan.percent / 100)
                prec = line.product_uom.rounding
                plan_qty = float_round(plan_qty, precision_rounding=prec)
                qty = min(plan_qty, line.remaining_uom_qty)
                calculated_before = True
            else:
                qty = line.remaining_uom_qty
            if qty <= 0:
                continue
            lines.append(
                (
                    0,
                    0,
                    {
                        "blanket_line_id": line.id,
                        "product_id": line.product_id.id,
                        "date_schedule": line.date_schedule,
                        "remaining_uom_qty": line.remaining_uom_qty,
                        "price_unit": line.price_unit,
                        "product_uom": line.product_uom,
                        "qty": qty,
                        "partner_id": line.partner_id,
                    },
                )
            )
        if not lines:
            return self.env["sale.order"]

        wizard = (
            self.env["sale.blanket.order.wizard"]
            .with_context(active_id=self.id, active_model="sale.blanket.order")
            .create({"blanket_order_id": self.id, "line_ids": lines})
        )

        result = wizard.create_sale_order()
        domain = result.get("domain", [])
        if not domain or not domain[0]:
            return self.env["sale.order"]
        sale_order_id = domain[0][2][0]
        orders = self.env["sale.order"].search([("id", "=", sale_order_id)])
        if not orders:
            return self.env["sale.order"]
        blanket_orders = self.env["sale.blanket.order"].browse(self.id)
        if plan:
            for order in orders:
                if not calculated_before:
                    plan._compute_new_order_quantity(blanket_orders)
                order.date_order = plan.plan_date
            plan.sale_order_ids += orders
        return orders

    @api.depends("amount_total", "total_service_costs", "total_product_costs")
    def _compute_total_costs(self):
        for order in self:
            order.total_costs = order.total_product_costs + order.total_service_costs

    @api.depends("order_product_ids.amount_total")
    def _compute_total_product_costs(self):
        for order in self:
            order.total_product_costs = sum(
                [line.amount_total for line in order.order_product_ids]
            )

    @api.depends("order_service_ids.amount_total")
    def _compute_total_service_costs(self):
        for order in self:
            order.total_service_costs = sum(
                [line.amount_total for line in order.order_service_ids]
            )

    def action_show_mis_forecast(self):
        self.ensure_one()
        context = dict(self.env.context)
        context.pop("group_by", None)

        return {
            "type": "ir.actions.act_window",
            "name": _("Cash Flow Forecast - Sale Blanket Order"),
            "res_model": "mis.cash_flow.forecast_line",
            "domain": [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
            ],
            "view_mode": "pivot,tree",
            "context": context,
        }

    def action_show_account_analytic_line(self):
        self.ensure_one()
        context = dict(self.env.context)
        context.pop("group_by", None)
        context.update({"tree_view_ref": "analytic.view_account_analytic_line_tree"})

        return {
            "type": "ir.actions.act_window",
            "name": _("Account Analytic Line"),
            "res_model": "account.analytic.line",
            "domain": [
                ("account_id", "=", self.analytic_account_id.id),
            ],
            "view_mode": "tree,pivot",
            "context": context,
        }


class BlanketOrderLine(models.Model):
    _inherit = "sale.blanket.order.line"

    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        related="order_id.analytic_account_id",
        string="Analytic Account",
    )
