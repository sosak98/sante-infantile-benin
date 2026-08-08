import logging
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client
except Exception:
    Client = None


def send_sms(phone: str, message: str) -> bool:
    """
    Envoie un SMS via Twilio si configuré, sinon journalise le message (mode développement).
    Retourne True si l'envoi a été tenté.
    """
    # Préférence: Twilio (env vars TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM)
    sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    from_number = getattr(settings, 'TWILIO_FROM', None)

    if sid and token and from_number and Client is not None:
        try:
            client = Client(sid, token)
            client.messages.create(body=message, from_=from_number, to=phone)
            return True
        except Exception as e:
            logger.exception('Erreur en envoyant le SMS via Twilio')
            return False

    # Fallback: console/log mode
    logger.info('SMS fallback: to=%s message=%s', phone, message)
    return True
