import re


PLACEHOLDER_THREAD_NAMES = {"create_fmea", "chat_db"}
MAX_TITLE_WORDS = 8
MAX_TITLE_LENGTH = 80

_PREFIX_PATTERNS = [
    re.compile(r"^(please\s+)?(help me\s+)?(create|generate|build)\s+an?\s+fmea\s+(for|about)\s+", re.IGNORECASE),
    re.compile(r"^(please\s+)?(i am|i'm|we are|we're)\s+(designing|building|working on)\s+", re.IGNORECASE),
    re.compile(r"^(please\s+)?(can you|could you|would you|will you)\s+", re.IGNORECASE),
    re.compile(r"^(please\s+)?(tell me about|explain|describe|summarize|help me understand)\s+", re.IGNORECASE),
    re.compile(r"^(please\s+)?(what is|what are|how does|how do)\s+", re.IGNORECASE),
]


def should_replace_thread_name(current_name):
    if current_name is None:
        return True

    normalized = _normalize_whitespace(str(current_name)).lower()
    return not normalized or normalized in PLACEHOLDER_THREAD_NAMES


def build_chat_title(message_content, max_words=MAX_TITLE_WORDS, max_length=MAX_TITLE_LENGTH):
    if not message_content:
        return None

    cleaned = _clean_message_seed(message_content)
    if not cleaned:
        return None

    trimmed = _trim_to_sentence(cleaned)
    stripped = _strip_prefixes(trimmed)
    candidate = stripped or trimmed

    words = candidate.split()
    if len(words) > max_words:
        candidate = " ".join(words[:max_words])

    candidate = candidate.strip(" -:;,.!?\"'`()[]{}")
    if not candidate:
        return None

    if len(candidate) > max_length:
        candidate = candidate[:max_length].rstrip()
        if " " in candidate:
            candidate = candidate.rsplit(" ", 1)[0]

    if candidate and candidate[0].islower():
        candidate = candidate[0].upper() + candidate[1:]

    return candidate or None


def _clean_message_seed(text):
    text = text.replace("`", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_whitespace(text):
    return re.sub(r"\s+", " ", text).strip()


def _trim_to_sentence(text):
    parts = re.split(r"[\n\r]+|(?<=[.!?])\s+", text, maxsplit=1)
    return parts[0].strip()


def _strip_prefixes(text):
    candidate = text.strip()
    previous = None

    while candidate and candidate != previous:
        previous = candidate
        for pattern in _PREFIX_PATTERNS:
            candidate = pattern.sub("", candidate, count=1).strip()

    return candidate
