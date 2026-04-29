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