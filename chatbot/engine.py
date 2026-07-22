import os
import re
import time
from openai import OpenAI


SKILL_PATH = os.path.expanduser(
    "~/.config/opencode/skills/customerbot/SKILL.md"
)

FALLBACK_MODELS = [
    "llama-3.1-8b-instant",
    "openai/gpt-oss-20b",
]


def _load_system_prompt() -> str:
    try:
        with open(SKILL_PATH, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return (
            "You are NexSupport, a professional and empathetic banking support "
            "assistant. Help customers with accounts, transactions, cards, "
            "disputes, and general banking inquiries. Be concise, warm, "
            "and security-conscious."
        )


SYSTEM_PROMPT = _load_system_prompt()


def _extract_retry_after(e: Exception) -> float:
    default_wait = 5.0
    try:
        if hasattr(e, "body") and isinstance(e.body, dict):
            err_data = e.body.get("error", {})
            if isinstance(err_data, dict):
                metadata = err_data.get("metadata", {})
                if isinstance(metadata, dict):
                    retry_sec = metadata.get("retry_after_seconds")
                    if retry_sec is not None:
                        return float(retry_sec)
    except Exception:
        pass

    try:
        err_str = str(e)
        match = re.search(r"['\"]?retry_after_seconds['\"]?\s*[:=]\s*['\"]?([0-9]+(?:\.[0-9]+)?)", err_str)
        if match:
            return float(match.group(1))
        match_hdr = re.search(r"['\"]?Retry-After['\"]?\s*[:=]\s*['\"]?([0-9]+(?:\.[0-9]+)?)", err_str)
        if match_hdr:
            return float(match_hdr.group(1))
    except Exception:
        pass

    return default_wait


class ServiceBot:
    def __init__(self, api_key: str, model: str, status_callback=None):
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key,
        )
        self.model = model
        self.status_callback = status_callback
        self.messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        self.greeted = False

    def get_greeting(self) -> str:
        return self.chat("Hello, who are you?")

    def get_closing(self) -> str:
        return (
            "Thank you for chatting with NexSupport! If you ever need help "
            "with your banking needs again, I'm just a message away. "
            "Have a great day!"
        )

    def chat(self, message: str) -> str:
        self.messages.append({"role": "user", "content": message})

        models_to_try = [self.model]
        for fb_model in FALLBACK_MODELS:
            if fb_model not in models_to_try:
                models_to_try.append(fb_model)

        current_model_idx = 0
        max_retries_per_model = 2

        while current_model_idx < len(models_to_try):
            active_model = models_to_try[current_model_idx]
            retries = 0

            while retries <= max_retries_per_model:
                try:
                    response = self.client.chat.completions.create(
                        model=active_model,
                        messages=self.messages,
                        temperature=0.7,
                        max_tokens=1024,
                    )

                    reply = response.choices[0].message.content
                    self.messages.append({"role": "assistant", "content": reply})

                    if active_model != self.model:
                        if self.status_callback:
                            self.status_callback(f"Successfully fell back to model: {active_model}")
                        self.model = active_model

                    return reply

                except Exception as e:
                    err_str = str(e)
                    is_rate_limit = False

                    if "429" in err_str or "rate-limited" in err_str.lower() or "rate_limit" in err_str.lower():
                        is_rate_limit = True

                    if is_rate_limit:
                        retry_after = _extract_retry_after(e)
                        retries += 1

                        if retries <= max_retries_per_model:
                            if retry_after <= 10.0:
                                if self.status_callback:
                                    self.status_callback(
                                        f"Model '{active_model}' is temporarily rate-limited. "
                                        f"Retrying in {retry_after:.1f}s (Attempt {retries}/{max_retries_per_model})..."
                                    )
                                time.sleep(retry_after)
                                continue
                            else:
                                if self.status_callback:
                                    self.status_callback(
                                        f"Model '{active_model}' has a long rate-limit wait ({retry_after:.1f}s). "
                                        f"Skipping to fallback model..."
                                    )
                                break
                        else:
                            if self.status_callback:
                                self.status_callback(
                                    f"Model '{active_model}' rate limit retries exhausted. "
                                    f"Skipping to fallback model..."
                                )
                            break
                    else:
                        is_provider_err = any(word in err_str.lower() for word in ["provider", "500", "502", "503", "504", "gateway", "server error"])
                        if is_provider_err:
                            if self.status_callback:
                                self.status_callback(
                                    f"Model '{active_model}' hit provider/server error. "
                                    f"Skipping to fallback model..."
                                )
                            break
                        else:
                            return f"I'm sorry, I ran into an error: {e}"

            current_model_idx += 1

        return "I'm sorry, all tried models (including fallbacks) are currently unavailable or rate-limited. Please try again in a few moments."
