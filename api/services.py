from .models import *
from datetime import datetime
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import make_aware
from datetime import datetime, time
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from decimal import Decimal
import random
from django.db.models import F
from django.db.models import Min
from django.utils.html import strip_tags
from django.template.loader import render_to_string
import re
from django.utils.timezone import now
from django.utils import timezone
from django.utils.dateparse import parse_datetime


def vip_reduction(country_code):
    try :
        moins_cher = []
        records = (
            Tarifs.objects.order_by("prix")
            .values("modele")
            .annotate(min_prix=Min("prix"))
            .order_by("min_prix")[:3]
        )
        vip = CategorieClient.objects.filter(name="VIP").first()
        taux = TauxChange.objects.filter(id=2).first()
        taux_change = taux.montant
        pourcentage = vip.reduction
        for record in records :
            model_id = record.get("modele")
            prix = record.get("min_prix") * taux_change if country_code == "DZ" else record.get("min_prix")
            final_prix = prix - (prix * pourcentage / 100 )
            modele = Modele.objects.filter(id=model_id).first()
            moins_cher.append({
                "currency": "DZ" if country_code == "DZ" else "EUR",
                "model_name":modele.name,
                "model_prix":final_prix,
                "marketing_text_fr":modele.marketing_text_fr,
                "nombre_de_place":modele.nombre_deplace,
                "nombre_de_bagages":modele.nombre_de_bagage,
                "boite_vitesse":modele.boite_vitesse,
                "type_carburant":modele.carburant,
                "photo_link":modele.photo_link,
                "sticker":modele.stickers
            })

        
        return moins_cher
    
    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}

def protections(ref, email, country_code):
    """
    Retourne un dict de protections indexé par clefs:
      - selected (nom de la protection choisie)
      - basic, standard, maximum (détails prix/total/caution)
    Application du taux DZ si nécessaire.
    """
    try:
        reservation = Reservation.objects.filter(name=ref, email=email).first()
        if not reservation:
            return {}

        nb_jour     = reservation.nbr_jour_reservation or 0
        category_id = getattr(reservation.categorie, "id", None)
        zone_id     = getattr(reservation.zone, "id", None)
        selected    = reservation.opt_protection_name or ""

        # Taux de change
        country_upper = (country_code or "").upper()
        taux_change = 1
        if country_upper == "DZ":
            taux = TauxChange.objects.filter(id=2).first()
            taux_change = getattr(taux, "montant", 1)

        # Recherche des protections
        protections_qs = Options.objects.filter(
            (Q(option_code__icontains="BASE")   |
             Q(option_code__icontains="STANDAR")|
             Q(option_code__icontains="MAX"))
            &
            (Q(categorie__id=category_id) | Q(categorie=None))
            &
            Q(zone__id=zone_id)
        )

        # Prépare le résultat
        result = {
            "selected": selected,
            "basic":    None,
            "standard": None,
            "maximum":  None,
        }

        for prot in protections_qs:
            name_l = (prot.name or "").lower()
            prix   = (prot.prix or 0) * taux_change

            item = {
                "protection_name":  prot.name,
                "protection_prix":  prix,
                "protection_total": prix * nb_jour,
                "protection_caution": (prot.caution or 0) * taux_change,
            }

            if "bas" in name_l:
                result["basic"]    = item
            elif "standar" in name_l:  # couvre "standard" et éventuelle typo "standart"
                result["standard"] = item
            elif "max" in name_l:
                result["maximum"]  = item

        return result

    except Exception:
        # Remonte l'exception pour qu'elle soit gérée dans la vue
        raise

def modify_protection_request(ref, protection,country_code):
    try:   
        reservation = Reservation.objects.filter(name=ref).first()
        lieu_depart_obj = reservation.lieu_depart
        nb_jour = reservation.nbr_jour_reservation
        category = reservation.categorie.id

        taux_change = TauxChange.objects.filter(id=2).first()
        taux = taux_change.montant if country_code == "DZ" else 1
        
        if reservation :
            if protection == "BASE":
                opt_protection = Options.objects.filter(option_code__icontains="BASE", categorie_id=category, zone= lieu_depart_obj.zone).first()
                prix = opt_protection.prix
                total = prix * nb_jour

                if total > reservation.opt_protection_total:
                    total_pay = total - reservation.opt_protection_total
                    if not reservation.opt_payment_name:
                        return {
                            "currency":"DA" if country_code == "DZ" else "EUR",
                            "new_protection_price":prix * taux,
                            "new_protection_total":total * taux,
                            "to_pay":total_pay * taux
                            }
                    else:
                        return {
                            "currency":"DA" if country_code == "DZ" else "EUR",
                            "new_protection_price":prix * taux,
                            "new_protection_total":total * taux,
                            }
                else : 
                    to_refund = reservation.opt_protection_total - total
                    if not reservation.opt_payment_name:
                        return {
                            "currency":"DA" if country_code == "DZ" else "EUR",
                            "new_protection_price":prix * taux,
                            "new_protection_total":total * taux,
                            "to_refund":to_refund * taux
                            }
                    else:
                        return {
                            "currency":"DA" if country_code == "DZ" else "EUR",
                            "new_protection_price":prix * taux,
                            "new_protection_total":total * taux,
                            }
                    
            elif protection == "STANDART":
                opt_protection = Options.objects.filter(option_code__icontains="STANDART", categorie_id=category, zone= lieu_depart_obj.zone).first()
                prix = opt_protection.prix
                total = prix * nb_jour

                if total > reservation.opt_protection_total:
                    total_pay = total - reservation.opt_protection_total
                    if not reservation.opt_payment_name:
                        return {
                            "currency":"DA" if country_code == "DZ" else "EUR",
                            "new_protection_price":prix * taux,
                            "new_protection_total":total * taux,
                            "to_pay":total_pay * taux
                            }
                    else:
                        return {
                            "currency":"DA" if country_code == "DZ" else "EUR",
                            "new_protection_price":prix * taux,
                            "new_protection_total":total * taux,
                            }
                else : 
                    to_refund = reservation.opt_protection_total - total
                    if not reservation.opt_payment_name:
                        return {
                            "currency":"DA" if country_code == "DZ" else "EUR",
                            "new_protection_price":prix * taux,
                            "new_protection_total":total * taux,
                            "to_refund":to_refund * taux
                            }
                    else:
                        return {
                            "currency":"DA" if country_code == "DZ" else "EUR",
                            "new_protection_price":prix * taux,
                            "new_protection_total":total * taux,
                            }
                    
            elif protection == "MAX":
                opt_protection = Options.objects.filter(option_code__icontains="MAX", categorie_id=category, zone= lieu_depart_obj.zone).first()
                prix = opt_protection.prix
                total = prix * nb_jour

                if total > reservation.opt_protection_total:
                    total_pay = total - reservation.opt_protection_total
                    if not reservation.opt_payment_name:
                        return {
                            "currency":"DA" if country_code == "DZ" else "EUR",
                            "new_protection_price":prix * taux,
                            "new_protection_total":total * taux,
                            "to_pay":total_pay * taux
                            }
                    else:
                        return {
                            "currency":"DA" if country_code == "DZ" else "EUR",
                            "new_protection_price":prix * taux,
                            "new_protection_total":total * taux,
                            }
                else : 
                    to_refund = reservation.opt_protection_total - total
                    if not reservation.opt_payment_name:
                        return {
                            "currency":"DA" if country_code == "DZ" else "EUR",
                            "new_protection_price":prix * taux,
                            "new_protection_total":total * taux,
                            "to_refund":to_refund * taux
                            }
                    else:
                        return {
                            "currency":"DA" if country_code == "DZ" else "EUR",
                            "new_protection_price":prix * taux,
                            "new_protection_total":total * taux,
                            }
                    
            else : 
                return {"message": "pas possible de modifier"}
        
        else : 
                return {"message": "pas possible de modifier"}

    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}

def verify_client(email, nom, prenom, birthday, permis, phone):
    try:
        nom = re.sub(r'\s+', ' ', nom.strip()).upper()
        prenom = re.sub(r'\s+', ' ', prenom.strip()).upper()
        client_id=ListeClient.objects.filter(nom=nom, prenom=prenom).first()
        if client_id :
            if client_id.risque == "eleve":
                return {"message":"negatif"}
            else :
                
                return {"message":"positif", "client_id": client_id.id}

        else :
            client_verify=ListeClient.objects.filter(nom=prenom, prenom=nom).first()
            if client_verify:
                if client_verify.risque == "eleve":
                    return {"message":"negatif"}
                else :
                    return {"message":"positif", "client_id": client_verify.id}
            else: 
                client = create_account(email=email,
                                        nom=nom, 
                                        prenom=prenom, 
                                        birthday=birthday, 
                                        permis_date=permis, 
                                        phone=phone)
                return {"message":"positif", "client_id": client.get("client_id") if client.get("client_id") else None}

    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}

def new_models():
    try:
        result = []
        modeles = Modele.objects.filter(stickers="new")
        if not modeles :
            modeles = Modele.objects.all().order_by('-create_date')[:3]
        for modele in modeles :
            result.append({
                "model_name": modele.name,
                "marketing_text_fr": modele.marketing_text_fr,
                "nbr_places": modele.nombre_deplace,
                "nbr_bagages": modele.nombre_de_bagage,
                "boite_vitesse": modele.boite_vitesse,
                "carburant": modele.carburant,
                "photo_link": modele.photo_link,
                "sticker": modele.stickers
            })

        return result

    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}


def add_options_request(ref, klm, nd_driver, carburant, sb_a, sb_b, sb_c, country_code):
    try:
        result = {}
        reservations = Reservation.objects.filter(name=ref).first()
        if not reservations:
            return {"message" : "pas de reservation avce cet id "}

        if reservations.client :
            free_options = free_options_f(reservations.client.id)

        to_pay_total = 0
        lieu_depart_obj = reservations.lieu_depart

        taux = TauxChange.objects.filter(id=2).first()
        taux_change = taux.montant

        result["currency"]="DA" if country_code == "DZ" else "EUR"

        if klm == "yes" and not reservations.opt_klm_name:
            klM_a = Options.objects.filter(option_code="KLM_ILLIMITED", zone= lieu_depart_obj.zone).first()
            klM_b = Options.objects.filter(option_code="KLM_ILLIMITED_B", zone= lieu_depart_obj.zone).first()
            klM_c = Options.objects.filter(option_code="KLM_ILLIMITED_C", zone= lieu_depart_obj.zone).first()   
            if klM_a.categorie == reservations.categorie :
                if free_options and free_options[0].get("option_seven") == True: 
                    klM_a_price = klM_a.prix * taux_change if country_code =="DZ" else klM_a.prix
                    klm_a_last_price = 0
                    klM_a_name = klM_a.name
                    klM_a_total = klM_a_price * reservations.nbr_jour_reservation
                    klm_a_last_total = 0
                    klm_result = {
                        "klm_name":klM_a_name,
                        "klM_price": klM_a_price,
                        "klM_last_price": klm_a_last_price,
                        "klM_total": klM_a_total,
                        "klM_last_total": klm_a_last_total,
                    }
                    result["klm"] = klm_result

                else : 
                    klM_a_price = klM_a.prix * taux_change if country_code =="DZ" else klM_a.prix
                    klM_a_name = klM_a.name
                    klM_a_total = klM_a_price * reservations.nbr_jour_reservation
                    to_pay_total += klM_a_total
                    klm_result = {
                        "klM_name":klM_a_name,
                        "klM_price": klM_a_price,
                        "klM_total": klM_a_total,
                    }
                    result["klm"] = klm_result

            elif klM_b.categorie == reservations.categorie :
                if free_options and free_options[0].get("option_seven") == True:
                    klM_b_price = klM_b.prix * taux_change if country_code=="DZ" else klM_b.prix
                    klm_b_last_price = 0
                    klM_b_name = klM_b.name
                    klM_b_total = klM_b_price * reservations.nbr_jour_reservation
                    klm_b_last_total = 0
                    klm_result = {
                        "klM_name":klM_b_name,
                        "klM_price": klM_b_price,
                        "klM_last_price": klm_b_last_price,
                        "klM_total": klM_b_total,
                        "klM_last_total": klm_b_last_total,
                    }
                    result["klm"] = klm_result
                else :
                    klM_b_price = klM_b.prix * taux_change if country_code=="DZ" else klM_b.prix
                    klM_b_name = klM_b.name
                    klM_b_total = klM_b_price * reservations.nbr_jour_reservation
                    to_pay_total += klM_b_total
                    klm_result = {
                        "klM_name":klM_b_name,
                        "klM_price": klM_b_price,
                        "klM_total": klM_b_total,
                    }
                    result["klm"] = klm_result
            elif klM_c.categorie == reservations.categorie :
                if free_options and free_options[0].get("option_seven") == True:
                    klM_c_price = klM_c.prix * taux_change if country_code=="DZ" else klM_c.prix
                    klm_c_last_price = 0
                    klM_c_name = klM_c.name
                    klM_c_total = klM_c_price * reservations.nbr_jour_reservation
                    klm_c_last_total = 0
                    klm_result = {
                        "klM_name":klM_c_name,
                        "klM_price": klM_c_price,
                        "klM_last_price": klm_c_last_price,
                        "klM_total": klM_c_total,
                        "klM_last_total": klm_c_last_total,
                    }
                    result["klm"] = klm_result
                else : 
                    klM_c_price = klM_c.prix * taux_change if country_code=="DZ" else klM_c.prix
                    klM_c_name = klM_c.name
                    klM_c_total = klM_c_price * reservations.nbr_jour_reservation
                    to_pay_total += klM_c_total
                    klm_result = {
                        "klM_name":klM_c_name,
                        "klM_price": klM_c_price,
                        "klM_total": klM_c_total,
                    }
                    result["klm"] = klm_result
            else :
                pass

        if nd_driver == "yes" and not reservations.opt_nd_driver_name:
            tarif_nd = Options.objects.filter(option_code="ND_DRIVER", zone= lieu_depart_obj.zone).first()
            if free_options and free_options[0].get("option_one") == True:
                nd_driver_price = tarif_nd.prix * taux_change if country_code=="DZ" else tarif_nd.prix
                nd_driver_last_price = 0
                nd_driver_name = tarif_nd.name
                nd_driver_total = nd_driver_price * reservations.nbr_jour_reservation
                nd_driver_last_total = 0
                nd_driver_result = {
                    "nd_driver_name":nd_driver_name,
                    "nd_driver_price": nd_driver_price,
                    "nd_driver_last_price": nd_driver_last_price,
                    "nd_driver_total": nd_driver_total,
                    "nd_driver_last_total": nd_driver_last_total,
                }
                result["nd_driver"] = nd_driver_result
            else :
                nd_driver_price = tarif_nd.prix * taux_change if country_code=="DZ" else tarif_nd.prix
                nd_driver_name = tarif_nd.name
                nd_driver_total = nd_driver_price * reservations.nbr_jour_reservation
                to_pay_total += nd_driver_total
                nd_driver_result = {
                    "nd_driver_name":nd_driver_name,
                    "nd_driver_price": nd_driver_price,
                    "nd_driver_total": nd_driver_total,
                }
                result["nd_driver"] = nd_driver_result

        if carburant == "yes" and not reservations.opt_plein_carburant_name:
            tarif_carburant = Options.objects.filter(option_code="P_CARBURANT", zone= lieu_depart_obj.zone).first()
            if free_options and free_options[0].get("option_two") == True:
                carburant = tarif_carburant.name
                carburant_price = tarif_carburant.prix * taux_change if country_code=="DZ" else tarif_carburant.prix
                carburant_last_price = 0
                carburant_total = carburant_price * reservations.nbr_jour_reservation
                carburant_last_total = 0
                carburant_result = {
                    "carburant_name": carburant,
                    "carburant_price": carburant_price,
                    "carburant_last_price": carburant_last_price,
                    "carburant_total": carburant_total,
                    "carburant_last_total": carburant_last_total,
                }
                result["carburant"] = carburant_result
            else :
                carburant = tarif_carburant.name
                carburant_price = tarif_carburant.prix * taux_change if country_code=="DZ" else tarif_carburant.prix
                carburant_total = carburant_price * reservations.nbr_jour_reservation
                to_pay_total += carburant_total
                carburant_result = {
                    "carburant_name": carburant,
                    "carburant_price": carburant_price ,
                    "carburant_total": carburant_total,
                }
                result["carburant"] = carburant_result

        if sb_a == "yes" and not reservations.opt_siege_a_name:
            tarif_sb_a = Options.objects.filter(option_code="S_BEBE_5", zone= lieu_depart_obj.zone).first()
            if free_options and free_options[0].get("option_three") == True:
                sb_a_name = tarif_sb_a.name
                sb_a_price = tarif_sb_a.prix * taux_change if country_code=="DZ" else tarif_sb_a.prix
                sb_a_last_price = 0
                sb_a_total = sb_a_price * reservations.nbr_jour_reservation
                sb_a_last_total = 0
                sb_a_result = {
                    "sb_a_name": sb_a_name,
                    "sb_a_price": sb_a_price,
                    "sb_a_last_price": sb_a_last_price,
                    "sb_a_total": sb_a_total,
                    "sb_a_last_total": sb_a_last_total,
                }
                result["sb_a"] = sb_a_result
            else :
                sb_a_name = tarif_sb_a.name
                sb_a_price = tarif_sb_a.prix * taux_change if country_code=="DZ" else tarif_sb_a.prix
                sb_a_total = sb_a_price * reservations.nbr_jour_reservation
                to_pay_total += sb_a_total
                sb_a_result = {
                    "sb_a_name": sb_a_name,
                    "sb_a_price": sb_a_price ,
                    "sb_a_total": sb_a_total,
                }
                result["sb_a"] = sb_a_result

        if sb_b == "yes" and not reservations.opt_siege_b_name:
            tarif_sb_b = Options.objects.filter(option_code="S_BEBE_13", zone= lieu_depart_obj.zone).first()
            if free_options and free_options[0].get("option_four") == True:
                sb_b_name = tarif_sb_b.name
                sb_b_price = tarif_sb_b.prix * taux_change if country_code=="DZ" else tarif_sb_b.prix
                sb_b_last_price = 0
                sb_b_total = sb_b_price * reservations.nbr_jour_reservation
                sb_b_last_total = 0
                sb_b_result = {
                    "sb_b_name": sb_b_name,
                    "sb_b_price": sb_b_price ,
                    "sb_b_last_price": sb_b_last_price ,
                    "sb_b_total": sb_b_total,
                    "sb_b_last_total": sb_b_last_total ,
                }
                result["sb_b"] = sb_b_result
            else : 
                sb_b_name = tarif_sb_b.name
                sb_b_price = tarif_sb_b.prix * taux_change if country_code=="DZ" else tarif_sb_b.prix
                sb_b_total = sb_b_price * reservations.nbr_jour_reservation
                to_pay_total += sb_b_total
                sb_b_result = {
                    "sb_b_name": sb_b_name,
                    "sb_b_price": sb_b_price ,
                    "sb_b_total": sb_b_total,
                }
                result["sb_b"] = sb_b_result

        if sb_c == "yes" and not reservations.opt_siege_c_name:
            tarif_sb_c = Options.objects.filter(option_code="S_BEBE_18", zone= lieu_depart_obj.zone).first()
            if free_options and free_options[0].get("option_five") == True:
                sb_c_name = tarif_sb_c.name
                sb_c_price = tarif_sb_c.prix * taux_change if country_code=="DZ" else tarif_sb_c.prix
                sb_c_last_price = 0
                sb_c_total = sb_c_price * reservations.nbr_jour_reservation
                sb_c_last_total = 0
                sb_c_result = {
                    "sb_c_name": sb_c_name,
                    "sb_c_price": sb_c_price ,
                    "sb_c_last_price": sb_c_last_price ,
                    "sb_c_total": sb_c_total,
                    "sb_c_last_total": sb_c_last_total,
                }
                result["sb_c"] = sb_c_result
            else : 
                sb_c_name = tarif_sb_c.name
                sb_c_price = tarif_sb_c.prix * taux_change if country_code=="DZ" else tarif_sb_c.prix
                sb_c_total = sb_c_price * reservations.nbr_jour_reservation
                to_pay_total += sb_c_total
                sb_c_result = {
                    "sb_c_name": sb_c_name,
                    "sb_c_price": sb_c_price ,
                    "sb_c_total": sb_c_total,
                }
                result["sb_c"] = sb_c_result
            
        if to_pay_total > 0 :
            result["total_price"] = to_pay_total
                
        return result
    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}

