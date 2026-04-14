# Copyright 2025 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class SaleBlanketOrderCommon(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        AnalyticAccount = cls.env["account.analytic.account"]
        AnalyticPlan = cls.env["account.analytic.plan"]
        cls.plan_a = AnalyticPlan.create({"name": "Plan A"})
        cls.analytic_account_a1 = AnalyticAccount.create(
            {
                "name": "analytic_account_a1",
                "plan_id": cls.plan_a.id,
            }
        )
        cls.partner_a = cls.env.ref("base.res_partner_3")
        cls.product_a = cls.env.ref("product.product_product_1")
        cls.service_a = cls.env.ref("product.product_product_4")
        cls.pricelist = cls.env.ref("product.list0")
        cls.currency = cls.env.company.currency_id
        cls.blanket = cls.env["sale.blanket.order"].create(
            {
                "partner_id": cls.partner_a.id,
                "currency_id": cls.currency.id,
                "pricelist_id": cls.pricelist.id,
                "analytic_account_id": cls.analytic_account_a1.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_a.id,
                            "product_uom": cls.product_a.uom_id.id,
                            "original_uom_qty": 12.0,
                            "price_unit": cls.product_a.lst_price,
                        },
                    )
                ],
            }
        )
