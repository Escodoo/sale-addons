Follow these steps to operate the custom planning and costing tools inside Sale Blanket Orders.

1. Defining Costs and Analytic Accounts

* Navigate to **Sales** > **Orders** > **Blanket Orders** and click **Create**.
* Select a Customer and assign an **Analytic Account** (this field is structurally emphasized and propagates down to all line items).
* Go to the cost target tabs to list your internal estimated resources. The system will automatically use the standard cost price of the items to compute **Total Cost Target (Products Costs + Services Costs)**.

2. Generating an Automated Delivery Schedule

* Tick the checkbox marked **Use Sale Order Plan**.
* Click the designated button to open the generation wizard.
* Enter your criteria, such as:
  * **Number of Installments**: Must be greater than 1.
  * **Interval**: e.g., 1.
  * **Interval Type**: Day, Month, or Year.
* Click **Create**. The planning grid will generate automatically, distributing the percentages evenly across all entries. Any residual decimal fractions are dynamically added to the final installment.

3. Releasing Sales Orders from the Plan

* **Single Release**: Process the line item flagged as **Next Order**. The system will trigger a wizard to create the specific Sales Order, applying the precise percentage volume to your quantities.
* **Bulk Release**: Use the bulk context configuration to trigger all remaining un-ordered plan allocations simultaneously, saving manual operational labor.

4. Financial Auditing

Use the stat buttons located at the top right of the record view to:

* View and review raw ledger records in **Account Analytic Lines**.
* View macro predictions inside the **MIS Cash Flow Forecast** pivot/tree views to see how these long-term agreements impact your company's future liquidity.