def mes_reservations(client_id,country_code):
    try:
        reservations = Reservation.objects.filter(client__id=client_id)
        if not reservations.exists():
            return {"message": "Aucune réservation trouvée pour ce client."}
        taux = TauxChange.objects.filter(id=2).first()
        taux_change = taux.montant
        result = []
        for reservation in reservations:
            can_be_modified = "yes"
            if reservation.status != "confirmee" :
                can_be_modified = "no"
            result.append({
                "currency":"DA" if country_code =="DZ" else "EUR",
                "id":reservation.id,
                "reference": reservation.name,
                "lieu_depart": reservation.lieu_depart.name,
                "lieu_depart_en": reservation.lieu_depart.name_en,
                "lieu_depart_ar": reservation.lieu_depart.name_ar,
                "lieu_retour": reservation.lieu_retour.name,
                "lieu_retour_en": reservation.lieu_retour.name_en,
                "lieu_retour_ar": reservation.lieu_retour.name_ar,
                "date_dapart": reservation.date_heure_debut,
                "date_retour": reservation.date_heure_fin,
                "duree": reservation.nbr_jour_reservation,
                "caution": reservation.opt_protection_caution * taux_change if country_code =="DZ" else reservation.opt_protection_caution,
                "total": reservation.total_reduit_euro * taux_change if country_code =="DZ" else reservation.total_reduit_euro,
                "create_date": reservation.create_date,
                "status": reservation.status,
                "model_name": reservation.model_name,
                "photo_link": reservation.photo_link,
                "marketing_text_fr": reservation.marketing_text_fr,
                "can_be_modified": can_be_modified,
            })

        result.sort(key=lambda x: x["date_dapart"], reverse=True)
        return {"reservations": result}

    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}


def cencel_request(ref,country_code):
    try:
        today = date.today()
        ma_reservation = Reservation.objects.filter(name=ref)
        if not ma_reservation.exists():
            return {"message": "Réservation non trouvée."}
        
            

        for record in ma_reservation:
            if record.status != 'confirmee':
                return ValueError("Cette opération n'est possible que pour les réservations confirmées.")
            total = record.total_reduit_euro
            date_reservation = record.date_heure_debut.date()
            periode_existe = Periode.objects.filter(
                    date_debut__lte=date_reservation,
                    date_fin__gte=date_reservation
                ).first()
            if periode_existe :
                annulation = ConditionAnnulation.objects.filter(id=1).first()
                jours_restants = (date_reservation - today).days
                if (periode_existe.saison == annulation.haute_saison and jours_restants < annulation.haute_montant) or (periode_existe.saison == annulation.basse_saison and jours_restants < annulation.basse_montant):
                    un_jour = record.prix_jour
                elif (periode_existe.saison == annulation.haute_saison and jours_restants >= annulation.haute_montant) or (periode_existe.saison == annulation.basse_saison and jours_restants >= annulation.basse_montant):
                    un_jour = 15
            else : 
                un_jour = record.prix_jour
            if record.opt_payment_name and un_jour == 15:
                rembourssement = True
                montant_rembourse = total - 15 
            elif not record.opt_payment_name and un_jour == 15:
                rembourssement = True
                montant_rembourse = record.prix_jour - 15
            else: 
                rembourssement = False
                montant_rembourse = 0
            reference = record.name
            raisons_annulation = AnnulerRaison.objects.all()
            cancellation_reasons = [
                {
                    "id": raison.id,
                    "text": {
                        "fr": raison.name,
                        "en": raison.name_en,
                        "ar": raison.name_ar
                    }
                }
                for raison in raisons_annulation
            ]
        
        taux = TauxChange.objects.filter(id=2).first()
        taux_change = taux.montant

        cancellation_data = {
            "reference": reference,
            "currency": "DZD" if country_code == "DZ" else "EUR",
            "cancellation_fee": un_jour * taux_change if country_code == "DZ" else un_jour,
            "refund_amount": montant_rembourse * taux_change if country_code == "DZ" else montant_rembourse,
            "is_refundable": rembourssement
        }

        return {
            "success": True,
            "data": {
                "cancellation": cancellation_data,
                "cancellation_reasons": cancellation_reasons
            }
        }
    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}

def verify_and_calculate(ref, lieu_depart, lieu_retour, date_depart, heure_depart, date_retour, heure_retour, country_code):
    try:
        result = []
        date_depart_heure = datetime.strptime(f"{date_depart} {heure_depart}", '%Y-%m-%d %H:%M')
        date_retour_heure = datetime.strptime(f"{date_retour} {heure_retour}", '%Y-%m-%d %H:%M')

        date_depart_heure += timedelta(hours=1)
        date_retour_heure += timedelta(hours=1)
        lieu_depart_obj = Lieux.objects.filter(id=lieu_depart).first()
        total = 0


        ma_reservation = Reservation.objects.filter(name=ref)
        for record in ma_reservation:
            get_vehicule_id = record.vehicule.numero

            vehicule = Vehicule.objects.get(numero=get_vehicule_id)
            vehicle_reservations = Reservation.objects.filter(vehicule=vehicule)
            is_available = True

            for reservation in vehicle_reservations:
                if (date_depart_heure < reservation.date_heure_fin and date_retour_heure > reservation.date_heure_debut and ref != record.name):
                    is_available = False
                    break

            if is_available == True :
                get_total = record.total_reduit_euro
                get_options_total = record.options_total
                get_status = record.status
                get_reservation_satus = record.etat_reservation
                if get_status != "confirmee" or get_reservation_satus != 'reserve' :
                    result.append({
                        'is_available': "no",
                        'can_be_midified':"no",
                    })
                    return result

                date_depart = datetime.strptime(date_depart, "%Y-%m-%d").date()
                date_retour = datetime.strptime(date_retour, "%Y-%m-%d").date()

                total_days = (date_retour - date_depart).days

                

                tarifs = Tarifs.objects.filter(
                    Q(modele = record.modele)&
                    Q(zone = lieu_depart_obj.zone)&
                    Q(nbr_de__lte=total_days) & Q(nbr_au__gte=total_days) & (
                        Q(date_depart_one__lte=date_depart, date_fin_one__gte=date_retour) |
                        Q(date_depart_two__lte=date_depart, date_fin_two__gte=date_retour) |
                        Q(date_depart_three__lte=date_depart, date_fin_three__gte=date_retour) |
                        Q(date_depart_four__lte=date_depart, date_fin_four__gte=date_retour)
                    )
                )
                for tarif in tarifs:
                    total = 0
                    prix_unitaire = 0

                    if tarif.date_depart_one and tarif.date_fin_one:
                        if date_depart <= tarif.date_fin_one and date_retour >= tarif.date_depart_one:
                            overlap_start = max(date_depart, tarif.date_depart_one)
                            overlap_end = min(date_retour, tarif.date_fin_one)
                            overlap_days = (overlap_end - overlap_start).days
                            if overlap_days > 0:
                                total += overlap_days * tarif.prix
                                prix_unitaire = tarif.prix

                    if tarif.date_depart_two and tarif.date_fin_two:
                        if date_depart <= tarif.date_fin_two and date_retour >= tarif.date_depart_two:
                            overlap_start = max(date_depart, tarif.date_depart_two)
                            overlap_end = min(date_retour, tarif.date_fin_two)
                            overlap_days = (overlap_end - overlap_start).days
                            if overlap_days > 0:
                                total += overlap_days * tarif.prix
                                prix_unitaire = tarif.prix

                    if tarif.date_depart_three and tarif.date_fin_three:
                        if date_depart <= tarif.date_fin_three and date_retour >= tarif.date_depart_three:
                            overlap_start = max(date_depart, tarif.date_depart_three)
                            overlap_end = min(date_retour, tarif.date_fin_three)
                            overlap_days = (overlap_end - overlap_start).days
                            if overlap_days > 0:
                                total += overlap_days * tarif.prix
                                prix_unitaire = tarif.prix

                    if tarif.date_depart_four and tarif.date_fin_four:
                        if date_depart <= tarif.date_fin_four and date_retour >= tarif.date_depart_four:
                            overlap_start = max(date_depart, tarif.date_depart_four)
                            overlap_end = min(date_retour, tarif.date_fin_four)
                            overlap_days = (overlap_end - overlap_start).days
                            if overlap_days > 0:
                                total += overlap_days * tarif.prix
                                prix_unitaire = tarif.prix
                                        
                    frais_dossier = Options.objects.filter(option_code="FRAIS_DOSSIER", zone=lieu_depart_obj.zone).first()
                    if frais_dossier:
                        total += frais_dossier.prix

                    frais_livraison = FraisLivraison.objects.filter(depart_id=lieu_depart, retour_id=lieu_retour)
                    if frais_livraison :
                        for frais in frais_livraison:
                            total += frais.montant if frais else 0
                    else :
                        transit_lieu = lieu_depart_obj.zone.transmission_point
                        frais_livraison_one = FraisLivraison.objects.filter(depart_id=lieu_depart, retour_id=transit_lieu).first()
                        frais_livraison_two = FraisLivraison.objects.filter(depart_id=transit_lieu, retour_id=lieu_retour).first()
                        total += frais_livraison_one.montant + frais_livraison_two.montant if frais_livraison_one and frais_livraison_two else 0

                    supplements = Supplement.objects.filter(
                        Q(heure_debut__lte=heure_depart, heure_fin__gte=heure_depart) |
                        Q(heure_debut__lte=heure_retour, heure_fin__gte=heure_retour)
                    )
                    for supplement in supplements:
                        total += supplement.montant if supplement else 0

                    supplements = Supplement.objects.filter(
                        Q(valeur__gt=0)
                    )

                    for supplement in supplements:

                        start_hour = float(heure_depart[:2]) + float(heure_depart[3:])/60
                        end_hour = float(heure_retour[:2]) + float(heure_retour[3:])/60

                        duration = end_hour - start_hour

                        if duration > supplement.reatrd:
                            total += (prix_unitaire * supplement.valeur) / 100
                
                print("!!!!!!!!!apres supplement total",total,"!!!!!!!!!")
                    
                if record.reduction > 0 :
                    pourcentage = record.reduction
                    total = ((100-pourcentage) * total) / 100
                
                if total > 0:
                    total_ = get_options_total + total

                if record.opt_klm:
                    total_ += record.opt_klm.prix * (record.nbr_jour_reservation - total_days) if record.opt_klm.type_tarif == "jour" else 0

                if record.opt_protection:
                    total_ += record.opt_protection.prix * (record.nbr_jour_reservation - total_days) if record.opt_protection.type_tarif == "jour" else 0

                if record.opt_nd_driver:
                    total_ += record.opt_nd_driver.prix * (record.nbr_jour_reservation - total_days) if record.opt_nd_driver.type_tarif == "jour" else 0

                if record.opt_plein_carburant:
                    total_ += record.opt_plein_carburant.prix * (record.nbr_jour_reservation - total_days) if record.opt_plein_carburant.type_tarif == "jour" else 0

                if record.opt_siege_a:
                    total_ += record.opt_siege_a.prix * (record.nbr_jour_reservation - total_days) if record.opt_siege_a.type_tarif == "jour" else 0

                if record.opt_siege_b:
                    total_ += record.opt_siege_b.prix * (record.nbr_jour_reservation - total_days) if record.opt_siege_b.type_tarif == "jour" else 0

                if record.opt_siege_c:
                    total_ += record.opt_siege_c.prix * (record.nbr_jour_reservation - total_days) if record.opt_siege_c.type_tarif == "jour" else 0

                print("!!!!!!!!!aprs option total",total,"!!!!!!!!!")
                credit = "no"
                credit_amount = 0
                if float(get_total) > float(total_) and ( float(get_total) - float(total_))>150: 
                    credit = "yes"
                    credit_amount = float(get_total) - float(total_)
                
                if float(total_) < float(get_total):
                    total_ = get_total

                print("!!!!!!!!!au finale total",total,"!!!!!!!!!")
                
                taux = TauxChange.objects.filter(id=2).first()
                taux_change = taux.montant
                
                result.append({
                    'is_available':"yes",
                    'old_total': float(get_total) * float(taux_change) if country_code == "DZ" else get_total,
                    'new_total':float(total_) * float(taux_change) if country_code == "DZ" else total_,
                    "credit":credit,
                    "credit_amount": credit_amount
                })

            else :
                result.append({
                    'is_available': "no",
                    'can_be_midified':"no",
                })
                return result
        return result

    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}
    
