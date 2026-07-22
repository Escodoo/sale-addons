# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import _, models
from odoo.exceptions import UserError


class SaleBlanketOrderWizard(models.TransientModel):
    _inherit = "sale.blanket.order.wizard"

    def create_sale_order(self):
        # TODO: método reescrito por completo pois o check de quantidade
        # restante do sale_blanket_order (create_sale_orders.py) fica
        # embutido no meio do loop que monta o pedido, sem um método
        # separado para sobrescrever. Não há como pular só esse "if" sem
        # duplicar o restante da lógica.
        allow_over_qty = self.line_ids and all(
            self.line_ids.mapped("blanket_line_id.order_id.allow_over_qty")
        )
        if not allow_over_qty:
            return super().create_sale_order()

        order_lines_by_customer = defaultdict(list)
        currency_id = 0
        pricelist_id = 0
        user_id = 0
        payment_term_id = 0
        client_order_ref = 0
        tag_ids = 0
        for line in self.line_ids.filtered(lambda line: line.qty != 0.0):
            vals = self._prepare_so_line_vals(line)
            order_lines_by_customer[line.partner_id.id].append((0, 0, vals))

            currency_id = self._check_consistency(
                currency_id, line.blanket_line_id.order_id.currency_id.id
            )
            pricelist_id = self._check_consistency(
                pricelist_id, line.blanket_line_id.pricelist_id.id
            )
            user_id = self._check_consistency(user_id, line.blanket_line_id.user_id.id)
            payment_term_id = self._check_consistency(
                payment_term_id, line.blanket_line_id.payment_term_id.id
            )
            client_order_ref = self._check_consistency(
                client_order_ref, line.blanket_line_id.order_id.client_order_ref
            )
            tag_ids = self._check_consistency(
                tag_ids, line.blanket_line_id.order_id.tag_ids
            )

        if not order_lines_by_customer:
            raise UserError(_("An order can't be empty"))

        if not currency_id:
            raise UserError(
                _(
                    "Can not create Sale Order from Blanket "
                    "Order lines with different currencies"
                )
            )

        res = []
        for customer in order_lines_by_customer:
            order_vals = self._prepare_so_vals(
                customer,
                user_id,
                currency_id,
                pricelist_id,
                payment_term_id,
                client_order_ref,
                tag_ids,
                order_lines_by_customer,
            )
            sale_order = self.env["sale.order"].create(order_vals)
            res.append(sale_order.id)
        return {
            "domain": [("id", "in", res)],
            "name": _("Sales Orders"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "sale.order",
            "context": {"from_sale_order": True},
            "type": "ir.actions.act_window",
        }
