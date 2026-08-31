from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render


def _attend_du_html(request):
    """Un navigateur demande du HTML, un client API non."""
    return "text/html" in request.headers.get("Accept", "")


def page_not_found(request, exception=None):
    """
    Handler 404 global.
    Remplace la page technique de Django qui listait toutes les routes.
    """
    if _attend_du_html(request):
        return render(request, "404.html", {"site_url": settings.SITE_BASE_URL}, status=404)
    return JsonResponse({"detail": "Not found"}, status=404)
