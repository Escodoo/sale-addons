This module truncates (instead of rounds) the Blanket Order line subtotal
for partners whose sale condition requires it.

It declares a named Decimal Accuracy precision, "Blanket Sale Order
subtotal line", editable from the Companies form (Truncation tab), and adds
a "Truncated Subtotal" flag on the Blanket Order (defaulted from the
partner's own flag, provided by ``truncation_base``, and persisted on the
order).

When the flag is checked, each order line's subtotal is computed by
truncating the extra decimals at the configured precision instead of
rounding them.
