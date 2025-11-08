# support-copilot
First test with the graph finishing without emitting an interrupt.

(.venv) PS D:\Lang\LangRepo\support-copilot> python .\run.py --amount-cents 5100 --order-id A100 --text "double charged, extra $51"
>> Running (will pause if a plan needs approval)...
No approval needed. Running to completion...

=== Draft Reply ===
Thank you for reaching out regarding your order. I understand that you were double charged and are requesting a refund of $51.00. Unfortunately, this request exceeds our automated limits, so I have escalated it to our support team for further assistance.

You can expect to hear back from them soon, and please note that refunds typically settle within 3–5 business days once processed [2]. Thank you for your patience!

=== Execution Results ===
[ToolResult(tool='notify', ok=True, result={'queued': True, 'channel': 'email', 'to': 'support@example.com', 'subject': 'Escalation needed for refund request: ticket t_5100'}, error=None, idempotency_key=None)]

=== Artifacts ===
{'report_json': 'file://tmp/report.json'}

>> Done.
(.venv) PS D:\Lang\LangRepo\support-copilot> python .\run.py --amount-cents 2800 --order-id A100 --text "I was double charged for that order, please refund the second charge."
>> Running (will pause if a plan needs approval)...
Approval requested. Proposed plan:

ticket_id='t_2800' steps=[ActionStep(tool='refund', args={'customer_id': 'cus_123', 'order_id': 'A100', 'amount': 2800, 'reason': 'policy goodwill'}, guard='amount_cents <= 5000', rationale='HIL 2000<=2800<=4000 with evidence present')] requires_approval=True

Approve, Deny, or Defer? [a/d/Enter=defer]: a
=== Draft Reply ===
Your refund has been initiated for the amount of **$28.00**. You can expect it to settle within **3–5 business days**. Thank you for your patience!

=== Execution Results ===
[ToolResult(tool='refund', ok=True, result={'refund_id': 'rf_123', 'currency': 'USD', 'amount': 2800}, error=None, idempotency_key=None)]

=== Artifacts ===
{'report_json': 'file://tmp/report.json'}

>> Done.                                     python .\run.py --amount-cents 1000 --order-id A100 --text "I was double charged for that order, please refund the second charge."
>> Running (will pause if a plan needs approval)...
No approval needed. Running to completion...

=== Draft Reply ===
Your refund has been initiated for the amount of **$10.00** for Order ID **A100**. You can expect the refund to settle within **3–5 business days**. Thank you for your patience!

=== Execution Results ===
[ToolResult(tool='refund', ok=True, result={'refund_id': 'rf_123', 'currency': 'USD', 'amount': 1000}, error=None, idempotency_key=None)]

=== Artifacts ===
{'report_json': 'file://tmp/report.json'}

>> Done.
(.venv) PS D:\Lang\LangRepo\support-copilot>