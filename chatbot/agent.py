import os
import re
import json
import time
from openai import OpenAI
from .tools import TOOL_DEFINITIONS, TOOL_HANDLERS

SKILL_PATH = os.path.expanduser(
    "~/.config/opencode/skills/customerbot/SKILL.md"
)

FALLBACK_MODELS = [
    "llama-3.1-8b-instant",
    "openai/gpt-oss-20b",
]

SCOPE_BOUNDARY = (
    "## CRITICAL SCOPE RULE — You must obey this above all else.\n\n"
    "You are NexSupport AI, the official banking support assistant. "
    "You ONLY answer questions about retail and commercial banking:\n"
    "1) ACCOUNTS — chequing, savings, credit cards, balances, statements, "
    "account status, account opening, account closures.\n"
    "2) TRANSACTIONS — e-Transfers, wire transfers, direct deposits, bill payments, "
    "debit/credit card purchases, pending transactions, transaction disputes, "
    "chargebacks, reversals.\n"
    "3) CARDS — debit cards, credit cards, lost/stolen card reporting, card freezing, "
    "card activation, PIN reset, replacement cards.\n"
    "4) FEES & RATES — account fees, interest rates (savings, GICs), "
    "transfer fees, foreign exchange rates, service charges.\n"
    "5) ONLINE & MOBILE BANKING — app support, login issues, "
    "transfer limits, account alerts, password reset, two-factor authentication.\n"
    "6) LOANS & CREDIT — personal loans, mortgages, lines of credit, "
    "loan applications, credit score inquiries, payment schedules.\n"
    "7) SECURITY & FRAUD — reporting unauthorised transactions, fraud alerts, "
    "suspicious activity, account security, phishing awareness.\n\n"
    "If the user asks about ANYTHING outside personal or business banking, you MUST:\n"
    "- Politely say the topic is outside your focus\n"
    "- Redirect to a related banking topic if possible\n"
    "- Keep it to 2-3 sentences maximum\n"
    "- NEVER answer the off-topic question, even partially\n"
    "- NEVER say \"I cannot answer\" — instead say something like: "
    "\"That's outside my banking focus, but I'd be happy to help with any account or transaction questions you have!\"\n\n"
    "EXAMPLES of off-topic topics: health/medical, agriculture/farming, politics, "
    "entertainment/sports, programming/coding, personal relationships, general trivia, "
    "cryptocurrency speculation, religion, vehicle repair, immigration/visa, "
    "gambling/betting, cooking/recipes, homework assignments, e-commerce orders, "
    "product shipping/returns, retail purchases.\n"
)

OUT_OF_SCOPE_PATTERNS = [
    r'\b(recipe|cook|bake|ingredient|dinner|lunch|breakfast|meal|pizza|pasta|wine|coffee|food|dish)\b',
    r'\b(sports|football|basketball|soccer|game|match|player|team|hockey|cricket|tennis)\b',
    r'\b(health|doctor|hospital|medicine|disease|symptom|pain|treatment|diagnos|headache|fever|cough|cold|flu|ache|hurt|injury|sick|ill|nausea|vomit|dizzy|allergy|infection|surgery|medication|drug|prescription|vaccine|therapy|therapist|psychologist|depression|anxiety|stress)\b',
    r'\b(farming|farm|crop|plant|harvest|livestock|agriculture|soil|fertilizer)\b',
    r'\b(politics|election|president|prime minister|government|political|vote|party|congress|senator|policy debate)\b',
    r'\b(programming|code|coding|software|app|website|python|javascript|react|api|algorithm|database|server|gpu|bug|deployment)\b',
    r'\b(relationship|dating|marriage|boyfriend|girlfriend|family|advice)\b',
    r'\b(horoscope|astrology|psychic|spiritual|prayer|bible|religious|religion)\b',
    r'\b(car|vehicle|mechanic|engine|tire|repair|maintenance)\b',
    r'\b(immigration|visa|passport|citizenship|green card)\b',
    r'\b(gambling|betting|crypto|bitcoin|invest|stock|trading|nft)\b',
    r'\b(celebrity|movie|music|song|actor|actress|entertainment|film|album|artist|band)\b',
    r'\b(homework|assignment|exam|test|quiz|college|university|school|teacher|student)\b',
    r'\b(weight loss|diet|exercise|workout|fitness|nutrition|gym|muscle)\b',
    r'\b(capital|country|city|geography|continent|population|flag|language)\b',
    r'\b(weather|forecast|climate|temperature|storm|rain)\b',
    r'\b(history|historical|war|battle|civilization|president of|king|queen)\b',
    r'\b(science|biology|chemistry|physics|space|nasa|universe|gravity|element)\b',
    r'\b(math|mathematics|algebra|calculus|equation|geometry|statistics|probability)\b',
    r'\b(trivia|general knowledge|fun fact|riddle|random question|guess|joke|poem)\b',
    r'\b(news|current events|celebrity news|headlines)\b',
    r'\b(travel|vacation|holiday|flight|airport|hotel|booking|destination)\b',
    r'\b(pet|dog|cat|animal|veterinarian|breed|zoo)\b',
    r'\b(pregnancy|baby|child|children|parenting|toddler|newborn)\b',
    r'\b(job|career|employment|interview|resume|salary|layoff)\b',
    r'\b(diy|home improvement|renovation|furniture|decorating|handyman)\b',
]


