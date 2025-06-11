import os
import requests
import logging
from datetime import datetime, timezone
from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse, parse_qs

# ——— konfiguracja loggera ———
_LOG_FILE = "payu_service.log"
logger = logging.getLogger("payu_service")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(_LOG_FILE, encoding="utf-8")
fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))
logger.addHandler(fh)

# etykiety logów
_LOG_REQ      = "→ PAYU AUTH REQUEST"
_LOG_RES      = "← PAYU AUTH RESPONSE"
_LOG_ORD_REQ  = "→ PAYU ORDER REQUEST"
_LOG_ORD_RES  = "← PAYU ORDER RESPONSE"
_LOG_URL      = "  URL:    "
_LOG_HEADERS  = "  HEADERS:"
_LOG_BODY     = "  BODY:   "
_LOG_STATUS   = "  STATUS: "
_LOG_TEXT     = "  TEXT:   "

# nagłówki i typy treści
_CONTENT_TYPE_FORM = "application/x-www-form-urlencoded"
_CONTENT_TYPE_JSON = "application/json"
_ACCEPT_JSON       = _CONTENT_TYPE_JSON

# konfiguracja z .env
CLIENT_ID     = os.getenv("PAYU_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("PAYU_CLIENT_SECRET", "")
POS_ID        = os.getenv("PAYU_POS_ID", "")
OAUTH_URL     = os.getenv("PAYU_OAUTH_URL", "https://secure.snd.payu.com/pl/standard/user/oauth/authorize")
API_URL       = os.getenv("PAYU_API_URL",   "https://secure.snd.payu.com/api/v2_1/orders")
NOTIFY_URL    = os.getenv("PAYU_NOTIFY_URL", "")

def _get_access_token() -> str:
    headers = {"Content-Type": _CONTENT_TYPE_FORM, "Accept": _ACCEPT_JSON}
    data = {"grant_type": "client_credentials"}
    auth = HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)

    logger.debug(_LOG_REQ)
    logger.debug(_LOG_URL + repr(OAUTH_URL))
    logger.debug(_LOG_HEADERS + str(headers))
    logger.debug(_LOG_BODY + str(data))

    resp = requests.post(
        OAUTH_URL,
        auth=auth,
        data=data,
        headers=headers,
        timeout=10,
        allow_redirects=False
    )

    logger.debug(_LOG_RES)
    logger.debug(_LOG_STATUS + str(resp.status_code))
    logger.debug(_LOG_HEADERS + str(dict(resp.headers)))
    logger.debug(_LOG_TEXT + resp.text[:500] + "…")

    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type", "")
    if _ACCEPT_JSON not in content_type:
        raise RuntimeError(f"Oczekiwano JSON z PayU auth, otrzymano {content_type!r}")

    try:
        payload = resp.json()
    except ValueError:
        raise RuntimeError(f"Niepoprawny JSON od PayU auth: {resp.text!r}")

    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"Brak access_token w odpowiedzi PayU: {payload}")
    return token


def create_payu_order(
    invoice_id: int,
    amount: float,
    buyer_email: str,
    buyer_name: str
) -> dict:
    """
    Tworzy zamówienie w PayU sandbox. Zwraca JSON lub parametry przekierowania płatności.
    """
    token = _get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  _CONTENT_TYPE_JSON,
        "Accept":        _ACCEPT_JSON,
    }

    ext_id = f"{invoice_id}_{int(datetime.now(timezone.utc).timestamp())}"
    body = {
        "notifyUrl":     NOTIFY_URL,
        "customerIp":    "127.0.0.1",
        "merchantPosId": POS_ID,
        "description":   f"Invoice #{invoice_id}",
        "currencyCode":  "PLN",
        "totalAmount":   str(int(amount * 100)),
        "extOrderId":    ext_id,
        "buyer": {
            "email":     buyer_email,
            "firstName": buyer_name.split()[0],
            "lastName":  buyer_name.split()[-1]
        },
        "products": [{
            "name":      f"Invoice #{invoice_id}",
            "unitPrice": str(int(amount * 100)),
            "quantity":  "1"
        }]
    }

    logger.debug(_LOG_ORD_REQ)
    logger.debug(_LOG_URL + repr(API_URL))
    logger.debug(_LOG_HEADERS + str(headers))
    logger.debug(_LOG_BODY + str(body))

    resp = requests.post(
        API_URL,
        json=body,
        headers=headers,
        timeout=10,
        allow_redirects=False
    )

    logger.debug(_LOG_ORD_RES)
    logger.debug(_LOG_STATUS + str(resp.status_code))
    logger.debug(_LOG_HEADERS + str(dict(resp.headers)))
    logger.debug(_LOG_TEXT + resp.text[:500] + "…")

    # obsługa przekierowania do płatności (HTTP 302)
    if resp.status_code in (301, 302):
        location = resp.headers.get("Location")
        qs = parse_qs(urlparse(location).query)
        order_id = qs.get("orderId", [None])[0]
        if not order_id:
            raise RuntimeError(f"Nie znaleziono orderId w przekierowaniu: {location}")
        logger.info(f"PayU zwrócił URL do płatności: {location}")
        return {"orderId": order_id, "redirectUri": location}

    # sprawdzenie JSON
    content_type = resp.headers.get("Content-Type", "")
    if _ACCEPT_JSON not in content_type:
        raise RuntimeError(f"Oczekiwano JSON od PayU, otrzymano {content_type!r}")

    resp.raise_for_status()
    try:
        return resp.json()
    except ValueError:
        raise RuntimeError(f"PayU zwróciło nie-JSON: {resp.text!r}")
