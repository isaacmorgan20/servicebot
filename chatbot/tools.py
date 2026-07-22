import json

_ACCOUNTS = {
    "ACC-1001": {
        "id": "ACC-1001", "customer": "Alice Johnson",
        "type": "Chequing", "balance": 12450.00,
        "status": "active", "opened": "2024-03-15",
    },
    "ACC-1002": {
        "id": "ACC-1002", "customer": "Bob Smith",
        "type": "Savings", "balance": 47200.00,
        "status": "active", "opened": "2023-11-02",
    },
    "ACC-1003": {
        "id": "ACC-1003", "customer": "Carol Davis",
        "type": "Credit Card", "balance": 2300.00,
        "status": "frozen", "opened": "2024-06-20",
        "reason": "Payment overdue — 45 days past due",
    },
    "ACC-1004": {
        "id": "ACC-1004", "customer": "David Wilson",
        "type": "Chequing", "balance": 850.00,
        "status": "active", "opened": "2025-01-10",
    },
}

_TRANSACTIONS = {
    "TXN-5001": {
        "id": "TXN-5001", "customer": "Alice Johnson",
        "type": "e-Transfer", "amount": 250.00,
        "status": "pending", "date": "2025-06-15",
        "description": "e-Transfer to frank@email.com",
    },
    "TXN-5002": {
        "id": "TXN-5002", "customer": "Bob Smith",
        "type": "Wire Transfer", "amount": 5000.00,
        "status": "completed", "date": "2025-06-14",
        "description": "International wire transfer to Savings account #8842",
    },
    "TXN-5003": {
        "id": "TXN-5003", "customer": "Carol Davis",
        "type": "Debit Card Purchase", "amount": 89.99,
        "status": "disputed", "date": "2025-06-10",
        "description": "Online purchase at TechStore.com — reported as unauthorised",
    },
    "TXN-5004": {
        "id": "TXN-5004", "customer": "David Wilson",
        "type": "Direct Deposit", "amount": 3200.00,
        "status": "completed", "date": "2025-06-01",
        "description": "Monthly payroll deposit from Acme Corp",
    },
}

_TICKETS = {
    "TKT-5001": {
        "id": "TKT-5001", "customer": "Alice Johnson",
        "subject": "Unauthorised transaction on chequing account",
        "status": "open", "priority": "high", "created": "2025-06-15",
    },
    "TKT-5002": {
        "id": "TKT-5002", "customer": "Bob Smith",
        "subject": "International wire transfer delayed",
        "status": "in_progress", "priority": "medium", "created": "2025-06-12",
    },
    "TKT-5003": {
        "id": "TKT-5003", "customer": "Carol Davis",
        "subject": "Request to unfreeze credit card",
        "status": "open", "priority": "low", "created": "2025-06-14",
    },
}

_FAQS = [
    {"question": "How do I open an account?", "answer": "You can open an account online in minutes. Visit our website or mobile app, select the account type (Chequing, Savings, or Credit Card), and complete the application. Approval typically takes 1-2 business days."},
    {"question": "What are your account fees?", "answer": "Our Chequing account has no monthly fee when you maintain a minimum balance of $500. Savings accounts have no monthly fees. Credit cards have an annual fee of $99 with the first year waived."},
    {"question": "How do I dispute a transaction?", "answer": "You can dispute a transaction directly in the mobile app under 'Transaction History' or call our support line. Disputes must be filed within 60 days of the transaction date. We'll investigate and issue a provisional credit within 10 business days."},
    {"question": "What are the international transfer fees?", "answer": "International wire transfers have a 1.5% fee (minimum $10, maximum $50). Processing takes 3-5 business days depending on the destination country."},
    {"question": "How do I report a lost or stolen card?", "answer": "Freeze your card immediately in the mobile app under 'Card Settings'. Then contact our 24/7 support line to order a replacement. You will receive a new card within 5-7 business days. You are not liable for unauthorised transactions if you report the loss promptly."},
    {"question": "What are your current interest rates?", "answer": "Savings Account: 2.50% APY. 1-Year GIC: 3.75%. 3-Year GIC: 4.10%. 5-Year GIC: 4.50%. Rates are subject to change. Contact us for current promotional rates."},
    {"question": "How do I increase my daily transfer limit?", "answer": "You can request a limit increase in the mobile app under 'Account Settings' → 'Transfer Limits'. Increases up to $10,000 are approved instantly. Higher amounts require verification and are processed within 24 hours."},
]

