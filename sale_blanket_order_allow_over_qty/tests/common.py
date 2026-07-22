# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class SaleBlanketOrderAllowOverQtyCommon(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        plan = cls.env["account.analytic.plan"].create({"name": "Allow Over Qty Plan"})
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {
                "name": "allow_over_qty_analytic_account",
                "plan_id": plan.id,
            }
        )
        cls.partner = cls.env.ref("base.res_partner_3")
        cls.product = cls.env.ref("product.product_product_1")
        cls.pricelist = cls.env.ref("product.list0")
        cls.currency = cls.env.company.currency_id
