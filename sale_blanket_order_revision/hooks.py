# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    wizards = env["sale.blanket.order.revision.wizard"].search(
        [("new_blanket_order_id", "!=", False)]
    )
    for wizard in wizards:
        new_order = wizard.new_blanket_order_id
        if not new_order.previous_blanket_order_id:
            new_order.previous_blanket_order_id = wizard.old_blanket_order_id.id
