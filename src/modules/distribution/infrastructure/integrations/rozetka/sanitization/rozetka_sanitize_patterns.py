"""Compiled regex patterns for Rozetka offer sanitization.

Each pattern has a comment explaining what it matches.
"""
import re


# Matches http:// or https:// URLs, and www. prefixed URLs
RE_URL = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

# Matches phone numbers in various formats: +380 (44) 123-4567, 044-123-45-67, etc.
# Optional country code (+1-3 digits), optional area code in parens, groups of 2-4 digits
RE_PHONE = re.compile(
    r"(?:\+?\d{1,3}[\s\-]?)?\(?\d{2,4}\)?[\s\-]?\d{2,4}[\s\-]?\d{2,4}[\s\-]?\d{0,4}"
)

# Matches email addresses: word chars, dots, +, - before @, domain after
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

# Matches common Unicode emoji ranges (emoticons, symbols, flags, dingbats, etc.)
RE_EMOJI = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # misc symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"  # dingbats
    "\U0000FE00-\U0000FE0F"  # variation selectors
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols extended-A
    "\U00002600-\U000026FF"  # misc symbols (sun, cloud, etc.)
    "\U0000200D"             # zero-width joiner (used in combined emoji)
    "\U00002B50"             # star
    "\U00002764"             # heart
    "]+",
    flags=re.UNICODE,
)

# Ukrainian stop phrases forbidden in Rozetka descriptions
_STOP_PHRASES = [
    r"точк[аи] видачі",                                         # pickup points
    r"умови? (?:оформлення|замовлення|доставк[иі]|оплат[иі])",  # order/delivery/payment terms
    r"(?:безкоштовн[аі]|безплатн[аі]) доставк[аі]",             # free delivery
    r"(?:ТОВ|ФОП|ЛТД|ТМ)\s",                                    # company legal forms
    r"гарантія повернення",                                       # return guarantee
    r"зателефонуйте",                                             # "call us"
    r"зв['ʼ]яжіться з нами",                                     # "contact us"
]
# Combined pattern matching any of the stop phrases above (case-insensitive)
RE_STOP_PHRASES = re.compile("|".join(_STOP_PHRASES), re.IGNORECASE)

# Matches forbidden punctuation in product names: quotes, guillemets, parentheses
RE_NAME_FORBIDDEN = re.compile(r'["\u00ab\u00bb\u201c\u201d\u201e()]')

# Matches template placeholders like {field_name} or {param:Param Name}
RE_TEMPLATE_PLACEHOLDER = re.compile(r"\{([^}]+)\}")