def _lookup_account(account_id: str) -> dict:
    account = _ACCOUNTS.get(account_id.upper())
    if not account:
        return {"success": False, "error": f"Account {account_id} not found."}
    return {"success": True, "data": account}

def _reverse_transaction(transaction_id: str, reason: str) -> dict:
    txn = _TRANSACTIONS.get(transaction_id.upper())
    if not txn:
        return {"success": False, "error": f"Transaction {transaction_id} not found."}
    if txn["status"] == "completed":
        return {"success": False, "error": "Completed transactions cannot be reversed through this channel. Please submit a formal dispute request."}
    if txn["status"] == "disputed":
        return {"success": False, "error": f"Transaction {transaction_id} is already under dispute."}
    return {
        "success": True,
        "data": {
            "transaction_id": transaction_id.upper(),
            "amount": txn["amount"],
            "status": "reversal_initiated",
            "message": f"Reversal of ${txn['amount']:.2f} for transaction {transaction_id.upper()} has been initiated. Funds will be returned within 3-5 business days.",
        },
    }

def _update_ticket(ticket_id: str, status: str, note: str = "") -> dict:
    ticket = _TICKETS.get(ticket_id.upper())
    if not ticket:
        return {"success": False, "error": f"Ticket {ticket_id} not found."}
    valid_statuses = ["open", "in_progress", "resolved", "closed"]
    if status.lower() not in valid_statuses:
        return {"success": False, "error": f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"}
    return {
        "success": True,
        "data": {
            "ticket_id": ticket_id.upper(),
            "previous_status": ticket["status"],
            "new_status": status.lower(),
            "note": note,
        },
    }

def _escalate_to_human(ticket_id: str, reason: str) -> dict:
    ticket = _TICKETS.get(ticket_id.upper())
    if not ticket:
        return {"success": False, "error": f"Ticket {ticket_id} not found."}
    return {
        "success": True,
        "data": {
            "ticket_id": ticket_id.upper(),
            "escalated": True,
            "priority": "high",
            "message": f"Ticket {ticket_id.upper()} has been escalated to a banking agent. Reason: {reason}",
        },
    }

def _search_faq(query: str) -> dict:
    results = []
    q = query.lower()
    for faq in _FAQS:
        if q in faq["question"].lower() or q in faq["answer"].lower():
            results.append(faq)
    if not results:
        return {"success": True, "data": [], "message": "No matching FAQ entries found."}
    return {"success": True, "data": results}


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_account",
            "description": "Look up a customer's bank account by account ID (e.g. ACC-1001). Returns account type, balance, status, and opening date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "The account ID to look up, e.g. ACC-1001",
                    }
                },
                "required": ["account_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reverse_transaction",
            "description": "Initiate a reversal for a pending transaction (e-Transfer, bill payment, etc.). Completed transactions cannot be reversed through this channel — guide the customer to file a formal dispute.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "The transaction ID to reverse, e.g. TXN-5001",
                    },
                    "reason": {
                        "type": "string",
                        "description": "The reason for the reversal request",
                    },
                },
                "required": ["transaction_id", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_ticket",
            "description": "Update the status of a banking support ticket. Valid statuses: open, in_progress, resolved, closed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "The ticket ID to update, e.g. TKT-5001",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["open", "in_progress", "resolved", "closed"],
                        "description": "New status for the ticket",
                    },
                    "note": {
                        "type": "string",
                        "description": "Optional note explaining the update",
                    },
                },
                "required": ["ticket_id", "status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Escalate a banking support ticket to a human agent. Use for complex issues like fraud claims, large disputes, account closures, or when the customer explicitly requests a human.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "The ticket ID to escalate, e.g. TKT-5001",
                    },
                    "reason": {
                        "type": "string",
                        "description": "The reason for escalation",
                    },
                },
                "required": ["ticket_id", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_faq",
            "description": "Search the banking knowledge base / FAQ for answers to common customer questions about accounts, fees, disputes, transfers, cards, and interest rates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query, e.g. 'transfer limit' or 'dispute transaction'",
                    },
                },
                "required": ["query"],
            },
        },
    },
]

TOOL_HANDLERS = {
    "lookup_account": _lookup_account,
    "reverse_transaction": _reverse_transaction,
    "update_ticket": _update_ticket,
    "escalate_to_human": _escalate_to_human,
    "search_faq": _search_faq,
}