IN_SCOPE_KEYWORDS = [
    r'\b(account|chequing|checking|savings|balance|deposit|withdraw|withdrawal)s?\b',
    r'\b(transfer|wire|e-?transfer|etransfer|payment|bill|pay|payee|autopay)s?\b',
    r'\b(card|debit|credit|pin|freeze|fraud|dispute|chargeback|charge)s?\b',
    r'\b(loan|mortgage|interest|rate|gic|tfsa|rrsp|fee|service charge|overdraft|line of credit)s?\b',
    r'\b(statement|transaction|pending|online banking|mobile|app|login)s?\b',
    r'\b(bank|banking|password|limit|alert|security|unauthorised|unauthorized)s?\b',
    r'\b(ticket|faq|policy|support|help)s?\b',
    r'\b(routing|iban|swift|branch|atm|cheque|check|receipt|due date|minimum balance)s?\b',
]


def is_out_of_scope(message: str) -> str | None:
    msg_lower = message.lower().strip()
    msg_clean = re.sub(r"[^a-z0-9\s']", ' ', msg_lower).strip()

    greetings = [
        'hi', 'hello', 'hey', 'good morning',
        'good afternoon', 'good evening', "what's up", 'yo',
    ]
    if msg_clean in greetings or msg_clean.startswith(('hi ', 'hello ', 'hey ')):
        return None

    if msg_clean in (
        'who are you', 'what can you do', 'what do you do', 'help',
        'thanks', 'thank you', 'thank you very much', 'goodbye', 'bye',
        'ok', 'okay', 'yes', 'no', 'yes please', 'ok thanks', 'cool',
        'great', 'perfect', "that's all", 'no thanks',
    ):
        return None

    health_pattern = re.compile(r'\b(headache|fever|cough|cold|flu|ache|hurt|sick|ill|nausea|pain|doctor|medicine|symptom|diagnos|treatment)\b')
    health_matches = health_pattern.findall(msg_clean)
    has_bank_context = bool(re.search(r'\b(health insurance|dental|benefit|employee|workplace|policy|bank|account|payment|claim|coverage)\b', msg_clean))
    if len(health_matches) >= 1 and not has_bank_context:
        return (
            "Health questions are outside my scope — I specialise in banking "
            "support! If you're asking about health insurance payments or "
            "health benefit claims through your account, I can help with that!"
        )

    score = 0
    for pattern in OUT_OF_SCOPE_PATTERNS:
        score += len(list(re.finditer(pattern, msg_clean)))

    in_scope = False
    for pattern in IN_SCOPE_KEYWORDS:
        if re.search(pattern, msg_clean):
            score -= 2
            in_scope = True

    if score >= 1:
        return (
            "That's outside my banking focus — I specialise in accounts, "
            "transactions, cards, and other banking support! "
            "Is there a banking question I can help you with?"
        )

    # No banking signal at all: assume it is off-topic instead of letting the
    # model answer. This prevents general-knowledge / trivia queries slipping
    # through the keyword heuristics.
    if not in_scope:
        return (
            "That's outside my banking focus — I specialise in accounts, "
            "transactions, cards, and other banking support! "
            "Is there a banking question I can help you with?"
        )

    return None


def _load_system_prompt() -> str:
    try:
        with open(SKILL_PATH, encoding="utf-8") as f:
            base = f.read()
    except FileNotFoundError:
        base = (
            "You are NexSupport AI, the official banking support assistant. "
            "Help customers with accounts, transactions, cards, disputes, "
            "and general banking inquiries. Be professional, accurate, "
            "and security-conscious."
        )

    tools_section = (
        "\n\n---\n\n"
        "TOOLS AVAILABLE TO YOU:\n"
        "- lookup_account: Look up a customer bank account by account ID (e.g. ACC-1001)\n"
        "- reverse_transaction: Reverse a pending transaction (e.g. TXN-5001)\n"
        "- update_ticket: Update support ticket status (open, in_progress, resolved, closed)\n"
        "- escalate_to_human: Escalate complex banking issues to a human agent\n"
        "- search_faq: Search banking knowledge base for FAQ answers\n\n"
        "TOOL RULES:\n"
        "- Use tools when a customer asks about accounts, transactions, tickets, or FAQs\n"
        "- Ask for the account/transaction/ticket ID if not provided\n"
        "- Explain what you are doing before or after using a tool\n"
        "- Only reverse transactions with 'pending' status; completed transactions need a formal dispute\n"
        "- For fraud claims, large disputes, or if the customer requests it, offer escalation\n"
        "- Never fabricate account IDs, transaction IDs, ticket IDs, or customer data\n"
        "- Verify customer identity before sharing sensitive account information"
    )

    return SCOPE_BOUNDARY + base + tools_section


