# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields

from odoo.addons.base.tests.common import BaseCommon


class TestSaleBlanketOrderTruncationSubtotal(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Truncation Test Product", "type": "service"}
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Truncation Test Partner", "truncate_subtotal": True}
        )
        cls.pricelist = cls.env["product.pricelist"].create(
            {"name": "Truncation Test Pricelist"}
        )
        cls.validity_date = fields.Date.to_string(
            fields.Date.today() + timedelta(days=30)
        )

    def _create_blanket_order(self, truncate_subtotal):
        return self.env["sale.blanket.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
                "validity_date": self.validity_date,
                "truncate_subtotal": truncate_subtotal,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom": self.product.uom_id.id,
                            "original_uom_qty": 1.19,
                            # 47.42 * 1.19 = 56.4298, que arredonda para
                            # cima em 56.43 na precisão da moeda, mas deve
                            # ser truncado para 56.42. A precisão nomeada
                            # é de 4 casas, mas campos Monetary sempre
                            # limitam à precisão da própria moeda (2
                            # casas aqui), que é o ponto de truncamento
                            # efetivo.
                            "price_unit": 47.42,
                        },
                    )
                ],
            }
        )

    def test_truncate_subtotal_cuts_off_extra_decimals_without_rounding(self):
        blanket_order = self._create_blanket_order(True)
        line = blanket_order.line_ids
        self.assertEqual(line.price_subtotal, 56.42)
        self.assertEqual(line.price_total, line.price_subtotal + line.price_tax)

    def test_truncate_subtotal_disabled_keeps_standard_rounding(self):
        blanket_order = self._create_blanket_order(False)
        line = blanket_order.line_ids
        self.assertEqual(line.price_subtotal, 56.43)

    def test_truncate_subtotal_defaults_from_partner_onchange(self):
        blanket_order = self.env["sale.blanket.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
                "validity_date": self.validity_date,
            }
        )
        blanket_order.onchange_partner_id()
        self.assertTrue(blanket_order.truncate_subtotal)

    def test_toggling_truncate_subtotal_recomputes_existing_line(self):
        # Teste de regressão: gravar a flag num pedido já criado deve
        # recalcular o subtotal da linha (já armazenado), não só aplicar
        # na criação.
        blanket_order = self._create_blanket_order(False)
        line = blanket_order.line_ids
        self.assertEqual(line.price_subtotal, 56.43)

        blanket_order.write({"truncate_subtotal": True})
        self.assertEqual(line.price_subtotal, 56.42)

        blanket_order.write({"truncate_subtotal": False})
        self.assertEqual(line.price_subtotal, 56.43)

    def test_changing_partner_flag_does_not_affect_existing_orders(self):
        # A flag do parceiro só serve de valor padrão quando o pedido
        # seleciona o parceiro (veja test_truncate_subtotal_defaults_from_
        # partner_onchange acima). Alterá-la depois não deve mudar
        # retroativamente pedidos já criados para esse parceiro, já que a
        # flag deve ser persistida/editável por pedido (BO/SO), não um
        # vínculo ao vivo com o parceiro.
        partner = self.env["res.partner"].create(
            {"name": "Late Flag Partner", "truncate_subtotal": False}
        )
        blanket_order = self.env["sale.blanket.order"].create(
            {
                "partner_id": partner.id,
                "pricelist_id": self.pricelist.id,
                "validity_date": self.validity_date,
            }
        )
        blanket_order.onchange_partner_id()
        self.assertFalse(blanket_order.truncate_subtotal)

        partner.truncate_subtotal = True
        self.assertFalse(blanket_order.truncate_subtotal)

    def test_truncation_is_clamped_to_currency_precision(self):
        # Documenta/comprova, com números explícitos, por que 47.42 *
        # 1.19 vira 56.42 (truncado) ou 56.43 (arredondado) em vez do
        # mais intuitivo 56.4298 ou de um valor com 4 casas: a precisão
        # nomeada está configurada em 4 dígitos, mas um campo Monetary
        # sempre limita à precisão da moeda do registro (2 dígitos para
        # uma moeda padrão), que é a precisão que realmente se aplica.
        precision = self.env["decimal.precision"].search(
            [("name", "=", "Blanket Sale Order subtotal line")]
        )
        self.assertEqual(precision.digits, 4)

        currency = self.pricelist.currency_id
        self.assertEqual(currency.decimal_places, 2)

        raw_amount = 47.42 * 1.19
        self.assertAlmostEqual(raw_amount, 56.4298)

        blanket_order = self._create_blanket_order(True)
        line = blanket_order.line_ids
        self.assertEqual(line.price_subtotal, 56.42)

        blanket_order.truncate_subtotal = False
        self.assertEqual(line.price_subtotal, 56.43)