def option_ma_reservation(ref, email, country_code):
    """
    Retourne un dict d'options indexées par slug, avec
    prix et totaux (convertis si DZ), et champs spécifiques pour KLM.
    """
    try:
        reservation = Reservation.objects.filter(name=ref, email=email).first()
        if not reservation:
            return {}

        nb_jour     = reservation.nbr_jour_reservation or 0
        category_id = getattr(reservation.categorie, "id", None)
        zone_id     = getattr(reservation.zone, "id", None)

        options_qs = Options.objects.filter(
            (Q(option_code__icontains="KLM_ILLIMITED") |
             Q(option_code__icontains="P_ANTICIPE")    |
             Q(option_code__icontains="P_CARBURANT")  |
             Q(option_code__icontains="S_BEBE_5")     |
             Q(option_code__icontains="S_BEBE_13")    |
             Q(option_code__icontains="S_BEBE_18")    |
             Q(option_code__icontains="ND_DRIVER"))
            &
            (Q(categorie__id=category_id) | Q(categorie=None))
            &
            Q(zone__id=zone_id)
        )

        # Normalise le country code
        country_upper = (country_code or "").upper()
        taux_change = 1
        if country_upper == "DZ":
            taux = TauxChange.objects.filter(id=2).first()
            taux_change = getattr(taux, "montant", 1)

        slug_map = {
            "PAIEMENT":       "paiement_prise",
            "P_CARBURANT":    "opt_plein_carburant",
            "ND_DRIVER":      "second_driver",
            "S_BEBE_5":       "opt_siege_a",
            "S_BEBE_13":      "opt_siege_b",
            "S_BEBE_18":      "opt_siege_c",
            "KLM_ILLIMITED":  "opt_klm",
        }

        result = {}
        for opt in options_qs:
            code      = (opt.option_code or "").upper()
            tarif     = (opt.type_tarif   or "").lower()
            prix_base = opt.prix or 0

            # Trouve le slug correspondant
            slug = next((s for key, s in slug_map.items() if key in code), None)
            if not slug:
                continue

            prix_unitaire = prix_base * taux_change
            total = prix_unitaire * nb_jour if tarif == "jour" else prix_unitaire

            entry = {
                "option_name":  opt.name or "",
                "option_prix":  prix_unitaire,
                "option_total": total,
            }

            if "KLM_ILLIMITED" in code:
                limit_base    = getattr(opt, "limit_Klm", 0)
                penalite_base = getattr(opt, "penalite_Klm", 0)
                entry.update({
                    "klm_limit":    limit_base * (nb_jour if tarif == "jour" else 1),
                    "penalite_klm": penalite_base * (float(taux_change) if country_upper == "DZ" else 1),
                })

            result[slug] = entry

        return result

    except Exception as e:
        # On remonte l'erreur pour être gérée dans la vue
        raise
    
def ma_reservation_detail(ref, email, country_code):
    try:
        ma_reservation =Reservation.objects.filter(name=ref, email=email).first()
        if not ma_reservation :
            return {"error": "reservation non trouvé"}
        result =[]
        date = ma_reservation.date_heure_debut.date()
        today = datetime.today().date()
        can_cancel = "yes" 
        can_midify = "yes" if (date - today).days >= 1 else "no"
        retour = ma_reservation.date_heure_fin.date()
        can_modify_return = "yes" if (retour - today).days >= 1 else "no"
        address = ma_reservation.lieu_depart.address
        frais_livraison = ma_reservation.frais_de_dossier
        lieu_rdv = ma_reservation.lieu_depart.rendez_vous      
        
        if country_code =="DZ":
            taux = TauxChange.objects.filter(id=2).first()
            taux_change = taux.montant
            if ma_reservation :
                result.append({
                    "currency":"DA",
                    'can_cancel': can_cancel,
                    "can_midify":can_midify,
                    "can_modify_return":can_modify_return,
                    'id': ma_reservation.id,
                    'reference': ma_reservation.name,
                    'client_nom': ma_reservation.nom,
                    'client_perenom': ma_reservation.prenom,
                    'lieu_depart': ma_reservation.lieu_depart.id,
                    "address_fr":ma_reservation.lieu_depart.address,
                    "address_en":ma_reservation.lieu_depart.address_en,
                    "address_ar":ma_reservation.lieu_depart.address_ar,
                    'lieu_retour': ma_reservation.lieu_retour.id,
                    'address_lieu': address,
                    'lieu_rdv': lieu_rdv,
                    'frais_livraison':frais_livraison,
                    'date_depart': ma_reservation.date_heure_debut,
                    'date_retour': ma_reservation.date_heure_fin,
                    'date_depart_char' : ma_reservation.date_depart_char,
                    'date_retour_char' : ma_reservation.date_retour_char,
                    'heure_depart_char' : ma_reservation.heure_depart_char,
                    'heure_retour_char' : ma_reservation.heure_retour_char,
                    'mobile': ma_reservation.numero_lieu,
                    'status': ma_reservation.status,
                    'opt_payment': ma_reservation.opt_payment_name,
                    'opt_payment_price': ma_reservation.opt_payment_price * taux_change if ma_reservation.opt_payment_price else 0,
                    'opt_payment_total': ma_reservation.opt_payment_total * taux_change if ma_reservation.opt_payment_total else 0,
                    'opt_klm': ma_reservation.opt_klm_name ,
                    'opt_kilometrage': ma_reservation.opt_kilometrage,
                    'opt_klm_price': ma_reservation.opt_klm_price * taux_change if ma_reservation.opt_klm_price else 0,
                    'opt_klm_total': ma_reservation.opt_klm_total * taux_change if ma_reservation.opt_klm_total else 0,
                    'opt_protection': ma_reservation.opt_protection_name,
                    'opt_protection_caution': ma_reservation.opt_protection_caution * taux_change if ma_reservation.opt_protection_caution else 0,
                    'opt_protection_price': ma_reservation.opt_protection_price * taux_change if ma_reservation.opt_protection_price else 0,
                    'opt_protection_total': ma_reservation.opt_protection_total * taux_change if ma_reservation.opt_protection_total else 0,
                    'opt_nd_driver': ma_reservation.opt_nd_driver_name,
                    'opt_nd_driver_price': ma_reservation.opt_nd_driver_price * taux_change if ma_reservation.opt_nd_driver_price else 0,
                    'opt_nd_driver_total': ma_reservation.opt_nd_driver_total * taux_change if ma_reservation.opt_nd_driver_total else 0,
                    'opt_plein_carburant': ma_reservation.opt_plein_carburant_name,
                    'opt_plein_carburant_price': ma_reservation.opt_plein_carburant_prix * taux_change if ma_reservation.opt_plein_carburant_prix else 0,
                    'opt_plein_carburant_total': ma_reservation.opt_plein_carburant_total * taux_change if ma_reservation.opt_plein_carburant_total else 0,
                    'opt_siege_a': ma_reservation.opt_siege_a_name,
                    'opt_siege_a_price': ma_reservation.opt_siege_a_prix * taux_change if ma_reservation.opt_siege_a_prix else 0,
                    'opt_siege_a_total': ma_reservation.opt_siege_a_total * taux_change if ma_reservation.opt_siege_a_total else 0,
                    'opt_siege_b': ma_reservation.opt_siege_b_name,
                    'opt_siege_b_price': ma_reservation.opt_siege_b_prix * taux_change if ma_reservation.opt_siege_b_prix else 0,
                    'opt_siege_b_total': ma_reservation.opt_siege_b_total * taux_change if ma_reservation.opt_siege_b_total else 0,
                    'opt_siege_c': ma_reservation.opt_siege_c_name,
                    'opt_siege_c_price': ma_reservation.opt_siege_c_prix * taux_change if ma_reservation.opt_siege_c_prix else 0,
                    'opt_siege_c_total': ma_reservation.opt_siege_c_total * taux_change if ma_reservation.opt_siege_c_total else 0,
                    'vehicule_id': ma_reservation.vehicule.id,
                    'modele_name': ma_reservation.model_name,
                    "car_description_fr":ma_reservation.modele.description_fr,
                    "car_description_en":ma_reservation.modele.description_en,
                    "car_description_ar":ma_reservation.modele.description_ar,
                    'marketing_text_fr': ma_reservation.marketing_text_fr,
                    'photo_link': ma_reservation.photo_link,
                    'photo_link_nd': ma_reservation.photo_link_nd,
                    'nombre_deplace': ma_reservation.nombre_deplace,
                    'nombre_de_porte': ma_reservation.nombre_de_porte,
                    'nombre_de_bagage': ma_reservation.nombre_de_bagage,
                    'boite_vitesse': ma_reservation.boite_vitesse,
                    'carburant': ma_reservation.carburant,
                    'age_min': ma_reservation.age_min,
                    'nbr_jour_reservation': ma_reservation.nbr_jour_reservation,
                    'total_reduit_euro': ma_reservation.total_reduit_euro * taux_change if ma_reservation.total_reduit_euro else 0,
                    "montant_paye":ma_reservation.montant_paye * taux_change if ma_reservation.total_reduit_euro else 0,
                    "email":ma_reservation.email,
                })
        else :  
            if ma_reservation :
                result.append({
                    "currency":"EUR",
                    'can_cancel': can_cancel,
                    "can_midify":can_midify,
                    "can_modify_return":can_modify_return,
                    'id':ma_reservation.id,
                    'reference': ma_reservation.name,
                    'client_nom': ma_reservation.nom,
                    'client_perenom': ma_reservation.prenom,
                    'lieu_depart': ma_reservation.lieu_depart.id,
                    "address_fr":ma_reservation.lieu_depart.address,
                    "address_en":ma_reservation.lieu_depart.address_en,
                    "address_ar":ma_reservation.lieu_depart.address_ar,
                    'lieu_retour': ma_reservation.lieu_retour.id,
                    'address_lieu': address,
                    'lieu_rdv': lieu_rdv,
                    'frais_livraison':frais_livraison,
                    'date_depart': ma_reservation.date_heure_debut,
                    'date_retour': ma_reservation.date_heure_fin,
                    'date_depart_char' : ma_reservation.date_depart_char,
                    'date_retour_char' : ma_reservation.date_retour_char,
                    'heure_depart_char' : ma_reservation.heure_depart_char,
                    'heure_retour_char' : ma_reservation.heure_retour_char,
                    'mobile': ma_reservation.numero_lieu,
                    'status': ma_reservation.status,
                    'opt_payment': ma_reservation.opt_payment_name,
                    'opt_payment_price': ma_reservation.opt_payment_price,
                    'opt_payment_total': ma_reservation.opt_payment_total,
                    'opt_klm': ma_reservation.opt_klm_name ,
                    'opt_kilometrage': ma_reservation.opt_kilometrage,
                    'opt_klm_price': ma_reservation.opt_klm_price,
                    'opt_klm_total': ma_reservation.opt_klm_total,
                    'opt_protection': ma_reservation.opt_protection_name,
                    'opt_protection_caution': ma_reservation.opt_protection_caution,
                    'opt_protection_price': ma_reservation.opt_protection_price,
                    'opt_protection_total': ma_reservation.opt_protection_total,
                    'opt_nd_driver': ma_reservation.opt_nd_driver_name,
                    'opt_nd_driver_price': ma_reservation.opt_nd_driver_price,
                    'opt_nd_driver_total': ma_reservation.opt_nd_driver_total,
                    'opt_plein_carburant': ma_reservation.opt_plein_carburant_name,
                    'opt_plein_carburant_price': ma_reservation.opt_plein_carburant_prix,
                    'opt_plein_carburant_total': ma_reservation.opt_plein_carburant_total,
                    'opt_siege_a': ma_reservation.opt_siege_a_name,
                    'opt_siege_a_price': ma_reservation.opt_siege_a_prix,
                    'opt_siege_a_total': ma_reservation.opt_siege_a_total,
                    'opt_siege_b': ma_reservation.opt_siege_b_name,
                    'opt_siege_b_price': ma_reservation.opt_siege_b_prix,
                    'opt_siege_b_total': ma_reservation.opt_siege_b_total,
                    'opt_siege_c': ma_reservation.opt_siege_c_name,
                    'opt_siege_c_price': ma_reservation.opt_siege_c_prix,
                    'opt_siege_c_total': ma_reservation.opt_siege_c_total,
                    'vehicule_id': ma_reservation.vehicule.id,
                    "car_description_fr":ma_reservation.modele.description_fr,
                    "car_description_en":ma_reservation.modele.description_en,
                    "car_description_ar":ma_reservation.modele.description_ar,
                    'modele_name': ma_reservation.model_name,
                    'marketing_text_fr': ma_reservation.marketing_text_fr,
                    'photo_link': ma_reservation.photo_link,
                    'photo_link_nd': ma_reservation.photo_link_nd,
                    'nombre_deplace': ma_reservation.nombre_deplace,
                    'nombre_de_porte': ma_reservation.nombre_de_porte,
                    'nombre_de_bagage': ma_reservation.nombre_de_bagage,
                    'boite_vitesse': ma_reservation.boite_vitesse,
                    'carburant': ma_reservation.carburant,
                    'age_min': ma_reservation.age_min,
                    'nbr_jour_reservation': ma_reservation.nbr_jour_reservation,
                    'total_reduit_euro': ma_reservation.total_reduit_euro,
                    "montant_paye":ma_reservation.montant_paye,
                    "email":ma_reservation.email,

                })  

        return result

    except Exception as e:
        return {"message": f"Erreur: {str(e)}", "reservation_id": None}

def create_account(email, nom, prenom, phone , birthday, permis_date):
    try:
        nom = re.sub(r'\s+', ' ', nom.strip()).upper()
        prenom = re.sub(r'\s+', ' ', prenom.strip()).upper()

        client = ListeClient.objects.filter(nom__iexact=nom, prenom__iexact=prenom).first()
        if client:
            return {"created": False, "message": "Le client existe déjà avec ce nom et prénom."}
        
        client = ListeClient.objects.filter(nom__iexact=prenom, prenom__iexact=nom).first()
        if client:
            return {"created": False, "message": "Le client existe déjà avec prénom et nom inversés."}
        category = CategorieClient.objects.filter(name="DRIVER").first()
        
        client_create = ListeClient.objects.create(
            email=email,
            nom=nom,
            prenom=prenom,
            telephone=phone,
            mobile = phone,
            date_de_naissance=birthday,
            date_de_permis=permis_date,
            categorie_client=category,
            category_client_name=category.name,
            total_points_char="0 pts",
            total_points=0,
            create_date=datetime.now()
        )
        client_create.save()
        max_retries = 3
        for attempt in range(max_retries):
            try:
                sujet = f"enregistrement de compte & activation"
                expediteur = settings.EMAIL_HOST_USER
                html_message = render_to_string('email/create_account.html', {
                    "nom": nom,
                    "prenom": prenom
                })
                
                send_mail(
                    sujet,
                    strip_tags(html_message),
                    expediteur,
                    [email],
                    html_message=html_message,
                    fail_silently=False,
                )
                break  
                
            except Exception as mail_error:
                if attempt == max_retries - 1:  
                    print(f"Erreur envoi email: {mail_error}")
                else:
                    time.sleep(2)
 
                   
        return {"created": True, "client_id": client_create.id}
            
    except Exception as e:
        return {"message": f"Erreur inattendue : {str(e)}", "client_id": None}



