import re
import json
from user_agents import parse
from geoip2 import database
from django.conf import settings

class ClientInfoExtractor:
    """
    Classe pour extraire et formater les informations détaillées du client
    """
    
    def __init__(self, request):
        self.request = request
        self.meta = request.META
        
    def get_real_ip(self):
        """
        Récupère l'IP réelle du client en tenant compte des proxies/CDN
        """
        # Liste des headers possibles pour l'IP réelle (par ordre de priorité)
        ip_headers = [
            'HTTP_CF_CONNECTING_IP',      # Cloudflare
            'HTTP_X_REAL_IP',              # Nginx proxy
            'HTTP_X_FORWARDED_FOR',        # Standard proxy
            'HTTP_X_FORWARDED',            # Variation
            'HTTP_FORWARDED_FOR',          # Variation
            'HTTP_FORWARDED',              # RFC 7239
            'REMOTE_ADDR',                 # IP directe
        ]
        
        for header in ip_headers:
            ip = self.meta.get(header)
            if ip:
                # Si plusieurs IPs (format: "client, proxy1, proxy2")
                if ',' in ip:
                    ip = ip.split(',')[0].strip()
                
                # Validation de l'IP
                if self._is_valid_ip(ip):
                    return ip
        
        return 'IP non disponible'
    
    def _is_valid_ip(self, ip):
        """
        Valide le format d'une adresse IP (IPv4 ou IPv6)
        """
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){7}[0-9a-fA-F]{0,4}$'
        
        if re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip):
            return True
        return False
    
    def get_user_agent_details(self):
        """
        Parse le User-Agent pour extraire des informations détaillées
        """
        user_agent_string = self.meta.get('HTTP_USER_AGENT', '')
        
        try:
            user_agent = parse(user_agent_string)
            
            return {
                'raw': user_agent_string,
                'browser': {
                    'name': user_agent.browser.family,
                    'version': user_agent.browser.version_string,
                },
                'os': {
                    'name': user_agent.os.family,
                    'version': user_agent.os.version_string,
                },
                'device': {
                    'type': self._get_device_type(user_agent),
                    'brand': user_agent.device.brand or 'Inconnu',
                    'model': user_agent.device.model or 'Inconnu',
                },
                'is_mobile': user_agent.is_mobile,
                'is_tablet': user_agent.is_tablet,
                'is_pc': user_agent.is_pc,
                'is_bot': user_agent.is_bot,
            }
        except Exception as e:
            return {
                'raw': user_agent_string,
                'error': str(e),
                'browser': {'name': 'Inconnu', 'version': ''},
                'os': {'name': 'Inconnu', 'version': ''},
                'device': {'type': 'Inconnu', 'brand': '', 'model': ''},
                'is_mobile': False,
                'is_tablet': False,
                'is_pc': False,
                'is_bot': False,
            }
    
    def _get_device_type(self, user_agent):
        """
        Détermine le type d'appareil
        """
        if user_agent.is_mobile:
            return 'Mobile'
        elif user_agent.is_tablet:
            return 'Tablette'
        elif user_agent.is_pc:
            return 'Ordinateur'
        elif user_agent.is_bot:
            return 'Bot'
        return 'Inconnu'
    
    def get_location_info(self):
        """
        Récupère les informations de géolocalisation basées sur l'IP
        """
        ip = self.get_real_ip()
        
        # Informations depuis les headers CDN (Cloudflare, etc.)
        cloudflare_country = self.meta.get('HTTP_CF_IPCOUNTRY')
        cloudflare_city = self.meta.get('HTTP_CF_IPCITY')
        country_code = self.meta.get('HTTP_X_COUNTRY_CODE')
        
        location = {
            'ip': ip,
            'country_code': cloudflare_country or country_code or 'Inconnu',
            'country_name': self._get_country_name(cloudflare_country or country_code),
            'city': cloudflare_city or 'Non disponible',
            'timezone': self.meta.get('HTTP_CF_TIMEZONE', 'Non disponible'),
        }
        
        return location
    
    def _get_country_name(self, country_code):
        """
        Convertit le code pays en nom complet
        """
        countries = {
            'DZ': 'Algérie',
            'FR': 'France',
            'MA': 'Maroc',
            'TN': 'Tunisie',
            'US': 'États-Unis',
            'GB': 'Royaume-Uni',
            'DE': 'Allemagne',
            'ES': 'Espagne',
            'IT': 'Italie',
            'CA': 'Canada',
            # Ajoutez plus de pays selon vos besoins
        }
        return countries.get(country_code, country_code if country_code else 'Inconnu')
    
    def get_request_info(self):
        """
        Récupère les informations générales de la requête
        """
        return {
            'method': self.request.method,
            'path': self.request.path,
            'referer': self.meta.get('HTTP_REFERER', 'Accès direct'),
            'accept_language': self.meta.get('HTTP_ACCEPT_LANGUAGE', 'Non disponible'),
            'accept_encoding': self.meta.get('HTTP_ACCEPT_ENCODING', 'Non disponible'),
            'connection': self.meta.get('HTTP_CONNECTION', 'Non disponible'),
            'protocol': self.meta.get('SERVER_PROTOCOL', 'HTTP/1.1'),
        }
    
    def get_security_info(self):
        """
        Informations de sécurité et détection
        """
        user_agent_details = self.get_user_agent_details()
        
        return {
            'is_bot': user_agent_details.get('is_bot', False),
            'is_secure': self.request.is_secure(),
            'dnsmbl_listed': False,  # Vous pouvez implémenter une vérification DNSBL
            'proxy_detected': self._detect_proxy(),
            'vpn_suspected': self._detect_vpn(),
        }
    
    def _detect_proxy(self):
        """
        Détecte si la requête passe par un proxy
        """
        proxy_headers = [
            'HTTP_VIA',
            'HTTP_X_FORWARDED_FOR',
            'HTTP_FORWARDED_FOR',
            'HTTP_X_FORWARDED',
            'HTTP_FORWARDED',
            'HTTP_CLIENT_IP',
            'HTTP_FORWARDED_FOR_IP',
        ]
        
        for header in proxy_headers:
            if self.meta.get(header):
                return True
        return False
    
    def _detect_vpn(self):
        """
        Détection basique de VPN (à améliorer avec des services tiers)
        """
        # Détection basique basée sur des patterns communs
        ip = self.get_real_ip()
        user_agent = self.meta.get('HTTP_USER_AGENT', '').lower()
        
        vpn_patterns = ['vpn', 'proxy', 'tor']
        
        for pattern in vpn_patterns:
            if pattern in user_agent:
                return True
        
        return False
    
    def get_complete_info(self):
        """
        Retourne toutes les informations dans un dictionnaire structuré
        """
        user_agent_details = self.get_user_agent_details()
        location_info = self.get_location_info()
        request_info = self.get_request_info()
        security_info = self.get_security_info()
        
        return {
            'ip': location_info['ip'],
            'location': location_info,
            'user_agent': user_agent_details,
            'request': request_info,
            'security': security_info,
            'timestamp': self.request.META.get('HTTP_DATE', ''),
        }
    
    def format_for_display(self):
        """
        Formate les informations pour un affichage lisible
        """
        info = self.get_complete_info()
        
        display = f"""
╔══════════════════════════════════════════════════════════════════╗
║                  INFORMATIONS CLIENT DÉTAILLÉES                  ║
╠══════════════════════════════════════════════════════════════════╣
║ 🌐 LOCALISATION                                                  ║
║    IP Address      : {info['ip']:<45} ║
║    Pays           : {info['location']['country_name']:<45} ║
║    Code Pays      : {info['location']['country_code']:<45} ║
║    Ville          : {info['location']['city']:<45} ║
║    Fuseau Horaire : {info['location']['timezone']:<45} ║
╠══════════════════════════════════════════════════════════════════╣
║ 💻 APPAREIL                                                      ║
║    Type           : {info['user_agent']['device']['type']:<45} ║
║    Marque         : {info['user_agent']['device']['brand']:<45} ║
║    Modèle         : {info['user_agent']['device']['model']:<45} ║
║    Mobile         : {'Oui' if info['user_agent']['is_mobile'] else 'Non':<45} ║
║    Tablette       : {'Oui' if info['user_agent']['is_tablet'] else 'Non':<45} ║
╠══════════════════════════════════════════════════════════════════╣
║ 🌐 NAVIGATEUR                                                    ║
║    Nom            : {info['user_agent']['browser']['name']:<45} ║
║    Version        : {info['user_agent']['browser']['version']:<45} ║
╠══════════════════════════════════════════════════════════════════╣
║ 🖥️  SYSTÈME D'EXPLOITATION                                       ║
║    OS             : {info['user_agent']['os']['name']:<45} ║
║    Version        : {info['user_agent']['os']['version']:<45} ║
╠══════════════════════════════════════════════════════════════════╣
║ 🔗 REQUÊTE                                                       ║
║    Méthode        : {info['request']['method']:<45} ║
║    Chemin         : {info['request']['path']:<45} ║
║    Referer        : {info['request']['referer'][:45]:<45} ║
║    Langue         : {info['request']['accept_language'][:45]:<45} ║
║    Protocole      : {info['request']['protocol']:<45} ║
╠══════════════════════════════════════════════════════════════════╣
║ 🔒 SÉCURITÉ                                                      ║
║    Bot Détecté    : {'Oui ⚠️' if info['security']['is_bot'] else 'Non ✓':<45} ║
║    Connexion HTTPS: {'Oui ✓' if info['security']['is_secure'] else 'Non ⚠️':<45} ║
║    Proxy Détecté  : {'Oui ⚠️' if info['security']['proxy_detected'] else 'Non ✓':<45} ║
║    VPN Suspecté   : {'Oui ⚠️' if info['security']['vpn_suspected'] else 'Non ✓':<45} ║
╚══════════════════════════════════════════════════════════════════╝
        """
        
        return display.strip()
    
    def get_json_summary(self):
        """
        Retourne un résumé JSON compact pour stockage en base de données
        """
        info = self.get_complete_info()
        
        return json.dumps({
            'ip': info['ip'],
            'country': info['location']['country_code'],
            'city': info['location']['city'],
            'device': info['user_agent']['device']['type'],
            'browser': f"{info['user_agent']['browser']['name']} {info['user_agent']['browser']['version']}",
            'os': f"{info['user_agent']['os']['name']} {info['user_agent']['os']['version']}",
            'is_mobile': info['user_agent']['is_mobile'],
            'is_bot': info['security']['is_bot'],
            'referer': info['request']['referer'],
        }, ensure_ascii=False)