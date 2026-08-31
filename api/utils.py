from django.core.signing import TimestampSigner, BadSignature, SignatureExpired

signer = TimestampSigner(salt="pickup-view-safar")


def generate_pickup_token(livraison_id: int) -> str:
    """Génère un token signé à partir du livraison_id"""
    return signer.sign(livraison_id)


def verify_pickup_token(token: str, max_age_days: int = 30):
    """
    Vérifie le token et retourne le livraison_id.
    Lève SignatureExpired ou BadSignature si invalide.
    """
    return signer.unsign(token, max_age=60 * 60 * 24 * max_age_days)

# --- Jeton de session compte client (etapes 2 et 3 du nouveau flux OTP) ---
# Signe avec la SECRET_KEY, donc infalsifiable et sans stockage en base :
# ListeClient est une table Odoo (managed = False), on ne peut pas y ajouter
# de colonne token.

ACCOUNT_TOKEN_MAX_AGE_DAYS = 7

account_signer = TimestampSigner(salt="account-session-safar")


def generate_account_token(client_id: int) -> str:
    """Genere un token signe portant le client_id, valable 7 jours."""
    return account_signer.sign(str(client_id))


def verify_account_token(token: str, max_age_days: int = ACCOUNT_TOKEN_MAX_AGE_DAYS) -> int:
    """
    Verifie le token et retourne le client_id qu'il contient.
    Leve SignatureExpired (perime) ou BadSignature (invalide ou falsifie).
    """
    return int(account_signer.unsign(token, max_age=60 * 60 * 24 * max_age_days))