def otp_send(email):
    try:
        client = ListeClient.objects.filter(email=email).first()
        if client is None:
            return {"account":False,"message": "Aucun client trouvé avec cet email.", "client_id": None}

        otp_code = f"{random.randint(100000, 999999)}"
        client.otp = otp_code
        client.otp_created_at = datetime.now()
        client.save()

        sujet = f"Votre code OTP {otp_code}"
        expediteur = settings.EMAIL_HOST_USER

        html_message = render_to_string('email/otp_email.html', {
            'client': client.nom,
            'client_prenom':client.prenom,
            'otp_code': otp_code,
        })
        try:

            send_mail(
                sujet,
                strip_tags(html_message),  
                expediteur,
                [email],
                html_message=html_message,
                fail_silently=False,
            )
            return {"sent": True,"client_id": client.id, "account": True}
        except Exception as e:
            return {"sent": False,"message": f"Erreur lors de l'envoi de l'email : {str(e)}", "client_id": client.id}
    except Exception as e:
        return {"sent": False,"message": f"Erreur inattendue : {str(e)}", "client_id": None}
    
def otp_verify(email, otp, client_id):
    try:
        client = ListeClient.objects.filter(id=client_id).first()
        if not client:
            return {"success": False, "message": "Aucun client trouvé avec cet email."}
        
        otp_time = client.otp_created_at

        if timezone.is_naive(otp_time):
            otp_time = timezone.make_aware(otp_time)
        
        otp_time += timedelta(hours=1)

        if str(client.otp) == str(otp) and timezone.now() - otp_time < timedelta(minutes=7):
            client.otp = None
            client.otp_created_at = None
            client.save()
            return {"success": True}
        elif str(client.otp) == str(otp) and timezone.now() - otp_time > timedelta(minutes=7):
            client.otp = None
            client.otp_created_at = None
            client.save()
            return {"success": False, "expired":True}
        elif str(client.otp) != str(otp) and client.otp:
            client.otp = None
            client.otp_created_at = None
            client.save()
            return {"success": False, "incorrect":True}
        else:
            return {"success": False}
    except Exception as e:
        return {"success": False, "message": f"Erreur inattendue : {str(e)}"}

def rechercher_vehicules_disponibles(lieu_depart_id, lieu_retour_id, date_depart, heure_depart, date_retour, heure_retour):

    try:
        lieu_depart = Lieux.objects.get(pk=lieu_depart_id)
        lieu_retour = Lieux.objects.get(pk=lieu_retour_id)

        date_heure_debut = datetime.strptime(f"{date_depart} {heure_depart}", '%Y-%m-%d %H:%M')
        date_heure_fin = datetime.strptime(f"{date_retour} {heure_retour}", '%Y-%m-%d %H:%M')

        vehicules_disponibles = Vehicule.objects.filter(
            zone=lieu_depart.zone,
            active_test=True,
            date_debut_service__lt=date_heure_debut
        ).exclude(
            Q(reservation__date_heure_debut__lt=date_heure_fin) &
            Q(reservation__date_heure_fin__gt=date_heure_debut) &
            Q(reservation__status='confirmee')
        ).distinct()

        return vehicules_disponibles

    except ObjectDoesNotExist as e:
        print(f"Erreur: {e}")
        return []


def rechercher_tarifs(lieu_depart_id, lieu_retour_id, date_depart, heure_depart, date_retour, heure_retour):

    date_depart = datetime.strptime(date_depart, "%Y-%m-%d").date()
    date_retour = datetime.strptime(date_retour, "%Y-%m-%d").date()

    total_days = (date_retour - date_depart).days

    tarifs = Tarifs.objects.filter(
        Q(nbr_de__lte=total_days) & Q(nbr_au__gte=total_days) & (
            Q(date_depart_one__lte=date_depart, date_fin_one__gte=date_retour) |
            Q(date_depart_two__lte=date_depart, date_fin_two__gte=date_retour) |
            Q(date_depart_three__lte=date_depart, date_fin_three__gte=date_retour) |
            Q(date_depart_four__lte=date_depart, date_fin_four__gte=date_retour)
        )
    )

    resultats = []

    for record in tarifs:
        total = 0
        prix_unitaire = 0

        # Calcul des jours de réservation et ajout du tarif
        if record.date_depart_one and record.date_fin_one:
            if date_depart <= record.date_fin_one and date_retour >= record.date_depart_one:
                overlap_start = max(date_depart, record.date_depart_one)
                overlap_end = min(date_retour, record.date_fin_one)
                overlap_days = (overlap_end - overlap_start).days
                if overlap_days > 0:
                    total += overlap_days * record.prix
                    prix_unitaire = record.prix

        if record.date_depart_two and record.date_fin_two:
            if date_depart <= record.date_fin_two and date_retour >= record.date_depart_two:
                overlap_start = max(date_depart, record.date_depart_two)
                overlap_end = min(date_retour, record.date_fin_two)
                overlap_days = (overlap_end - overlap_start).days
                if overlap_days > 0:
                    total += overlap_days * record.prix
                    prix_unitaire = record.prix

        if record.date_depart_three and record.date_fin_three:
            if date_depart <= record.date_fin_three and date_retour >= record.date_depart_three:
                overlap_start = max(date_depart, record.date_depart_three)
                overlap_end = min(date_retour, record.date_fin_three)
                overlap_days = (overlap_end - overlap_start).days
                if overlap_days > 0:
                    total += overlap_days * record.prix
                    prix_unitaire = record.prix

        if record.date_depart_four and record.date_fin_four:
            if date_depart <= record.date_fin_four and date_retour >= record.date_depart_four:
                overlap_start = max(date_depart, record.date_depart_four)
                overlap_end = min(date_retour, record.date_fin_four)
                overlap_days = (overlap_end - overlap_start).days
                if overlap_days > 0:
                    total += overlap_days * record.prix
                    prix_unitaire = record.prix

        frais_livraison = FraisLivraison.objects.filter(depart_id=lieu_depart_id, retour_id=lieu_retour_id)
        for frais in frais_livraison:
            total += frais.montant if frais else 0

        supplements = Supplement.objects.filter(
            Q(heure_debut__lte=heure_depart, heure_fin__gte=heure_depart) |
            Q(heure_debut__lte=heure_retour, heure_fin__gte=heure_retour)
        )
        for supplement in supplements:
            total += supplement.montant if supplement else 0

        for supplement in supplements:

            start_hour = float(heure_depart[:2]) + float(heure_depart[3:])/60
            end_hour = float(heure_retour[:2]) + float(heure_retour[3:])/60

            duration = end_hour - start_hour

            if duration > supplement.reatrd:
                total += (prix_unitaire * supplement.valeur) / 100

        if total > 0:
            prix_par_jour = total / total_days if total_days > 0 else 0
            resultats.append({
                "modele_id": record.modele.id,
                "total": total,
                "prix": prix_par_jour
            })

    return resultats

def check_client(id):
    try:
        client_id=ListeClient.objects.filter(id=id).first()
        if client_id :
            if client_id.risque == "eleve":
                return {"message":"negatif"}
            else :
                return {"message":"positif"}

    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}


def get_available_vehicles(date_depart, heure_depart, date_retour, heure_retour, zone):
    date_heure_debut = datetime.strptime(f"{date_depart} {heure_depart}", "%Y-%m-%d %H:%M")
    date_heure_fin = datetime.strptime(f"{date_retour} {heure_retour}", "%Y-%m-%d %H:%M")

    reserved_vehicles = Reservation.objects.filter(
        Q(date_heure_debut__lt=date_heure_fin, date_heure_fin__gt=date_heure_debut),  
        etat_reservation__in=["reserve", "loue"],status="confirmee"  
    ).values_list("vehicule_id", flat=True)

    blocked_vehicles = BlockCar.objects.filter(
        Q(date_from__lte=date_heure_fin.date(), date_to__gte=date_heure_debut.date())
    ).values_list("vehicule_id", flat=True)

    available_vehicles = Vehicule.objects.filter(
        active_test=True,  
        date_debut_service__lte=date_heure_debut.date(),
        zone_id=int(zone) 
    ).exclude(
        id__in=list(reserved_vehicles) + list(blocked_vehicles)
    )  

    return available_vehicles

def search_option(code, total_days, lieu_depart):
    try:
        option = Options.objects.filter(option_code=code,zone=lieu_depart.zone).first()
        return {
            'name': option.name,
            'name_en': option.name_en,
            'name_ar': option.name_ar,
            'type_tarif': option.type_tarif,
            'prix': option.prix,
            'total': option.prix * total_days if option.type_tarif == 'jour' else option.prix,
            'categorie': option.categorie.id if option.categorie else None,
            'limit': (option.limit_Klm or 0) * total_days,
            'penalite': option.penalite_Klm or 0,
            'caution': option.caution or 0,
            'min_prix' : float(option.min_prix) if option.min_prix is not None else 0
        }
    except Options.DoesNotExist:
        return {'name': None,'name_en':None,'name_ar':None,'type_tarif': None, 'min_prix' :0, 'prix': 0, 'total': 0, 'limit': 0, 'penalite': 0, 'caution': 0, 'categorie': 0}
 
def search_option_DA(code, total_days, lieu_depart):
    try:
        option = Options.objects.filter(option_code=code,zone=lieu_depart.zone).first()
        taux = TauxChange.objects.filter(id=2).first()
        
        if not option or not taux:
            return {'name': None, 'prix': 0, 'total': 0, 'limit': 0, 'penalite': 0, 'caution': 0, 'categorie': 0}
        
        prix = float(option.prix) if option.prix is not None else 0
        montant_taux = float(taux.montant) if taux.montant is not None else 0
        limit_Klm = float(option.limit_Klm) if option.limit_Klm is not None else 0
        penalite_Klm = float(option.penalite_Klm) if option.penalite_Klm is not None else 0
        caution = float(option.caution) if option.caution is not None else 0
        min_prix = float(option.min_prix) if option.min_prix is not None else 0

        return {
            'name': option.name,
            'name_en': option.name_en,
            'name_ar': option.name_ar,
            'type_tarif': option.type_tarif,
            'prix': prix * montant_taux,
            'total': prix * float(total_days) * montant_taux if option.type_tarif == 'jour' else prix * montant_taux,
            'categorie': option.categorie.id if option.categorie else None,
            'limit': limit_Klm * total_days,
            'penalite': penalite_Klm * montant_taux,
            'caution': caution * montant_taux,
            'min_prix': min_prix * montant_taux
        }
    
    except Options.DoesNotExist:
        return {'name': None,'name_en':None,'name_ar':None,'type_tarif': None, 'prix': 0, 'total': 0, 'limit': 0, 'penalite': 0, 'caution': 0, 'categorie': 0,'min_prix':0} 
    
def free_options_f(client_id):
    free_options = []
    if client_id:
        client_status = check_client(client_id)
        client = ListeClient.objects.filter(id=client_id).first()

        if not client:
            return {"message": "Client introuvable"}

        if client_status.get("message") == "negatif":
            return {"message": "Client has a high risk, cannot proceed"}
        elif client_status.get("message") == "positif":
            client_categori_id = client.categorie_client.id
            category_client = CategorieClient.objects.filter(id=client_categori_id).first()
            
            options = [
                category_client.option_one,
                category_client.option_two,
                category_client.option_three,
                category_client.option_four,
                category_client.option_five,
                category_client.option_six,
                category_client.option_seven,
                category_client.option_eight,
                category_client.option_nine,
                category_client.option_ten,
            ]

            option_un = any(opt and "KLM" in opt.option_code for opt in options)
            option_deux = any(opt and "ANTICIPE" in opt.option_code for opt in options)
            option_trois= any(opt and "MAX" in opt.option_code for opt in options)
            option_quatre= any(opt and "DRIVER" in opt.option_code for opt in options)
            option_cinq= any(opt and "CARBURANT" in opt.option_code for opt in options)
            option_sixe= any(opt and "S_BEBE_5" in opt.option_code for opt in options)
            option_sept= any(opt and "S_BEBE_13" in opt.option_code for opt in options)
            option_huite= any(opt and "S_BEBE_18" in opt.option_code for opt in options)

            free_options.append({
                "option_one": option_quatre,
                "option_two": option_cinq,
                "option_three": option_sixe,
                "option_four": option_sept,
                "option_five": option_huite,
                "option_six": option_deux,
                "option_seven": option_un,
                "option_eight": option_trois,
                })
        else:
            return client_status

    return free_options

