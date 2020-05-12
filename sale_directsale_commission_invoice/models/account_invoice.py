# Copyright 2020 Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    # TODO: Tratar cancelamentos
    # @api.multi
    # def button_cancel(self):
    #     result = super(AccountInvoice, self).button_cancel()
    #     self.sudo()._activity_cancel_on_sale()
    #     return result
    #
    # @api.multi
    # def _activity_cancel_on_sale(self):
    #     """ If some PO are cancelled, we need to put an activity on their origin SO (only the open ones). Since a PO can have
    #         been modified by several SO, when cancelling one PO, many next activities can be schedulded on different SO.
    #     """
    #     sale_to_notify_map = {}  # map SO -> recordset of PO as {sale.order: set(purchase.order.line)}
    #     for order in self:
    #         for purchase_line in order.order_line:
    #             if purchase_line.sale_line_id:
    #                 sale_order = purchase_line.sale_line_id.order_id
    #                 sale_to_notify_map.setdefault(sale_order, self.env['purchase.order.line'])
    #                 sale_to_notify_map[sale_order] |= purchase_line
    #
    #     for sale_order, purchase_order_lines in sale_to_notify_map.items():
    #         sale_order.activity_schedule_with_view('mail.mail_activity_data_warning',
    #             user_id=sale_order.user_id.id or self.env.uid,
    #             views_or_xmlid='sale_purchase.exception_sale_on_purchase_cancellation',
    #             render_context={
    #                 'purchase_orders': purchase_order_lines.mapped('order_id'),
    #                 'purchase_lines': purchase_order_lines,
    #         })


class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    directsale_sale_order_id = fields.Many2one(related='directsale_sale_order_line_id.order_id', string="Sale Order", store=True, readonly=True)
    directsale_sale_order_line_id = fields.Many2one('sale.order.line', string="Origin Sale Item", index=True)
