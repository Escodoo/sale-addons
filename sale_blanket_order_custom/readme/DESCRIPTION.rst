The `sale_blanket_order_custom` module enhances the standard Blanket Order architecture by implementing a scheduled delivery roadmap system and segmented target costing.


1. ``sale.blanket.order.sale.order.plan``
------------------------------------------
Handles the chronological timeline entries for sales order generation.
* Automatically marks the final entry using ``_compute_last`` to pool any remaining rounding or residual quantities.
* Enforces strict sequential order generation via the ``to_order`` computation logic, preventing out-of-order execution.
* Features a SQL constraint to ensure installment indexes are unique per blanket order.

2. ``sale.blanket.order.product`` & ``sale.blanket.order.service``
------------------------------------------------------------------
Tables acting as cost-tracking ledgers. They capture estimated costs based on product and service `standard_price` defaults and aggregate them on the parent document.

1. ``sale.blanket.order``
-------------------------
* Enforces validation rules preventing agreement confirmation if "Use Sale Order Plan" is enabled but no lines exist, or if any plan line contains a 0% distribution.
* Calculates total target costs globally via ``_compute_total_costs``.
* Dynamically fetches data from ``account.analytic.line`` and ``mis.cash_flow.forecast_line`` to feed smart buttons.

2. ``sale.blanket.order.line``
------------------------------
* Automatically inherits and links the ``analytic_account_id`` from the parent blanket order.

Wizards & Transient Models

1. Create Order Plan (``sale.create.order.plan``)
-------------------------------------------------
An interface gathering generation criteria (number of installments, start date, interval, and interval unit) to wipe and rebuild a clean planning grid.

2. Make Planned Order (``sale.make.planned.order``)
---------------------------------------------------
A execution wizard that handles automated sales order generation, allowing individual sequential creation or bulk creation of all remaining planned releases at once depending on the context flag.