def search_result_vehicule(lieu_depart_id, lieu_retour_id, date_depart, heure_depart, date_retour, heure_retour, client_id, prime_code, country_code):
    try:
        date_depart = datetime.strptime(date_depart, "%Y-%m-%d").date()
        date_retour = datetime.strptime(date_retour, "%Y-%m-%d").date()
        today = datetime.today().date()
    except ValueError:
        return {"message": "Invalid date format"}
    taux = TauxChange.objects.filter(id=2).first()
    taux_change = taux.montant
    if taux_change and taux_change is not None :
       taux_change = float(taux_change)
    else : 
        return{"message": "taux de change introuvable"} 
    
    if date_retour < date_depart:
        return {"message": "Return date cannot be before departure date"}

    total_days = (date_retour - date_depart).days

    lieu_depart = Lieux.objects.filter(id=lieu_depart_id).first()
    if not lieu_depart:
        return {"message": "Lieu de départ introuvable"}

    zone_id = lieu_depart.zone.id if lieu_depart.zone else None
    if not zone_id:
        return {"message": "Zone introuvable pour ce lieu de départ"}

    result = []
    client_pr = 0 
    client_sold = 0
    total = 0
    total_red = 0
    prix_unitaire = 0
    prix_unitaire_red = 0
    prix_jour = 0
    total_primary = 0
    montant_promotion = 0
    montant_code_prime = 0
    promotions = Promotion.objects.filter(
        debut_visibilite__lte=today,
        fin_visibilite__gte=today,
        date_debut__lte=date_depart,
        date_fin__gte=date_retour,
        active_passive=True
    ).first()
    promotion_name = promotions.name if promotions is not None else None
    promotion_value = 0
    model_one = None
    model_two = None
    model_three = None
    model_four = None
    model_five = None

    if promotions and promotions.tout_modele == "oui" and promotions.tout_zone == "oui":
        promotion_value = promotions.reduction
    elif promotions and promotions.tout_modele == "oui" and promotions.tout_zone == "non":
        if lieu_depart.zone == promotions.zone_one or lieu_depart.zone == promotions.zone_one or lieu_depart.zone == promotions.zone_one :
            promotion_value = promotions.reduction
        else :
            promotion_value = 0
    elif promotions and promotions.tout_modele == "non" and promotions.tout_zone == "oui":
        promotion_value = promotions.reduction
        if promotions.model_one :
            model_one = promotions.model_one
        else :
            model_one = None
        if promotions.model_two :
            model_two = promotions.model_two
        else :
            model_two = None
        if promotions.model_three :
            model_three = promotions.model_three
        else :
            model_three = None
        if promotions.model_four :
            model_four = promotions.model_four
        else :
            model_four = None
        if promotions.model_five :
            model_five = promotions.model_five
        else :
            model_five = None
    elif promotions and promotions.tout_modele == "non" and promotions.tout_zone == "non":
        if lieu_depart.zone == promotions.zone_one :
            promotion_value = promotions.reduction
            if promotions.model_one :
                model_one = promotions.model_one
            else :
                model_one = None
            if promotions.model_two :
                model_two = promotions.model_two
            else :
                model_two = None
            if promotions.model_three :
                model_three = promotions.model_three
            else :
                model_three = None
            if promotions.model_four :
                model_four = promotions.model_four
            else :
                model_four = None
            if promotions.model_five :
                model_five = promotions.model_five
            else :
                model_five = None
        elif lieu_depart.zone == promotions.zone_two :
            promotion_value = promotions.reduction
            if promotions.model_one :
                model_one = promotions.model_one
            else :
                model_one = None
            if promotions.model_two :
                model_two = promotions.model_two
            else :
                model_two = None
            if promotions.model_three :
                model_three = promotions.model_three
            else :
                model_three = None
            if promotions.model_four :
                model_four = promotions.model_four
            else :
                model_four = None
            if promotions.model_five :
                model_five = promotions.model_five
            else :
                model_five = None
        elif lieu_depart.zone == promotions.zone_three :
            promotion_value = promotions.reduction
            if promotions.model_one :
                model_one = promotions.model_one
            else :
                model_one = None
            if promotions.model_two :
                model_two = promotions.model_two
            else :
                model_two = None
            if promotions.model_three :
                model_three = promotions.model_three
            else :
                model_three = None
            if promotions.model_four :
                model_four = promotions.model_four
            else :
                model_four = None
            if promotions.model_five :
                model_five = promotions.model_five
            else :
                model_five = None
        else :
            promotion_value = 0
    elif promotions and promotions.tout_modele == "aleatoire" and promotions.tout_zone == "oui":
        if promotions.nbr_model == 1:
            promotion_value = promotions.reduction
            model_one = Modele.objects.order_by("?").first()
        elif promotions.nbr_model == 2:
            promotion_value = promotions.reduction
            records = Modele.objects.order_by("?")[:2]
            if len(records) == 2:
                model_one, model_two = records
            else:
                model_one = records[0] if records else None
                model_two = None
        elif promotions.nbr_model == 3:
            promotion_value = promotions.reduction
            records = Modele.objects.order_by("?")[:3]
            if len(records) == 3:
                model_one, model_two, model_three = records
            else:
                model_one = records[0] if len(records) > 0 else None
                model_two = records[1] if len(records) > 1 else None
                model_three = records[2] if len(records) > 2 else None
        elif promotions.nbr_model == 4:
            promotion_value = promotions.reduction
            records = Modele.objects.order_by("?")[:4]
            if len(records) == 4:
                model_one, model_two, model_three, model_four = records
            else:
                model_one = records[0] if len(records) > 0 else None
                model_two = records[1] if len(records) > 1 else None
                model_three = records[2] if len(records) > 2 else None
                model_four = records[3] if len(records) > 3 else None
        elif promotions.nbr_model == 5:
            promotion_value = promotions.reduction
            records = Modele.objects.order_by("?")[:5]
            if len(records) == 5:
                model_one, model_two, model_three, model_four, model_five = records
            else:
                model_one = records[0] if len(records) > 0 else None
                model_two = records[1] if len(records) > 1 else None
                model_three = records[2] if len(records) > 2 else None
                model_four = records[3] if len(records) > 3 else None
                model_five = records[4] if len(records) > 3 else None
        else :
            model_one = None
            model_two = None
            model_three = None
            model_four = None
            model_five = None
            
    date_annulation = None
    annulation = ConditionAnnulation.objects.filter(id=1).first()
    if annulation:
        periode = Periode.objects.filter(
            saison=annulation.haute_saison, 
            date_debut__lt=date_depart, 
            date_fin__gt=date_retour  
        ).first() 
        if periode:
            jr_avant = annulation.haute_montant
            if isinstance(jr_avant, int) and jr_avant > 0:
                date_annulation = date_depart - timedelta(days=jr_avant) 
            else:
                date_annulation = None
        else:
            jr_avant = None
            date_annulation = None
        if not periode:
            periode = Periode.objects.filter(
                saison=annulation.basse_saison, 
                date_debut__lt=date_depart, 
                date_fin__gt=date_retour  
            ).first()  
            if periode:
                jr_avant = annulation.basse_montant
                if isinstance(jr_avant, int) and jr_avant > 0:
                    date_annulation = date_depart - timedelta(days=jr_avant) 
                else:
                    date_annulation = None
            else:
                jr_avant = None
                date_annulation = None
        
    else:
        jr_avant = None
        date_annulation = None
    
    client = None

    if country_code == "DZ":
        if client_id :
            client_status = check_client(client_id)  
            client = ListeClient.objects.filter(id=client_id).first()          
            if not client:
                return {"message": "Client introuvable"}
            
            if client_status.get("message") == "negatif":
                return {"message": "Client has a high risk, cannot proceed"}
            elif client_status.get("message") == "positif":
                client_pr = client.reduction if client.reduction is not None else 0
                client_sold = float(client.solde) * taux_change if client.solde is not None else 0

            else:
                return client_status 
        prime_red = 0
        if prime_code and not client_id:
            parent_client = ListeClient.objects.filter(code_prime=prime_code).first() 
            if parent_client :
                parent_sold = SoldeParrainage.objects.filter(name="Solde Parrainage").first()
                prime_red = float(parent_sold.parrain_solde) * taux_change if parent_sold.parrain_solde is not None else 0

        available_vehicles = get_available_vehicles(date_depart, heure_depart, date_retour, heure_retour, zone_id)
        lieu_depart_obj = Lieux.objects.filter(id=lieu_depart_id).first()

        frais_livraison = FraisLivraison.objects.filter(depart_id=lieu_depart_id, retour_id=lieu_retour_id) 
        if frais_livraison :
            for frais in frais_livraison:
                total += float(frais.montant) * taux_change if frais else 0
        else :
            transit_lieu = lieu_depart_obj.zone.transmission_point
            frais_livraison_one = FraisLivraison.objects.filter(depart_id=lieu_depart_id, retour_id=transit_lieu).first()
            frais_livraison_two = FraisLivraison.objects.filter(depart_id=transit_lieu, retour_id=lieu_retour_id).first()
            total += float(frais_livraison_one.montant + frais_livraison_two.montant) * taux_change if frais_livraison_one and frais_livraison_two else 0

        supplements_one = Supplement.objects.filter(
            Q(heure_debut__lte=heure_depart, heure_fin__gte=heure_depart) 
        ).first()

        total += float(supplements_one.montant) * taux_change if supplements_one else 0

        supplements_two = Supplement.objects.filter(
            Q(heure_debut__lte=heure_retour, heure_fin__gte=heure_retour)
        ).first()
        total += float(supplements_two.montant) * taux_change if supplements_two else 0

        frais_dossier = search_option_DA("FRAIS_DOSSIER", total_days, lieu_depart)
        total += frais_dossier["total"] 

        paiement_anticipe = search_option_DA("P_ANTICIPE", total_days, lieu_depart)
        opt_payment_name = paiement_anticipe["name"]
        opt_payment_name_en = paiement_anticipe["name_en"]
        opt_payment_name_ar = paiement_anticipe["name_ar"]
        opt_payment_type_tarif = paiement_anticipe["type_tarif"]
        opt_payment_unit = paiement_anticipe["prix"]
        opt_payment_total = paiement_anticipe["total"]

        vip_limit = search_option_DA("KLM_ILLIMITED", total_days, lieu_depart)
        vip_limit_value = vip_limit["limit"]

        klm_illimite = search_option_DA("KLM_ILLIMITED", total_days, lieu_depart)
        opt_klm_name = klm_illimite["name"]
        opt_klm_name_en = klm_illimite["name_en"]
        opt_klm_name_ar = klm_illimite["name_ar"]
        opt_klm_type_tarif = klm_illimite["type_tarif"]
        opt_klm_unit = klm_illimite["prix"]
        opt_klm_total = klm_illimite["total"]
        opt_klm_limit = vip_limit_value if client is not None and client.categorie_client.name == "VIP" and client.categorie_client is not None else klm_illimite["limit"]
        opt_klm_penalite = klm_illimite["penalite"]
        
        klm_illimite_b = search_option_DA("KLM_ILLIMITED_B", total_days, lieu_depart)
        opt_klm_b_name = klm_illimite_b["name"]
        opt_klm_b_name_en = klm_illimite_b["name_en"]
        opt_klm_b_name_ar = klm_illimite_b["name_ar"]
        opt_klm_b_type_tarif = klm_illimite_b["type_tarif"]
        opt_klm_b_unit = klm_illimite_b["prix"]
        opt_klm_b_total = klm_illimite_b["total"]
        opt_klm_b_limit = vip_limit_value if client is not None and client.categorie_client.name == "VIP" and client.categorie_client is not None else klm_illimite_b["limit"]
        opt_klm_b_penalite = klm_illimite_b["penalite"]

        klm_illimite_c = search_option_DA("KLM_ILLIMITED_C", total_days, lieu_depart)
        opt_klm_c_name = klm_illimite_c["name"]
        opt_klm_c_name_en = klm_illimite_c["name_en"]
        opt_klm_c_name_ar = klm_illimite_c["name_ar"]
        opt_klm_c_type_tarif = klm_illimite_c["type_tarif"]
        opt_klm_c_unit = klm_illimite_c["prix"]
        opt_klm_c_total = klm_illimite_c["total"]
        opt_klm_c_limit =  vip_limit_value if client is not None and client.categorie_client.name == "VIP" and client.categorie_client is not None else klm_illimite_c["limit"] 
        opt_klm_c_penalite = klm_illimite_c["penalite"]

        nd_driver = search_option_DA("ND_DRIVER", total_days, lieu_depart)
        opt_nd_driver_name = nd_driver["name"]
        opt_nd_driver_name_en = nd_driver["name_en"]
        opt_nd_driver_name_ar = nd_driver["name_ar"]
        opt_nd_driver_type_tarif = nd_driver["type_tarif"]
        opt_nd_driver_unit = nd_driver["prix"]
        opt_nd_driver_total = nd_driver["total"]

        plein_carburant = search_option_DA("P_CARBURANT", total_days, lieu_depart)
        opt_carburant_name = plein_carburant["name"]
        opt_carburant_name_en = plein_carburant["name_en"]
        opt_carburant_name_ar = plein_carburant["name_ar"]
        opt_carburant_type_tarif = plein_carburant["type_tarif"]
        opt_carburant_unit = plein_carburant["prix"]
        opt_carburant_total = plein_carburant["total"]

        siege_a = search_option_DA("S_BEBE_5", total_days, lieu_depart)
        opt_siege_a_name = siege_a["name"]
        opt_siege_a_name_en = siege_a["name_en"]
        opt_siege_a_name_ar = siege_a["name_ar"]
        opt_siege_a_type_tarif = siege_a["type_tarif"]
        opt_siege_a_unit = siege_a["prix"]
        opt_siege_a_total = siege_a["total"]

        siege_b = search_option_DA("S_BEBE_13", total_days, lieu_depart)
        opt_siege_b_name = siege_b["name"]
        opt_siege_b_name_en = siege_b["name_en"]
        opt_siege_b_name_ar = siege_b["name_ar"]
        opt_siege_b_type_tarif = siege_b["type_tarif"]
        opt_siege_b_unit = siege_b["prix"]
        opt_siege_b_total = siege_b["total"]

        siege_c = search_option_DA("S_BEBE_18", total_days, lieu_depart)
        opt_siege_c_name = siege_c["name"]
        opt_siege_c_name_en = siege_c["name_en"]
        opt_siege_c_name_ar = siege_c["name_ar"]
        opt_siege_c_type_tarif = siege_c["type_tarif"]
        opt_siege_c_unit = siege_c["prix"]
        opt_siege_c_total = siege_c["total"]
    
        base_a = search_option_DA("BASE_P_1", total_days, lieu_depart)
        base_a_name = base_a["name"]
        base_a_name_en = base_a["name_en"]
        base_a_name_ar = base_a["name_ar"]
        base_a_type_tarif = base_a["type_tarif"]
        base_a_unit = base_a["prix"]
        base_a_total = base_a["total"]
        base_a_category = base_a["categorie"]
        base_a_caution = base_a["caution"]

        base_b = search_option_DA("BASE_P_2", total_days, lieu_depart)
        base_b_name = base_b["name"]
        base_b_name_en = base_b["name_en"]
        base_b_name_ar = base_b["name_ar"]
        base_b_type_tarif = base_b["type_tarif"]
        base_b_unit = base_b["prix"]
        base_b_total = base_b["total"]
        base_b_category = base_b["categorie"]
        base_b_caution = base_b["caution"]

        base_c = search_option_DA("BASE_P_3", total_days, lieu_depart)
        base_c_name = base_c["name"]
        base_c_name_en = base_c["name_en"]
        base_c_name_ar = base_c["name_ar"]
        base_c_type_tarif = base_c["type_tarif"]
        base_c_unit = base_c["prix"]
        base_c_total = base_c["total"]
        base_c_category = base_c["categorie"]
        base_c_caution = base_c["caution"]

        standart_a = search_option_DA("STANDART_P_1", total_days, lieu_depart)
        standart_a_name = standart_a["name"]
        standart_a_name_en = standart_a["name_en"]
        standart_a_name_ar = standart_a["name_ar"]
        standart_a_type_tarif = standart_a["type_tarif"]
        standart_a_unit = standart_a["prix"]
        standart_a_total = standart_a["total"]
        standart_a_caution = standart_a["caution"]

        standart_b = search_option_DA("STANDART_P_2", total_days, lieu_depart)
        standart_b_name = standart_b["name"]
        standart_b_name_en = standart_b["name_en"]
        standart_b_name_ar = standart_b["name_ar"]
        standart_b_type_tarif = standart_b["type_tarif"]
        standart_b_unit = standart_b["prix"]
        standart_b_total = standart_b["total"]
        standart_b_caution = standart_b["caution"]

        standart_c = search_option_DA("STANDART_P_3", total_days, lieu_depart)
        standart_c_name = standart_c["name"]
        standart_c_name_en = standart_c["name_en"]
        standart_c_name_ar = standart_c["name_ar"]
        standart_c_type_tarif = standart_c["type_tarif"]
        standart_c_unit = standart_c["prix"]
        standart_c_total = standart_c["total"]
        standart_c_caution = standart_c["caution"]

        max_a = search_option_DA("MAX_P_1", total_days, lieu_depart)
        max_a_name = max_a["name"]
        max_a_name_en = max_a["name_en"]
        max_a_name_ar = max_a["name_ar"]
        max_a_type_tarif = max_a["type_tarif"]
        max_a_unit = max_a["prix"] if max_a["total"] > max_a["min_prix"] else max_a["min_prix"] / total_days
        max_a_total = max_a["total"] if max_a["total"] > max_a["min_prix"] else max_a["min_prix"]
        max_a_caution = max_a["caution"] 

        max_b = search_option_DA("MAX_P_2", total_days, lieu_depart)
        max_b_name = max_b["name"]
        max_b_name_en = max_b["name_en"]
        max_b_name_ar = max_b["name_ar"]
        max_b_type_tarif = max_b["type_tarif"]
        max_b_unit = max_b["prix"] if max_b["total"] > max_b["min_prix"] else max_b["min_prix"] / total_days
        max_b_total = max_b["total"] if max_b["total"] > max_b["min_prix"] else max_b["min_prix"]
        max_b_caution = max_b["caution"]

        max_c = search_option_DA("MAX_P_3", total_days, lieu_depart)
        max_c_name = max_c["name"]
        max_c_name_en = max_c["name_en"]
        max_c_name_ar = max_c["name_ar"]
        max_c_type_tarif = max_c["type_tarif"]
        max_c_unit = max_c["prix"] if max_c["total"] > max_c["min_prix"] else max_c["min_prix"] / total_days
        max_c_total = max_c["total"] if max_c["total"] > max_c["min_prix"] else max_c["min_prix"]
        max_c_caution = max_c["caution"]

        modeles_ajoutes = set()
        total_brut = 0

        for vehicle in available_vehicles:
            if vehicle.modele.id in modeles_ajoutes:
                continue

            tarif = Tarifs.objects.filter(
                modele=vehicle.modele,  
                nbr_de__lte=total_days, 
                nbr_au__gte=total_days,
                zone=lieu_depart.zone
            ).filter(
                Q(date_depart_one__lte=date_depart, date_fin_one__gte=date_retour) |
                Q(date_depart_two__lte=date_depart, date_fin_two__gte=date_retour) |
                Q(date_depart_three__lte=date_depart, date_fin_three__gte=date_retour) |
                Q(date_depart_four__lte=date_depart, date_fin_four__gte=date_retour)
            ).first()

            if tarif:
                prix_jour = float(tarif.prix) * taux_change
                total_primary = total
                supplements_valeur = Supplement.objects.filter(valeur__gt=0)
                
                for supplement in supplements_valeur:
                    start_hour = float(heure_depart[:2]) + float(heure_depart[3:])/60
                    end_hour = float(heure_retour[:2]) + float(heure_retour[3:])/60
                    duration = end_hour - start_hour
                    if duration > supplement.reatrd:
                        total_primary += (prix_jour * supplement.valeur) / 100

                total_brut = total_primary + (prix_jour * total_days)
                prix_unitaire = total_brut / total_days
                if int(client_pr) > promotion_value :
                    promotion = "yes"
                    percentage = client_pr
                    montant_code_prime = prix_jour * client_pr / 100 * total_days
                    total_red = total_primary + (((100 - percentage) * prix_jour / 100) * total_days)
                    prix_unitaire_red = total_red / total_days
                elif promotion_value > int(client_pr) and promotions.tout_modele == "oui":
                    promotion = "yes"
                    percentage = promotion_value 
                    montant_promotion = prix_jour * promotion_value / 100 * total_days
                    total_red = total_primary + (((100 - percentage) * prix_jour / 100) * total_days)
                    prix_unitaire_red = total_red / total_days
                elif model_one is not None and model_one.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    montant_promotion = prix_jour * promotion_value / 100 * total_days
                    total_red = total_primary + (((100 - percentage) * prix_jour / 100) * total_days)
                    prix_unitaire_red = total_red / total_days
                elif model_two is not None and model_two.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    montant_promotion = prix_jour * promotion_value / 100 * total_days
                    total_red = total_primary + (((100 - percentage) * prix_jour / 100) * total_days)
                    prix_unitaire_red = total_red / total_days
                elif model_three is not None and model_three.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    montant_promotion = prix_jour * promotion_value / 100 * total_days
                    total_red = total_primary + (((100 - percentage) * prix_jour / 100) * total_days)
                    prix_unitaire_red = total_red / total_days
                elif model_four is not None and model_four.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    montant_promotion = prix_jour * promotion_value / 100 * total_days
                    total_red = total_primary + (((100 - percentage) * prix_jour / 100) * total_days)
                    prix_unitaire_red = total_red / total_days
                elif model_five is not None and model_five.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    montant_promotion = prix_jour * promotion_value / 100 * total_days
                    total_red = total_primary + (((100 - percentage) * prix_jour / 100) * total_days)
                    prix_unitaire_red = total_red / total_days
                else :
                    promotion = "no"
                    percentage = 0
                    montant_promotion = 0  
                    montant_code_prime = 0
                    total_red = total_brut
                    prix_unitaire_red = prix_unitaire
                
                solde_anterieur = 0
                if int(client_sold) > 0 : 
                    promotion = "yes"
                    solde_anterieur = client_sold
                    percentage = round(float(client_sold) * 100 / float(total_brut),2)
                    total_red = float(total_brut) - float(client_sold)
                    prix_unitaire_red = float(prix_unitaire) - (float(prime_red) / float(total_days))
                
                if int(prime_red) > 0 :
                    promotion = "yes"
                    solde_anterieur = client_sold
                    percentage = round(float(prime_red) * 100 / float(total_brut),2)
                    total_red = float(total_brut) - float(prime_red)
                    prix_unitaire_red = float(prix_unitaire) - (float(prime_red) / float(total_days))
                
                modeles_ajoutes.add(vehicle.modele.id)

                if vehicle.categorie.id == base_a_category :

                    result.append({
                        "promotion": promotion,
                        "percentage": percentage,
                        "promotion_name":promotion_name,
                        "montant_promotion":montant_promotion,
                        "montant_code_prime":montant_code_prime,
                        "solde_anterieur":solde_anterieur,
                        "currency": "DA",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total_brut,
                        "last_total":total_red,
                        "prix": prix_unitaire,
                        "last_prix": prix_unitaire_red,
                        "klm_name": opt_klm_name ,
                        "klm_name_en": opt_klm_name_en ,
                        "klm_name_ar": opt_klm_name_ar ,
                        "klm_type_tarif": opt_klm_type_tarif ,
                        "klm_price": opt_klm_unit,
                        "klm_total": opt_klm_total,
                        "klm_limit":opt_klm_limit,
                        "klm_penalite":opt_klm_penalite,
                        "carburant_name": opt_carburant_name,
                        "carburant_name_en": opt_carburant_name_en,
                        "carburant_name_ar": opt_carburant_name_ar,
                        "carburant_type_tarif": opt_carburant_type_tarif,
                        "carburant_price": opt_carburant_unit,
                        "carburant_total": opt_carburant_total,
                        "nd_driver_name": opt_nd_driver_name,
                        "nd_driver_name_en": opt_nd_driver_name_en,
                        "nd_driver_name_ar": opt_nd_driver_name_ar,
                        "nd_driver_type_tarif": opt_nd_driver_type_tarif,
                        "nd_driver_price": opt_nd_driver_unit,
                        "nd_driver_total": opt_nd_driver_total,
                        "paiement_name": opt_payment_name,
                        "paiement_name_en": opt_payment_name_en,
                        "paiement_name_ar": opt_payment_name_ar,
                        "paiement_type_tarif": opt_payment_type_tarif,
                        "paiement_price": opt_payment_unit,
                        "payer_maintenant":prix_jour,
                        "paiement_total": opt_payment_total,
                        "sb_5_name": opt_siege_a_name,
                        "sb_5_name_en": opt_siege_a_name_en,
                        "sb_5_name_ar": opt_siege_a_name_ar,
                        "sb_5_type_tarif": opt_siege_a_type_tarif,
                        "sb_5_price": opt_siege_a_unit,
                        "sb_5_total": opt_siege_a_total,
                        "sb_13_name": opt_siege_b_name,
                        "sb_13_name_en": opt_siege_b_name_en,
                        "sb_13_name_ar": opt_siege_b_name_ar,
                        "sb_13_type_tarif": opt_siege_b_type_tarif,
                        "sb_13_price": opt_siege_b_unit,
                        "sb_13_total": opt_siege_b_total,
                        "sb_18_name": opt_siege_c_name,
                        "sb_18_name_en": opt_siege_c_name_en,
                        "sb_18_name_ar": opt_siege_c_name_ar,
                        "sb_18_type_tarif": opt_siege_c_type_tarif,
                        "sb_18_price": opt_siege_c_unit,
                        "sb_18_total": opt_siege_c_total,
                        "base_protection_name": base_a_name,
                        "base_protection_name_en": base_a_name_en,
                        "base_protection_name_ar": base_a_name_ar,
                        "base_protection_type_tarif": base_a_type_tarif,
                        "base_protection_price": base_a_unit,
                        "base_protection_total": base_a_total,
                        "base_protection_caution": base_a_caution,
                        "standart_protection_name": standart_a_name,
                        "standart_protection_name_en": standart_a_name_en,
                        "standart_protection_name_ar": standart_a_name_ar,
                        "standart_protection_type_tarif": standart_a_type_tarif,
                        "standart_protection_price": standart_a_unit,
                        "standart_protection_total": standart_a_total,
                        "standart_protection_caution": standart_a_caution,
                        "max_protection_name": max_a_name,
                        "max_protection_name_en": max_a_name_en,
                        "max_protection_name_ar": max_a_name_ar,
                        "max_protection_type_tarif": max_a_type_tarif,
                        "max_protection_price": max_a_unit,
                        "max_protection_total": max_a_total,
                        "max_protection_caution": max_a_caution,
                        'id': vehicle.id,
                        'model_name': vehicle.model_name,
                        'nombre_deplace': vehicle.nombre_deplace,
                        'nombre_de_bagage': vehicle.nombre_de_bagage,
                        'nombre_de_porte': vehicle.nombre_de_porte,
                        'boite_vitesse': vehicle.boite_vitesse,
                        'carburant': vehicle.carburant,
                        'marketing_text_fr': vehicle.marketing_text_fr,
                        'description': vehicle.modele.description_fr,
                        'description_en': vehicle.modele.description_en,
                        'description_ar': vehicle.modele.description_ar,
                        'photo_link': vehicle.photo_link,
                        'photo_link_nd': vehicle.photo_link_nd,
                        'age_min': vehicle.age_min,
                        'sticker': vehicle.sticker,
                        'vehicule_type':vehicle.modele.vehicule_type,
                        "date_annulation":date_annulation,
                    })
                
                if vehicle.categorie.id == base_b_category :
                    result.append({
                        "promotion": promotion,
                        "percentage": percentage,
                        "promotion_name":promotion_name,
                        "montant_promotion":montant_promotion,
                        "montant_code_prime":montant_code_prime,
                        "solde_anterieur":solde_anterieur,
                        "currency": "DA",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total_brut,
                        "last_total":total_red,
                        "prix": prix_unitaire,
                        "last_prix": prix_unitaire_red,
                        "klm_name": opt_klm_b_name ,
                        "klm_name_en": opt_klm_b_name_en ,
                        "klm_name_ar": opt_klm_b_name_ar ,
                        "klm_type_tarif": opt_klm_b_type_tarif ,
                        "klm_price": opt_klm_b_unit,
                        "klm_total": opt_klm_b_total,
                        "klm_limit":opt_klm_b_limit,
                        "klm_penalite":opt_klm_b_penalite,
                        "carburant_name": opt_carburant_name,
                        "carburant_name_en": opt_carburant_name_en,
                        "carburant_name_ar": opt_carburant_name_ar,
                        "carburant_type_tarif": opt_carburant_type_tarif,
                        "carburant_price": opt_carburant_unit,
                        "carburant_total": opt_carburant_total,
                        "nd_driver_name": opt_nd_driver_name,
                        "nd_driver_name_en": opt_nd_driver_name_en,
                        "nd_driver_name_ar": opt_nd_driver_name_ar,
                        "nd_driver_type_tarif": opt_nd_driver_type_tarif,
                        "nd_driver_price": opt_nd_driver_unit,
                        "nd_driver_total": opt_nd_driver_total,
                        "paiement_name": opt_payment_name,
                        "paiement_name_en": opt_payment_name_en,
                        "paiement_name_ar": opt_payment_name_ar,
                        "paiement_type_tarif": opt_payment_type_tarif,
                        "paiement_price": opt_payment_unit,
                        "payer_maintenant":prix_jour,
                        "paiement_total": opt_payment_total,
                        "sb_5_name": opt_siege_a_name,
                        "sb_5_name_en": opt_siege_a_name_en,
                        "sb_5_name_ar": opt_siege_a_name_ar,
                        "sb_5_type_tarif": opt_siege_a_type_tarif,
                        "sb_5_price": opt_siege_a_unit,
                        "sb_5_total": opt_siege_a_total,
                        "sb_13_name": opt_siege_b_name,
                        "sb_13_name_en": opt_siege_b_name_en,
                        "sb_13_name_ar": opt_siege_b_name_ar,
                        "sb_13_type_tarif": opt_siege_b_type_tarif,
                        "sb_13_price": opt_siege_b_unit,
                        "sb_13_total": opt_siege_b_total,
                        "sb_18_name": opt_siege_c_name,
                        "sb_18_name_en": opt_siege_c_name_en,
                        "sb_18_name_ar": opt_siege_c_name_ar,
                        "sb_18_type_tarif": opt_siege_c_type_tarif,
                        "sb_18_price": opt_siege_c_unit,
                        "sb_18_total": opt_siege_c_total,
                        "base_protection_name": base_b_name,
                        "base_protection_name_en": base_b_name_en,
                        "base_protection_name_ar": base_b_name_ar,
                        "base_protection_type_tarif": base_b_type_tarif,
                        "base_protection_price": base_b_unit,
                        "base_protection_total": base_b_total,
                        "base_protection_caution": base_b_caution,
                        "standart_protection_name": standart_b_name,
                        "standart_protection_name_en": standart_b_name_en,
                        "standart_protection_name_ar": standart_b_name_ar,
                        "standart_protection_type_tarif": standart_b_type_tarif,
                        "standart_protection_price": standart_b_unit,
                        "standart_protection_total": standart_b_total,
                        "standart_protection_caution": standart_b_caution,
                        "max_protection_name": max_b_name,
                        "max_protection_name_en": max_b_name_en,
                        "max_protection_name_ar": max_b_name_ar,
                        "max_protection_type_tarif": max_b_type_tarif,
                        "max_protection_price": max_b_unit,
                        "max_protection_total": max_b_total,
                        "max_protection_caution": max_b_caution,
                        'id': vehicle.id,
                        'model_name': vehicle.model_name,
                        'nombre_deplace': vehicle.nombre_deplace,
                        'nombre_de_bagage': vehicle.nombre_de_bagage,
                        'nombre_de_porte': vehicle.nombre_de_porte,
                        'boite_vitesse': vehicle.boite_vitesse,
                        'carburant': vehicle.carburant,
                        'marketing_text_fr': vehicle.marketing_text_fr,
                        'description': vehicle.modele.description_fr,
                        'description_en': vehicle.modele.description_en,
                        'description_ar': vehicle.modele.description_ar,
                        'photo_link': vehicle.photo_link,
                        'photo_link_nd': vehicle.photo_link_nd,
                        'age_min': vehicle.age_min,
                        'sticker': vehicle.sticker,
                        'vehicule_type':vehicle.modele.vehicule_type,
                        "date_annulation":date_annulation,
                    })

                if vehicle.categorie.id == base_c_category :
                    result.append({
                        "promotion": promotion,
                        "percentage": percentage,
                        "promotion_name":promotion_name,
                        "montant_promotion":montant_promotion,
                        "montant_code_prime":montant_code_prime,
                        "solde_anterieur":solde_anterieur,
                        "currency": "DA",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total_brut,
                        "last_total":total_red,
                        "prix": prix_unitaire,
                        "last_prix": prix_unitaire_red,
                        "klm_name": opt_klm_c_name ,
                        "klm_name_en": opt_klm_c_name_en ,
                        "klm_name_ar": opt_klm_c_name_ar ,
                        "klm_type_tarif": opt_klm_c_type_tarif ,
                        "klm_price": opt_klm_c_unit,
                        "klm_total": opt_klm_c_total,
                        "klm_limit":opt_klm_c_limit,
                        "klm_penalite":opt_klm_c_penalite,
                        "carburant_name": opt_carburant_name,
                        "carburant_name_en": opt_carburant_name_en,
                        "carburant_name_ar": opt_carburant_name_ar,
                        "carburant_type_tarif": opt_carburant_type_tarif,
                        "carburant_price": opt_carburant_unit,
                        "carburant_total": opt_carburant_total,
                        "nd_driver_name": opt_nd_driver_name,
                        "nd_driver_name_en": opt_nd_driver_name_en,
                        "nd_driver_name_ar": opt_nd_driver_name_ar,
                        "nd_driver_type_tarif": opt_nd_driver_type_tarif,
                        "nd_driver_price": opt_nd_driver_unit,
                        "nd_driver_total": opt_nd_driver_total,
                        "paiement_name": opt_payment_name,
                        "paiement_name_en": opt_payment_name_en,
                        "paiement_name_ar": opt_payment_name_ar,
                        "paiement_type_tarif": opt_payment_type_tarif,
                        "paiement_price": opt_payment_unit,
                        "payer_maintenant":prix_jour,
                        "paiement_total": opt_payment_total,
                        "sb_5_name": opt_siege_a_name,
                        "sb_5_name_en": opt_siege_a_name_en,
                        "sb_5_name_ar": opt_siege_a_name_ar,
                        "sb_5_type_tarif": opt_siege_a_type_tarif,
                        "sb_5_price": opt_siege_a_unit,
                        "sb_5_total": opt_siege_a_total,
                        "sb_13_name": opt_siege_b_name,
                        "sb_13_name_en": opt_siege_b_name_en,
                        "sb_13_name_ar": opt_siege_b_name_ar,
                        "sb_13_type_tarif": opt_siege_b_type_tarif,
                        "sb_13_price": opt_siege_b_unit,
                        "sb_13_total": opt_siege_b_total,
                        "sb_18_name": opt_siege_c_name,
                        "sb_18_name_en": opt_siege_c_name_en,
                        "sb_18_name_ar": opt_siege_c_name_ar,
                        "sb_18_type_tarif": opt_siege_c_type_tarif,
                        "sb_18_price": opt_siege_c_unit,
                        "sb_18_total": opt_siege_c_total,
                        "base_protection_name": base_c_name,
                        "base_protection_name_en": base_c_name_en,
                        "base_protection_name_ar": base_c_name_ar,
                        "base_protection_type_tarif": base_c_type_tarif,
                        "base_protection_price": base_c_unit,
                        "base_protection_total": base_c_total,
                        "base_protection_caution": base_c_caution,
                        "standart_protection_name": standart_c_name,
                        "standart_protection_name_en": standart_c_name_en,
                        "standart_protection_name_ar": standart_c_name_ar,
                        "standart_protection_type_tarif": standart_c_type_tarif,
                        "standart_protection_price": standart_c_unit,
                        "standart_protection_total": standart_c_total,
                        "standart_protection_caution": standart_c_caution,
                        "max_protection_name": max_c_name,
                        "max_protection_name_en": max_c_name_en,
                        "max_protection_name_ar": max_c_name_ar,
                        "max_protection_type_tarif": max_c_type_tarif,
                        "max_protection_price": max_c_unit,
                        "max_protection_total": max_c_total,
                        "max_protection_caution": max_c_caution,
                        'id': vehicle.id,
                        'model_name': vehicle.model_name,
                        'nombre_deplace': vehicle.nombre_deplace,
                        'nombre_de_bagage': vehicle.nombre_de_bagage,
                        'nombre_de_porte': vehicle.nombre_de_porte,
                        'boite_vitesse': vehicle.boite_vitesse,
                        'carburant': vehicle.carburant,
                        'marketing_text_fr': vehicle.marketing_text_fr,
                        'description': vehicle.modele.description_fr,
                        'description_en': vehicle.modele.description_en,
                        'description_ar': vehicle.modele.description_ar,
                        'photo_link': vehicle.photo_link,
                        'photo_link_nd': vehicle.photo_link_nd,
                        'age_min': vehicle.age_min,
                        'sticker': vehicle.sticker,
                        'vehicule_type':vehicle.modele.vehicule_type,
                        "date_annulation":date_annulation,
                    })
    else :
        lieu_depart_obj = Lieux.objects.filter(id=lieu_depart_id).first()
        if client_id:
            client_status = check_client(client_id)  
            client = ListeClient.objects.filter(id=client_id).first()
            
            if not client:
                return {"message": "Client introuvable"}
            
            if client_status.get("message") == "negatif":
                return {"message": "Client has a high risk, cannot proceed"}
            elif client_status.get("message") == "positif":
                client_pr = client.reduction if client.reduction is not None else 0
                client_sold = client.solde if client.solde is not None else 0
            else:
                return client_status 
            
        prime_red = 0
        if prime_code and not client_id:
            parent_client = ListeClient.objects.filter(code_prime=prime_code).first() 
            if parent_client :
                parent_sold = SoldeParrainage.objects.filter(name="Solde Parrainage").first()
                prime_red = parent_sold.parrain_solde

        available_vehicles = get_available_vehicles(date_depart, heure_depart, date_retour, heure_retour, zone_id)

        frais_livraison = FraisLivraison.objects.filter(depart_id=lieu_depart_id, retour_id=lieu_retour_id)
        if frais_livraison :
            for frais in frais_livraison:
                total += frais.montant if frais else 0
        else :
            transit_lieu = lieu_depart_obj.zone.transmission_point
            frais_livraison_one = FraisLivraison.objects.filter(depart_id=lieu_depart_id, retour_id=transit_lieu).first()
            frais_livraison_two = FraisLivraison.objects.filter(depart_id=transit_lieu, retour_id=lieu_retour_id).first()
            total += frais_livraison_one.montant + frais_livraison_two.montant if frais_livraison_one and frais_livraison_two else 0
                   
        supplements_one = Supplement.objects.filter(
            Q(heure_debut__lte=heure_depart, heure_fin__gte=heure_depart) 
        ).first()

        total += supplements_one.montant if supplements_one else 0

        supplements_two = Supplement.objects.filter(
            Q(heure_debut__lte=heure_retour, heure_fin__gte=heure_retour)
        ).first()
        total += supplements_two.montant if supplements_two else 0

            

        frais_dossier = search_option("FRAIS_DOSSIER", total_days, lieu_depart)
        total += frais_dossier["total"]
        
        paiement_anticipe = search_option("P_ANTICIPE", total_days, lieu_depart)
        opt_payment_name = paiement_anticipe["name"]
        opt_payment_name_en = paiement_anticipe["name_en"]
        opt_payment_name_ar = paiement_anticipe["name_ar"]
        opt_payment_type_tarif = paiement_anticipe["type_tarif"]
        opt_payment_unit = paiement_anticipe["prix"]
        opt_payment_total = paiement_anticipe["total"]

        klm_illimite = search_option("KLM_ILLIMITED", total_days, lieu_depart)
        opt_klm_name = klm_illimite["name"]
        opt_klm_name_en = klm_illimite["name_en"]
        opt_klm_name_ar = klm_illimite["name_ar"]
        opt_klm_type_tarif = klm_illimite["type_tarif"]
        opt_klm_unit = klm_illimite["prix"]
        opt_klm_total = klm_illimite["total"]
        opt_klm_limit = klm_illimite["limit"]
        opt_klm_penalite = klm_illimite["penalite"]

        klm_illimite_b = search_option("KLM_ILLIMITED_B", total_days, lieu_depart)
        opt_klm_b_name = klm_illimite_b["name"]
        opt_klm_b_name_en = klm_illimite_b["name_en"]
        opt_klm_b_name_ar = klm_illimite_b["name_ar"]
        opt_klm_b_type_tarif = klm_illimite_b["type_tarif"]
        opt_klm_b_unit = klm_illimite_b["prix"]
        opt_klm_b_total = klm_illimite_b["total"]
        opt_klm_b_limit = klm_illimite_b["limit"]
        opt_klm_b_penalite = klm_illimite_b["penalite"]

        klm_illimite_c = search_option("KLM_ILLIMITED_C", total_days, lieu_depart)
        opt_klm_c_name = klm_illimite_c["name"]
        opt_klm_c_name_en = klm_illimite_c["name_en"]
        opt_klm_c_name_ar = klm_illimite_c["name_ar"]
        opt_klm_c_type_tarif = klm_illimite_c["type_tarif"]
        opt_klm_c_unit = klm_illimite_c["prix"]
        opt_klm_c_total = klm_illimite_c["total"]
        opt_klm_c_limit = klm_illimite_c["limit"]
        opt_klm_c_penalite = klm_illimite_c["penalite"]

        nd_driver = search_option("ND_DRIVER", total_days, lieu_depart)
        opt_nd_driver_name = nd_driver["name"]
        opt_nd_driver_name_en = nd_driver["name_en"]
        opt_nd_driver_name_ar = nd_driver["name_ar"]
        opt_nd_driver_type_tarif = nd_driver["type_tarif"]
        opt_nd_driver_unit = nd_driver["prix"]
        opt_nd_driver_total = nd_driver["total"]

        plein_carburant = search_option("P_CARBURANT", total_days, lieu_depart)
        opt_carburant_name = plein_carburant["name"]
        opt_carburant_name_en = plein_carburant["name_en"]
        opt_carburant_name_ar = plein_carburant["name_ar"]
        opt_carburant_type_tarif = plein_carburant["type_tarif"]
        opt_carburant_unit = plein_carburant["prix"]
        opt_carburant_total = plein_carburant["total"]

        siege_a = search_option("S_BEBE_5", total_days, lieu_depart)
        opt_siege_a_name = siege_a["name"]
        opt_siege_a_name_en = siege_a["name_en"]
        opt_siege_a_name_ar = siege_a["name_ar"]
        opt_siege_a_type_tarif = siege_a["type_tarif"]
        opt_siege_a_unit = siege_a["prix"]
        opt_siege_a_total = siege_a["total"]

        siege_b = search_option("S_BEBE_13", total_days, lieu_depart)
        opt_siege_b_name = siege_b["name"]
        opt_siege_b_name_en = siege_b["name_en"]
        opt_siege_b_name_ar = siege_b["name_ar"]
        opt_siege_b_type_tarif = siege_b["type_tarif"]
        opt_siege_b_unit = siege_b["prix"]
        opt_siege_b_total = siege_b["total"]

        siege_c = search_option("S_BEBE_18", total_days, lieu_depart)
        opt_siege_c_name = siege_c["name"]
        opt_siege_c_name_en = siege_c["name_en"]
        opt_siege_c_name_ar = siege_c["name_ar"]
        opt_siege_c_type_tarif = siege_c["type_tarif"]
        opt_siege_c_unit = siege_c["prix"]
        opt_siege_c_total = siege_c["total"]

        base_a = search_option("BASE_P_1", total_days, lieu_depart)
        base_a_name = base_a["name"]
        base_a_name_en = base_a["name_en"]
        base_a_name_ar = base_a["name_ar"]
        base_a_type_tarif = base_a["type_tarif"]
        base_a_unit = base_a["prix"]
        base_a_total = base_a["total"]
        base_a_category = base_a["categorie"]
        base_a_caution = base_a["caution"]

        base_b = search_option("BASE_P_2", total_days, lieu_depart)
        base_b_name = base_b["name"]
        base_b_name_en = base_b["name_en"]
        base_b_name_ar = base_b["name_ar"]
        base_b_type_tarif = base_b["type_tarif"]
        base_b_unit = base_b["prix"]
        base_b_total = base_b["total"]
        base_b_category = base_b["categorie"]
        base_b_caution = base_b["caution"]

        base_c = search_option("BASE_P_3", total_days, lieu_depart)
        base_c_name = base_c["name"]
        base_c_name_en = base_c["name_en"]
        base_c_name_ar = base_c["name_ar"]
        base_c_type_tarif = base_c["type_tarif"]
        base_c_unit = base_c["prix"]
        base_c_total = base_c["total"]
        base_c_category = base_c["categorie"]
        base_c_caution = base_c["caution"]

        standart_a = search_option("STANDART_P_1", total_days, lieu_depart)
        standart_a_name = standart_a["name"]
        standart_a_name_en = standart_a["name_en"]
        standart_a_name_ar = standart_a["name_ar"]
        standart_a_type_tarif = standart_a["type_tarif"]
        standart_a_unit = standart_a["prix"]
        standart_a_total = standart_a["total"]
        standart_a_caution = standart_a["caution"]

        standart_b = search_option("STANDART_P_2", total_days, lieu_depart)
        standart_b_name = standart_b["name"]
        standart_b_name_en = standart_b["name_en"]
        standart_b_name_ar = standart_b["name_ar"]
        standart_b_type_tarif = standart_b["type_tarif"]
        standart_b_unit = standart_b["prix"]
        standart_b_total = standart_b["total"]
        standart_b_caution = standart_b["caution"]

        standart_c = search_option("STANDART_P_3", total_days, lieu_depart)
        standart_c_name = standart_c["name"]
        standart_c_name_en = standart_c["name_en"]
        standart_c_name_ar = standart_c["name_ar"]
        standart_c_type_tarif = standart_c["type_tarif"]
        standart_c_unit = standart_c["prix"]
        standart_c_total = standart_c["total"]
        standart_c_caution = standart_c["caution"]

        max_a = search_option("MAX_P_1", total_days, lieu_depart)
        max_a_name = max_a["name"]
        max_a_name_en = max_a["name_en"]
        max_a_name_ar = max_a["name_ar"]
        max_a_type_tarif = max_a["type_tarif"]
        max_a_unit = max_a["prix"] if max_a["total"] > max_a["min_prix"] else max_a["min_prix"] / total_days
        max_a_total = max_a["total"] if max_a["total"] > max_a["min_prix"] else max_a["min_prix"]
        max_a_caution = max_a["caution"] 

        max_b = search_option("MAX_P_2", total_days, lieu_depart)
        max_b_name = max_b["name"]
        max_b_name_en = max_b["name_en"]
        max_b_name_ar = max_b["name_ar"]
        max_b_type_tarif = max_b["type_tarif"]
        max_b_unit = max_b["prix"] if max_b["total"] > max_b["min_prix"] else max_b["min_prix"] / total_days
        max_b_total = max_b["total"] if max_b["total"] > max_b["min_prix"] else max_b["min_prix"]
        max_b_caution = max_b["caution"]

        max_c = search_option("MAX_P_3", total_days, lieu_depart)
        max_c_name = max_c["name"]
        max_c_name_en = max_c["name_en"]
        max_c_name_ar = max_c["name_ar"]
        max_c_type_tarif = max_c["type_tarif"]
        max_c_unit = max_c["prix"] if max_c["total"] > max_c["min_prix"] else max_c["min_prix"] / total_days
        max_c_total = max_c["total"] if max_c["total"] > max_c["min_prix"] else max_c["min_prix"]
        max_c_caution = max_c["caution"]

        modeles_ajoutes = set()
        total_brut = 0

        for vehicle in available_vehicles:
            if vehicle.modele.id in modeles_ajoutes:
                continue

            tarif = Tarifs.objects.filter(
                modele=vehicle.modele,  
                nbr_de__lte=total_days, 
                nbr_au__gte=total_days,
                zone=lieu_depart.zone
            ).filter(
                Q(date_depart_one__lte=date_depart, date_fin_one__gte=date_retour) |
                Q(date_depart_two__lte=date_depart, date_fin_two__gte=date_retour) |
                Q(date_depart_three__lte=date_depart, date_fin_three__gte=date_retour) |
                Q(date_depart_four__lte=date_depart, date_fin_four__gte=date_retour)
            ).first()

            if tarif:
                prix_jour = tarif.prix 
                total_primary = total
                supplements_valeur = Supplement.objects.filter(valeur__gt=0)
                for supplement in supplements_valeur:
                    start_hour = float(heure_depart[:2]) + float(heure_depart[3:])/60
                    end_hour = float(heure_retour[:2]) + float(heure_retour[3:])/60
                    duration = end_hour - start_hour
                    if duration > supplement.reatrd:
                        total_primary += (prix_jour * supplement.valeur) / 100 
                        
                total_brut = total_primary + (prix_jour * total_days)
                prix_unitaire = total_brut / total_days

                if int(client_pr) > promotion_value :
                    promotion = "yes"
                    percentage = client_pr
                    montant_code_prime = prix_jour * client_pr / 100 * total_days
                    total_red = total_primary + (((100 - percentage) * prix_jour / 100) * total_days)
                    prix_unitaire_red = total_red / total_days
                elif promotion_value > int(client_pr) and promotions.tout_modele == "oui":
                    promotion = "yes"
                    percentage = promotion_value 
                    montant_promotion = prix_jour * promotion_value / 100 * total_days
                    total_red = total_primary + (((100 - percentage) * prix_jour / 100) * total_days)
                    prix_unitaire_red = total_red / total_days
                elif model_one is not None and model_one.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    montant_promotion = prix_jour * promotion_value / 100 * total_days
                    total_red = total_primary + (((100 - percentage) * prix_jour / 100) * total_days)
                    prix_unitaire_red = total_red / total_days
                elif model_two is not None and model_two.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    montant_promotion = prix_jour * promotion_value / 100 * total_days
                    total_red = total_primary + (((100 - percentage) * prix_jour / 100) * total_days)
                    prix_unitaire_red = total_red / total_days
                elif model_three is not None and model_three.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    montant_promotion = prix_jour * promotion_value / 100 * total_days
                    total_red = total_primary + (((100 - percentage) * prix_jour / 100) * total_days)
                    prix_unitaire_red = total_red / total_days
                elif model_four is not None and model_four.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    montant_promotion = prix_jour * promotion_value / 100 * total_days
                    total_red = total_primary + (((100 - percentage) * prix_jour / 100) * total_days)
                    prix_unitaire_red = total_red / total_days
                elif model_five is not None and model_five.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    montant_promotion = prix_jour * promotion_value / 100 * total_days
                    total_red = total_primary + (((100 - percentage) * prix_jour / 100) * total_days)
                    prix_unitaire_red = total_red / total_days
                else :
                    promotion = "no"
                    percentage = 0
                    montant_promotion = 0  
                    montant_code_prime = 0
                    total_red = total_brut
                    prix_unitaire_red = prix_unitaire
                solde_anterieur = 0
                if int(client_sold) > 0 : 
                    promotion = "yes"
                    solde_anterieur = client_sold
                    percentage = round(float(client_sold) * 100 / float(total_brut),2)
                    total_red = float(total_brut) - float(client_sold)
                    prix_unitaire_red = float(prix_unitaire) - (float(prime_red) / float(total_days))
                
                if int(prime_red) > 0 :
                    promotion = "yes"
                    solde_anterieur = prime_red
                    percentage = round(float(prime_red) * 100 / float(total_brut),2)
                    total_red = float(total_brut) - float(prime_red)
                    prix_unitaire_red = float(prix_unitaire) - (float(prime_red) / float(total_days))
                
                modeles_ajoutes.add(vehicle.modele.id)

                if vehicle.categorie.id == base_a_category :

                    result.append({
                        "promotion": promotion,
                        "percentage": percentage,
                        "promotion_name":promotion_name,
                        "montant_promotion":montant_promotion,
                        "montant_code_prime":montant_code_prime,
                        "solde_anterieur":solde_anterieur,
                        "currency": "EUR",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total_brut,
                        "last_total":total_red,
                        "prix": prix_unitaire,
                        "last_prix": prix_unitaire_red,
                        "klm_name": opt_klm_name ,
                        "klm_name_en": opt_klm_name_en ,
                        "klm_name_ar": opt_klm_name_ar ,
                        "klm_type_tarif": opt_klm_type_tarif ,
                        "klm_price": opt_klm_unit,
                        "klm_total": opt_klm_total,
                        "klm_limit":opt_klm_limit,
                        "klm_penalite":opt_klm_penalite,
                        "carburant_name": opt_carburant_name,
                        "carburant_name_en": opt_carburant_name_en,
                        "carburant_name_ar": opt_carburant_name_ar,
                        "carburant_type_tarif": opt_carburant_type_tarif,
                        "carburant_price": opt_carburant_unit,
                        "carburant_total": opt_carburant_total,
                        "nd_driver_name": opt_nd_driver_name,
                        "nd_driver_name_en": opt_nd_driver_name_en,
                        "nd_driver_name_ar": opt_nd_driver_name_ar,
                        "nd_driver_type_tarif": opt_nd_driver_type_tarif,
                        "nd_driver_price": opt_nd_driver_unit,
                        "nd_driver_total": opt_nd_driver_total,
                        "paiement_name": opt_payment_name,
                        "paiement_name_en": opt_payment_name_en,
                        "paiement_name_ar": opt_payment_name_ar,
                        "paiement_type_tarif": opt_payment_type_tarif,
                        "paiement_price": opt_payment_unit,
                        "payer_maintenant":prix_jour,
                        "paiement_total": opt_payment_total,
                        "sb_5_name": opt_siege_a_name,
                        "sb_5_name_en": opt_siege_a_name_en,
                        "sb_5_name_ar": opt_siege_a_name_ar,
                        "sb_5_type_tarif": opt_siege_a_type_tarif,
                        "sb_5_price": opt_siege_a_unit,
                        "sb_5_total": opt_siege_a_total,
                        "sb_13_name": opt_siege_b_name,
                        "sb_13_name_en": opt_siege_b_name_en,
                        "sb_13_name_ar": opt_siege_b_name_ar,
                        "sb_13_type_tarif": opt_siege_b_type_tarif,
                        "sb_13_price": opt_siege_b_unit,
                        "sb_13_total": opt_siege_b_total,
                        "sb_18_name": opt_siege_c_name,
                        "sb_18_name_en": opt_siege_c_name_en,
                        "sb_18_name_ar": opt_siege_c_name_ar,
                        "sb_18_type_tarif": opt_siege_c_type_tarif,
                        "sb_18_price": opt_siege_c_unit,
                        "sb_18_total": opt_siege_c_total,
                         "base_protection_name": base_a_name,
                        "base_protection_name_en": base_a_name_en,
                        "base_protection_name_ar": base_a_name_ar,
                        "base_protection_type_tarif": base_a_type_tarif,
                        "base_protection_price": base_a_unit,
                        "base_protection_total": base_a_total,
                        "base_protection_caution": base_a_caution,
                        "standart_protection_name": standart_a_name,
                        "standart_protection_name_en": standart_a_name_en,
                        "standart_protection_name_ar": standart_a_name_ar,
                        "standart_protection_type_tarif": standart_a_type_tarif,
                        "standart_protection_price": standart_a_unit,
                        "standart_protection_total": standart_a_total,
                        "standart_protection_caution": standart_a_caution,
                        "max_protection_name": max_a_name,
                        "max_protection_name_en": max_a_name_en,
                        "max_protection_name_ar": max_a_name_ar,
                        "max_protection_type_tarif": max_a_type_tarif,
                        "max_protection_price": max_a_unit,
                        "max_protection_total": max_a_total,
                        "max_protection_caution": max_a_caution,
                        'id': vehicle.id,
                        'model_name': vehicle.model_name,
                        'nombre_deplace': vehicle.nombre_deplace,
                        'nombre_de_bagage': vehicle.nombre_de_bagage,
                        'nombre_de_porte': vehicle.nombre_de_porte,
                        'boite_vitesse': vehicle.boite_vitesse,
                        'carburant': vehicle.carburant,
                        'marketing_text_fr': vehicle.marketing_text_fr,
                        'description': vehicle.modele.description_fr,
                        'description_en': vehicle.modele.description_en,
                        'description_ar': vehicle.modele.description_ar,
                        'photo_link': vehicle.photo_link,
                        'photo_link_nd': vehicle.photo_link_nd,
                        'age_min': vehicle.age_min,
                        'sticker': vehicle.sticker,
                        'vehicule_type':vehicle.modele.vehicule_type,
                        "date_annulation":date_annulation,
                    })

                
                if vehicle.categorie.id == base_b_category :
                    result.append({
                        "promotion": promotion,
                        "percentage": percentage,
                        "promotion_name":promotion_name,
                        "montant_promotion":montant_promotion,
                        "montant_code_prime":montant_code_prime,
                        "solde_anterieur":solde_anterieur,
                        "currency": "EUR",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total_brut,
                        "last_total":total_red,
                        "prix": prix_unitaire,
                        "last_prix": prix_unitaire_red,
                        "klm_name": opt_klm_b_name ,
                        "klm_name_en": opt_klm_b_name_en ,
                        "klm_name_ar": opt_klm_b_name_ar ,
                        "klm_type_tarif": opt_klm_b_type_tarif ,
                        "klm_price": opt_klm_b_unit,
                        "klm_total": opt_klm_b_total,
                        "klm_limit":opt_klm_b_limit,
                        "klm_penalite":opt_klm_b_penalite,
                         "carburant_name": opt_carburant_name,
                        "carburant_name_en": opt_carburant_name_en,
                        "carburant_name_ar": opt_carburant_name_ar,
                        "carburant_type_tarif": opt_carburant_type_tarif,
                        "carburant_price": opt_carburant_unit,
                        "carburant_total": opt_carburant_total,
                        "nd_driver_name": opt_nd_driver_name,
                        "nd_driver_name_en": opt_nd_driver_name_en,
                        "nd_driver_name_ar": opt_nd_driver_name_ar,
                        "nd_driver_type_tarif": opt_nd_driver_type_tarif,
                        "nd_driver_price": opt_nd_driver_unit,
                        "nd_driver_total": opt_nd_driver_total,
                        "paiement_name": opt_payment_name,
                        "paiement_name_en": opt_payment_name_en,
                        "paiement_name_ar": opt_payment_name_ar,
                        "paiement_type_tarif": opt_payment_type_tarif,
                        "paiement_price": opt_payment_unit,
                        "payer_maintenant":prix_jour,
                        "paiement_total": opt_payment_total,
                        "sb_5_name": opt_siege_a_name,
                        "sb_5_name_en": opt_siege_a_name_en,
                        "sb_5_name_ar": opt_siege_a_name_ar,
                        "sb_5_type_tarif": opt_siege_a_type_tarif,
                        "sb_5_price": opt_siege_a_unit,
                        "sb_5_total": opt_siege_a_total,
                        "sb_13_name": opt_siege_b_name,
                        "sb_13_name_en": opt_siege_b_name_en,
                        "sb_13_name_ar": opt_siege_b_name_ar,
                        "sb_13_type_tarif": opt_siege_b_type_tarif,
                        "sb_13_price": opt_siege_b_unit,
                        "sb_13_total": opt_siege_b_total,
                        "sb_18_name": opt_siege_c_name,
                        "sb_18_name_en": opt_siege_c_name_en,
                        "sb_18_name_ar": opt_siege_c_name_ar,
                        "sb_18_type_tarif": opt_siege_c_type_tarif,
                        "sb_18_price": opt_siege_c_unit,
                        "sb_18_total": opt_siege_c_total,
                        "base_protection_name": base_b_name,
                        "base_protection_name_en": base_b_name_en,
                        "base_protection_name_ar": base_b_name_ar,
                        "base_protection_type_tarif": base_b_type_tarif,
                        "base_protection_price": base_b_unit,
                        "base_protection_total": base_b_total,
                        "base_protection_caution": base_b_caution,
                        "standart_protection_name": standart_b_name,
                        "standart_protection_name_en": standart_b_name_en,
                        "standart_protection_name_ar": standart_b_name_ar,
                        "standart_protection_type_tarif": standart_b_type_tarif,
                        "standart_protection_price": standart_b_unit,
                        "standart_protection_total": standart_b_total,
                        "standart_protection_caution": standart_b_caution,
                        "max_protection_name": max_b_name,
                        "max_protection_name_en": max_b_name_en,
                        "max_protection_name_ar": max_b_name_ar,
                        "max_protection_type_tarif": max_b_type_tarif,
                        "max_protection_price": max_b_unit,
                        "max_protection_total": max_b_total,
                        "max_protection_caution": max_b_caution,
                        'id': vehicle.id,
                        'model_name': vehicle.model_name,
                        'nombre_deplace': vehicle.nombre_deplace,
                        'nombre_de_bagage': vehicle.nombre_de_bagage,
                        'nombre_de_porte': vehicle.nombre_de_porte,
                        'boite_vitesse': vehicle.boite_vitesse,
                        'carburant': vehicle.carburant,
                        'marketing_text_fr': vehicle.marketing_text_fr,
                        'description': vehicle.modele.description_fr,
                        'description_en': vehicle.modele.description_en,
                        'description_ar': vehicle.modele.description_ar,
                        'photo_link': vehicle.photo_link,
                        'photo_link_nd': vehicle.photo_link_nd,
                        'age_min': vehicle.age_min,
                        'sticker': vehicle.sticker,
                        'vehicule_type':vehicle.modele.vehicule_type,
                        "date_annulation":date_annulation,
                    })

                if vehicle.categorie.id == base_c_category :
                    result.append({
                        "promotion": promotion,
                        "percentage": percentage,
                        "promotion_name":promotion_name,
                        "montant_promotion":montant_promotion,
                        "montant_code_prime":montant_code_prime,
                        "solde_anterieur":solde_anterieur,
                        "currency": "EUR",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total_brut,
                        "last_total":total_red,
                        "prix": prix_unitaire,
                        "last_prix": prix_unitaire_red,
                        "klm_name": opt_klm_c_name ,
                        "klm_type_tarif": opt_klm_c_type_tarif ,
                        "klm_price": opt_klm_c_unit,
                        "klm_total": opt_klm_c_total,
                        "klm_limit":opt_klm_c_limit,
                        "klm_penalite":opt_klm_c_penalite,
                         "carburant_name": opt_carburant_name,
                        "carburant_name_en": opt_carburant_name_en,
                        "carburant_name_ar": opt_carburant_name_ar,
                        "carburant_type_tarif": opt_carburant_type_tarif,
                        "carburant_price": opt_carburant_unit,
                        "carburant_total": opt_carburant_total,
                        "nd_driver_name": opt_nd_driver_name,
                        "nd_driver_name_en": opt_nd_driver_name_en,
                        "nd_driver_name_ar": opt_nd_driver_name_ar,
                        "nd_driver_type_tarif": opt_nd_driver_type_tarif,
                        "nd_driver_price": opt_nd_driver_unit,
                        "nd_driver_total": opt_nd_driver_total,
                        "paiement_name": opt_payment_name,
                        "paiement_name_en": opt_payment_name_en,
                        "paiement_name_ar": opt_payment_name_ar,
                        "paiement_type_tarif": opt_payment_type_tarif,
                        "paiement_price": opt_payment_unit,
                        "payer_maintenant":prix_jour,
                        "paiement_total": opt_payment_total,
                        "sb_5_name": opt_siege_a_name,
                        "sb_5_name_en": opt_siege_a_name_en,
                        "sb_5_name_ar": opt_siege_a_name_ar,
                        "sb_5_type_tarif": opt_siege_a_type_tarif,
                        "sb_5_price": opt_siege_a_unit,
                        "sb_5_total": opt_siege_a_total,
                        "sb_13_name": opt_siege_b_name,
                        "sb_13_name_en": opt_siege_b_name_en,
                        "sb_13_name_ar": opt_siege_b_name_ar,
                        "sb_13_type_tarif": opt_siege_b_type_tarif,
                        "sb_13_price": opt_siege_b_unit,
                        "sb_13_total": opt_siege_b_total,
                        "sb_18_name": opt_siege_c_name,
                        "sb_18_name_en": opt_siege_c_name_en,
                        "sb_18_name_ar": opt_siege_c_name_ar,
                        "sb_18_type_tarif": opt_siege_c_type_tarif,
                        "sb_18_price": opt_siege_c_unit,
                        "sb_18_total": opt_siege_c_total,
                        "base_protection_name": base_c_name,
                        "base_protection_type_tarif": base_c_type_tarif,
                        "base_protection_price": base_c_unit,
                        "base_protection_total": base_c_total,
                        "base_protection_caution": base_c_caution,
                        "standart_protection_name": standart_c_name,
                        "standart_protection_type_tarif": standart_c_type_tarif,
                        "standart_protection_price": standart_c_unit,
                        "standart_protection_total": standart_c_total,
                        "standart_protection_caution": standart_c_caution,
                        "max_protection_name": max_c_name,
                        "max_protection_type_tarif": max_c_type_tarif,
                        "max_protection_price": max_c_unit,
                        "max_protection_total": max_c_total,
                        "max_protection_caution": max_c_caution,
                        'id': vehicle.id,
                        'model_name': vehicle.model_name,
                        'nombre_deplace': vehicle.nombre_deplace,
                        'nombre_de_bagage': vehicle.nombre_de_bagage,
                        'nombre_de_porte': vehicle.nombre_de_porte,
                        'boite_vitesse': vehicle.boite_vitesse,
                        'carburant': vehicle.carburant,
                        'marketing_text_fr': vehicle.marketing_text_fr,
                        'description': vehicle.modele.description_fr,
                        'description_en': vehicle.modele.description_en,
                        'description_ar': vehicle.modele.description_ar,
                        'photo_link': vehicle.photo_link,
                        'photo_link_nd': vehicle.photo_link_nd,
                        'age_min': vehicle.age_min,
                        'sticker': vehicle.sticker,
                        'vehicule_type':vehicle.modele.vehicule_type,
                        "date_annulation":date_annulation,
                    })

    result.sort(key=lambda x: x["last_total"])
    return result 

            

            







    


    

        
 




