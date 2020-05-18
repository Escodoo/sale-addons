# Copyright 2020 Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

class SaleOrderLine(models.Model):
    _inherit = [
        "sale.order.line",
        "sale.commission.mixin",
    ]

    _name = "sale.order.line"

    agents = fields.One2many(
        string="Agents & commissions",
        comodel_name="sale.order.line.agent",
    )

class SaleOrderLineAgent(models.Model):
    _inherit = "sale.order.line.agent"

    order = fields.Many2one(
        string="Sale Order",
        comodel_name="sale.order",
        related="object_id.order_id",
        store=True,
    )

    # TODO: Corrigir data
    order_date = fields.Datetime(
        string="Sale Order Date",
        related="order.confirmation_date",
        store=True,
        readonly=True,
    )
    agent_line = fields.Many2many(
        comodel_name='sale.ds.commission.settlement.line',
        relation='ds_settlement_agent_line_rel',
        column1='agent_line_id',
        column2='settlement_id',
        copy=False,
    )
    settled = fields.Boolean(
        compute="_compute_settled",
        store=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        compute="_compute_company",
        store=True,
    )
    currency_id = fields.Many2one(
        related="object_id.currency_id",
        readonly=True,
    )

    @api.depends('agent_line', 'agent_line.settlement.state', 'order',
                 'order.state')
    def _compute_settled(self):
        # Count lines of not open or paid invoices as settled for not
        # being included in settlements
        for line in self:
            line.settled = (any(x.settlement.state != 'cancel'
                                for x in line.agent_line))

    @api.depends('object_id', 'object_id.company_id')
    def _compute_company(self):
        for line in self:
            line.company_id = line.object_id.company_id

    def _skip_settlement(self):
        """This function should return if the commission can be payed.
        #
        # :return: bool
        # """
        # self.ensure_one()
        # return (
        #     self.commission.invoice_state == 'paid' and
        #     self.invoice.state != 'paid'
        # ) or (self.invoice.state not in ('open', 'paid'))
        return False