AGENT_SYSTEM_PROMPT = _load_system_prompt()


class AgenticServiceBot:
    def __init__(self, api_key: str, model: str, status_callback=None):
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key,
        )
        self.model = model
        self.status_callback = status_callback
        self.messages: list[dict] = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        ]
        self.greeted = False

    def get_greeting(self) -> str:
        greeting_msg = {"role": "user", "content": "Hello, who are you?"}
        self.messages.append(greeting_msg)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=0.7,
                max_tokens=512,
            )
            reply = response.choices[0].message.content or ""
            self.messages.append({"role": "assistant", "content": reply})
            self.greeted = True
            return reply
        except Exception:
            return "Hello! I'm NexSupport AI, your banking support assistant. How can I help you with your accounts or transactions today?"

    def get_closing(self) -> str:
        return (
            "Thank you for chatting with NexSupport AI! If you ever need help "
            "with your accounts, transactions, or any banking questions, "
            "I'm just a message away. Have a great day!"
        )

    def _call_model(self, messages: list[dict], tools=None, max_tokens=2048) -> tuple:
        models_to_try = [self.model]
        for fb in FALLBACK_MODELS:
            if fb not in models_to_try:
                models_to_try.append(fb)

        last_error = None
        for model in models_to_try:
            try:
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": max_tokens,
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                response = self.client.chat.completions.create(**kwargs)

                if model != self.model and self.status_callback:
                    self.status_callback(f"Switched to fallback model: {model}")

                return response, None
            except Exception as e:
                last_error = e
                if self.status_callback:
                    self.status_callback(f"Model '{model}' failed: {e}")
                continue

        return None, last_error

    def chat(self, message: str) -> tuple[str, list[dict]]:
        scope_reply = is_out_of_scope(message)
        if scope_reply:
            return scope_reply, []

        self.messages.append({"role": "user", "content": message})

        tool_calls_log: list[dict] = []
        max_tool_rounds = 5

        for _ in range(max_tool_rounds):
            response, error = self._call_model(
                self.messages, tools=TOOL_DEFINITIONS, max_tokens=2048
            )

            if error:
                err_str = str(error)
                if "tool" in err_str.lower() or "function" in err_str.lower():
                    fallback_reply = self._chat_without_tools(message)
                    return fallback_reply, []
                return f"I'm sorry, I ran into an error: {error}", tool_calls_log

            msg = response.choices[0].message

            if not msg.tool_calls:
                reply = msg.content or ""
                self.messages.append({"role": "assistant", "content": reply})
                return reply, tool_calls_log

            assistant_msg: dict = {"role": "assistant", "content": msg.content or ""}
            api_tool_calls = []
            for tc in msg.tool_calls:
                api_tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })
            assistant_msg["tool_calls"] = api_tool_calls
            self.messages.append(assistant_msg)

            for tc in msg.tool_calls:
                tool_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                handler = TOOL_HANDLERS.get(tool_name)
                if handler:
                    try:
                        result = handler(**args)
                    except TypeError as e:
                        result = {"success": False, "error": str(e)}
                else:
                    result = {"success": False, "error": f"Unknown tool: {tool_name}"}

                result_str = json.dumps(result)

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str,
                })

                tool_calls_log.append({
                    "name": tool_name,
                    "arguments": args,
                    "result": result,
                    "status": "success" if result.get("success", False) else "error",
                })

        return (
            "I apologize, but I'm having trouble completing your request. "
            "Please try rephrasing or contact a human agent for assistance.",
            tool_calls_log,
        )

    def _chat_without_tools(self, message: str) -> str:
        self.messages.append({"role": "user", "content": message})
        try:
            response, error = self._call_model(
                self.messages, tools=None, max_tokens=1024
            )
            if error:
                return f"I'm sorry, I ran into an error: {error}"
            reply = response.choices[0].message.content or ""
            self.messages.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            return f"I'm sorry, I ran into an error: {e}"
