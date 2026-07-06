# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestSaleOrderTruncationSubtotal(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Truncation Test Product", "type": "service"}
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Truncation Test Partner", "truncate_subtotal": True}
        )

    def _create_order(self, truncate_subtotal):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "truncate_subtotal": truncate_subtotal,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            # 47.42 * (1 - 0.03 / 100) = 47.405774, que
                            # arredonda para cima em 47.41 na precisão da
                            # moeda, mas deve ser truncado para 47.40. A
                            # precisão nomeada é de 4 casas, mas campos
                            # Monetary sempre limitam à precisão da própria
                            # moeda (2 casas aqui), que é o ponto de
                            # truncamento efetivo.
                            "price_unit": 47.42,
                            "discount": 0.03,
                        },
                    )
                ],
            }
        )

    def test_truncate_subtotal_cuts_off_extra_decimals_without_rounding(self):
        order = self._create_order(True)
        line = order.order_line
        self.assertEqual(line.price_subtotal, 47.40)
        self.assertEqual(line.price_total, line.price_subtotal + line.price_tax)

    def test_truncate_subtotal_disabled_keeps_standard_rounding(self):
        order = self._create_order(False)
        line = order.order_line
        self.assertAlmostEqual(line.price_subtotal, 47.41)

    def test_truncate_subtotal_defaults_from_partner(self):
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        self.assertTrue(order.truncate_subtotal)

    def test_toggling_truncate_subtotal_recomputes_existing_line(self):
        # Teste de regressão: gravar a flag num pedido já criado deve
        # recalcular o subtotal da linha (já armazenado), não só aplicar
        # na criação.
        order = self._create_order(False)
        line = order.order_line
        self.assertAlmostEqual(line.price_subtotal, 47.41)

        order.write({"truncate_subtotal": True})
        self.assertEqual(line.price_subtotal, 47.40)

        order.write({"truncate_subtotal": False})
        self.assertAlmostEqual(line.price_subtotal, 47.41)

    def test_changing_partner_flag_does_not_affect_existing_orders(self):
        # A flag do parceiro só serve de valor padrão quando o pedido
        # seleciona o parceiro (veja test_truncate_subtotal_defaults_from_
        # partner acima). Alterá-la depois não deve mudar retroativamente
        # pedidos já criados para esse parceiro, já que a flag deve ser
        # persistida/editável por pedido (SO/BO), não um vínculo ao vivo
        # com o parceiro.
        partner = self.env["res.partner"].create(
            {"name": "Late Flag Partner", "truncate_subtotal": False}
        )
        order = self.env["sale.order"].create({"partner_id": partner.id})
        self.assertFalse(order.truncate_subtotal)

        partner.truncate_subtotal = True
        self.assertFalse(order.truncate_subtotal)

    def test_truncation_is_clamped_to_currency_precision(self):
        # Documenta/comprova, com números explícitos, por que 47.42 *
        # (1 - 0.03 / 100) vira 47.40 (truncado) ou 47.41 (arredondado)
        # em vez do mais intuitivo 47.405774 ou de um valor com 4 casas:
        # a precisão nomeada está configurada em 4 dígitos, mas um campo
        # Monetary sempre limita à precisão da moeda do registro (2
        # dígitos para uma moeda padrão), que é a precisão que realmente
        # se aplica.
        precision = self.env["decimal.precision"].search(
            [("name", "=", "Sale Order subtotal line")]
        )
        self.assertEqual(precision.digits, 4)

        order = self._create_order(True)
        line = order.order_line
        self.assertEqual(line.currency_id.decimal_places, 2)

        raw_amount = 47.42 * (1 - 0.03 / 100)
        self.assertAlmostEqual(raw_amount, 47.405774)

        self.assertEqual(line.price_subtotal, 47.40)

        order.truncate_subtotal = False
        self.assertAlmostEqual(line.price_subtotal, 47.41)
