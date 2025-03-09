from rest_framework.permissions import BasePermission

class CountryCodePermission(BasePermission):
    """
    Vérifie et ajoute le code pays à la requête.
    """
    def has_permission(self, request, view):
        # Récupérer le header X-Country-Code
        country_code = request.headers.get("X-Country-Code")

        # Stocker la valeur dans l'objet request
        request.country_code = country_code
        
        # Optionnel : bloquer les requêtes sans ce header
        if not country_code:
            return False  # Refuse l'accès si le header est manquant

        return True  # Autorise la requête
