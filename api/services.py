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

def protections(ref, country_code):
    try:
        nb_jour = 0
        if country_code == "DZ":
            protections_return = []
            taux = TauxChange.objects.filter(id=2).first()
            taux_change = taux.montant
            reservation = Reservation.objects.filter(name=ref).first()
            if reservation : 
                nb_jour = reservation.nbr_jour_reservation
            
            if not reservation:
                return {"message": "Réservation non trouvée"}

            selected_protection = reservation.opt_protection_name
            category = reservation.categorie.id

            protections = Options.objects.filter(    
                (Q(option_code__icontains="BASE") | 
                Q(option_code__icontains="MAX") | 
                Q(option_code__icontains="STANDART"))
                & Q(categorie_id=category)
            )
            protections_return.append({
                "selected_protection":selected_protection,
            })
            for protection in protections:
                protections_return.append({
                    "protection_name":protection.name,
                    "protection_prix":protection.prix *taux_change,
                    "protection_total":protection.prix * nb_jour * taux_change,
                    "protection_caution":protection.caution * taux_change,
                })
        else :
            protections_return = []
            reservation = Reservation.objects.filter(name=ref).first()
            if reservation : 
                nb_jour = reservation.nbr_jour_reservation
            
            if not reservation:
                return {"message": "Réservation non trouvée"}

            selected_protection = reservation.opt_protection_name
            category = reservation.categorie.id

            protections = Options.objects.filter(    
                (Q(option_code__icontains="BASE") | 
                Q(option_code__icontains="MAX") | 
                Q(option_code__icontains="STANDART"))
                & Q(categorie_id=category)
            )
            protections_return.append({
                "selected_protection":selected_protection,
            })
            for protection in protections:
                protections_return.append({
                    "protection_name":protection.name,
                    "protection_prix":protection.prix,
                    "protection_total":protection.prix * nb_jour,
                    "protection_caution":protection.caution,
                })
            

        return protections_return  

    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}


def modify_protection_request(ref, protection):
    try:   
        reservation = Reservation.objects.filter(name=ref).first()
        nb_jour = reservation.nbr_jour_reservation
        category = reservation.categorie.id
        
        if reservation :
            if protection == "BASE":
                opt_protection = Options.objects.filter(option_code__icontains="BASE", categorie_id=category).first()
                prix = opt_protection.prix
                total = prix * nb_jour

                if total > reservation.opt_protection_total:
                    total_pay = total - reservation.opt_protection_total
                    if reservation.opt_payment_name:
                        return {
                            "new_protection_price":prix,
                            "new_protection_total":total,
                            "to_pay":total_pay
                            }
                    else:
                        return {
                            "new_protection_price":prix,
                            "new_protection_total":total,
                            }
                else : 
                    to_refund = reservation.opt_protection_total - total
                    if reservation.opt_payment_name:
                        return {
                            "new_protection_price":prix,
                            "new_protection_total":total,
                            "to_refund":to_refund
                            }
                    else:
                        return {
                            "new_protection_price":prix,
                            "new_protection_total":total,
                            }
                    
            elif protection == "STANDART":
                opt_protection = Options.objects.filter(option_code__icontains="STANDART", categorie_id=category).first()
                prix = opt_protection.prix
                total = prix * nb_jour

                if total > reservation.opt_protection_total:
                    total_pay = total - reservation.opt_protection_total
                    if reservation.opt_payment_name:
                        return {
                            "new_protection_price":prix,
                            "new_protection_total":total,
                            "to_pay":total_pay
                            }
                    else:
                        return {
                            "new_protection_price":prix,
                            "new_protection_total":total,
                            }
                else : 
                    to_refund = reservation.opt_protection_total - total
                    if reservation.opt_payment_name:
                        return {
                            "new_protection_price":prix,
                            "new_protection_total":total,
                            "to_refund":to_refund
                            }
                    else:
                        return {
                            "new_protection_price":prix,
                            "new_protection_total":total,
                            }
                    
            elif protection == "MAX":
                opt_protection = Options.objects.filter(option_code__icontains="MAX", categorie_id=category).first()
                prix = opt_protection.prix
                total = prix * nb_jour

                if total > reservation.opt_protection_total:
                    total_pay = total - reservation.opt_protection_total
                    if reservation.opt_payment_name:
                        return {
                            "new_protection_price":prix,
                            "new_protection_total":total,
                            "to_pay":total_pay
                            }
                    else:
                        return {
                            "new_protection_price":prix,
                            "new_protection_total":total,
                            }
                else : 
                    to_refund = reservation.opt_protection_total - total
                    if reservation.opt_payment_name:
                        return {
                            "new_protection_price":prix,
                            "new_protection_total":total,
                            "to_refund":to_refund
                            }
                    else:
                        return {
                            "new_protection_price":prix,
                            "new_protection_total":total,
                            }
                    
            else : 
                return {"message": "pas possible de modifier"}
        
        else : 
                return {"message": "pas possible de modifier"}

    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}

def verify_client(email, nom, prenom, birthday, permis, phone):
    try:
        client_id=ListeClient.objects.filter(nom=nom, prenom=prenom).first()
        if client_id :
            if client_id.risque == "eleve":
                return {"message":"negatif"}
            else :
                return client_id.id

        else :
            client_verify=ListeClient.objects.filter(nom=prenom, prenom=nom).first()
            if client_verify:
                if client_verify.risque == "eleve":
                    return {"message":"negatif"}
                else :
                    return client_verify.id
            else:
                client = ListeClient.objects.create(
                    email=email,
                    nom=nom,
                    prenom=prenom,
                    date_de_naissance=birthday,
                    mobile=phone,
                    date_de_permis=permis,
                    risque="faible"
                )
                return client.id


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


def add_options_request(ref, nd_driver, carburant, sb_a, sb_b, sb_c,nom, prenom, birthday, permis_date):
    try:
        result = []
        reservations = Reservation.objects.filter(name=ref).first()

        if nom and prenom and birthday and permis_date :
            email = reservations.email
            phone = reservations.telephone
            verify_client(                
                email = email,
                nom = nom,
                prenom = prenom,
                birthday = birthday,
                permis = permis_date,
                phone =  phone
            )
        if not reservations:
            return {"message" : "pas de reservation avce cet id "}
        result.append({
            "nbr_jour": reservations.nbr_jour_reservation,
        })
        to_pay_total = 0
        if nd_driver == "yes" and not reservations.opt_nd_driver_name:
            tarif_nd = Options.objects.filter(option_code="ND_DRIVER").first()
            nd_driver_price = tarif_nd.prix
            nd_driver_name = tarif_nd.name
            nd_driver_total = nd_driver_price * reservations.nbr_jour_reservation
            to_pay_total += nd_driver_total
            result.append({
                "nd_driver_name":nd_driver_name,
                "nd_driver_price": nd_driver_price,
                "nd_driver_total": nd_driver_total,
            })

        if carburant == "yes" and not reservations.opt_plein_carburant_name:
            tarif_carburant = Options.objects.filter(option_code="P_CARBURANT").first()
            carburant = tarif_carburant.name
            carburant_price = tarif_carburant.prix
            carburant_total = carburant_price * reservations.nbr_jour_reservation
            to_pay_total += carburant_total
            result.append({
                "carburant_name": carburant,
                "carburant_price": carburant_price ,
                "carburant_total": carburant_total,
            })

        if sb_a == "yes" and not reservations.opt_siege_a_name:
            tarif_sb_a = Options.objects.filter(option_code="S_BEBE_5").first()
            sb_a_name = tarif_sb_a.name
            sb_a_price = tarif_sb_a.prix
            sb_a_total = sb_a_price * reservations.nbr_jour_reservation
            to_pay_total += sb_a_total
            result.append({
                "sb_a_name": sb_a_name,
                "sb_a_price": sb_a_price ,
                "sb_a_total": sb_a_total,
            })

        if sb_b == "yes" and not reservations.opt_siege_b_name:
            tarif_sb_b = Options.objects.filter(option_code="S_BEBE_13").first()
            sb_b_name = tarif_sb_b.name
            sb_b_price = tarif_sb_b.prix
            sb_b_total = sb_b_price * reservations.nbr_jour_reservation
            to_pay_total += sb_b_total
            result.append({
                "sb_b_name": sb_b_name,
                "sb_b_price": sb_b_price ,
                "sb_b_total": sb_b_total,
            })
        if sb_c == "yes" and not reservations.opt_siege_c_name:
            tarif_sb_c = Options.objects.filter(option_code="S_BEBE_18").first()
            sb_c_name = tarif_sb_c.name
            sb_c_price = tarif_sb_c.prix
            sb_c_total = sb_c_price * reservations.nbr_jour_reservation
            to_pay_total += sb_c_total
            result.append({
                "sb_c_name": sb_c_name,
                "sb_c_price": sb_c_price ,
                "sb_c_total": sb_c_total,
            })
        
        if to_pay_total > 0 :
            result.append({
                "to_pay_total": to_pay_total,
            })
        
        to_refund_total = 0
        
        if nd_driver == "no" and reservations.opt_nd_driver_name:
            tarif_nd = Options.objects.filter(option_code="ND_DRIVER").first()
            nd_driver_price = tarif_nd.prix
            nd_driver_name = tarif_nd.name
            nd_driver_total = nd_driver_price * reservations.nbr_jour_reservation
            to_refund_total += nd_driver_total
            result.append({
                "nd_driver_name":nd_driver_name,
                "to_refund": nd_driver_total,
            })
        if carburant == "no" and reservations.opt_plein_carburant_name:
            tarif_carburant = Options.objects.filter(option_code="P_CARBURANT").first()
            carburant = tarif_carburant.name
            carburant_price = tarif_carburant.prix
            carburant_total = carburant_price * reservations.nbr_jour_reservation
            to_refund_total += carburant_total
            result.append({
                "carburant_name": carburant,
                "to_refund": carburant_total,
            })
        if sb_a == "no" and reservations.opt_siege_a_name:
            tarif_sb_a = Options.objects.filter(option_code="S_BEBE_5").first()
            sb_a_name = tarif_sb_a.name
            sb_a_price = tarif_sb_a.prix
            sb_a_total = sb_a_price * reservations.nbr_jour_reservation
            to_refund_total += sb_a_total
            result.append({
                "sb_a_name": sb_a_name,
                "to_refund": sb_a_total,
            })

        if sb_b == "no" and reservations.opt_siege_b_name:
            tarif_sb_b = Options.objects.filter(option_code="S_BEBE_13").first()
            sb_b_name = tarif_sb_b.name
            sb_b_price = tarif_sb_b.prix
            sb_b_total = sb_b_price * reservations.nbr_jour_reservation
            to_refund_total += sb_b_total
            result.append({
                "sb_b_name": sb_b_name,
                "to_refund": sb_b_total,
            })
        if sb_c == "no" and reservations.opt_siege_c_name:
            tarif_sb_c = Options.objects.filter(option_code="S_BEBE_18").first()
            sb_c_name = tarif_sb_c.name
            sb_c_price = tarif_sb_c.prix
            sb_c_total = sb_c_price * reservations.nbr_jour_reservation
            to_refund_total += sb_c_total
            result.append({
                "sb_c_name": sb_c_name,
                "to_refund": sb_c_total,
            })
        
        if to_refund_total > 0 :
            result.append({
                "to_refund_total": to_refund_total,
            })

        return result
    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}

def mes_reservations(client_id):
    try:
        reservations = Reservation.objects.filter(client__id=client_id)
        if not reservations.exists():
            return {"message": "Aucune réservation trouvée pour ce client."}
        result = []
        for reservation in reservations:
            can_be_modified = "yes"
            if reservation.status != "confirmee" :
                can_be_modified = "no"
            result.append({
                "id":reservation.id,
                "reference": reservation.name,
                "lieu_depart": reservation.lieu_depart.name,
                "lieu_retour": reservation.lieu_retour.name,
                "date_dapart": reservation.date_heure_debut,
                "date_retour": reservation.date_heure_fin,
                "duree": reservation.nbr_jour_reservation,
                "caution": reservation.opt_protection_caution,
                "total": reservation.total_reduit_euro,
                "create_date": reservation.create_date,
                "status": reservation.status,
                "model_name": reservation.model_name,
                "photo_link": reservation.photo_link,
                "marketing_text_fr": reservation.marketing_text_fr,
                "can_be_modified": can_be_modified,
            })

        return {"reservations": result}

    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}


def cencel_request(ref):
    try:
        ma_reservation = Reservation.objects.filter(name=ref)
        if not ma_reservation.exists():
            return {"message": "Réservation non trouvée."}
        for record in ma_reservation:
            frais_dossier = record.frais_de_dossier
            un_jour = record.prix_jour
            if record.opt_payment_name :
                rembourssement = True
            else: rembourssement = False
            reference = record.name
            lieu_depart = record.lieu_depart.name
            date_depart = record.date_heure_debut
            raisons_annulation = AnnulerRaison.objects.filter()
            reasons = [raison.name for raison in raisons_annulation]

        result = {
            "reference":reference,
            "lieu_depart":lieu_depart,
            "date_depart":date_depart,
            "frais_dossier":frais_dossier,
            "frais_annulation":un_jour,
            "refund":rembourssement,
            "seasons":reasons,
                  }
        return result
    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}

def verify_and_calculate(ref, lieu_depart, lieu_retour, date_depart, heure_depart, date_retour, heure_retour):
    try:
        result = []
        date_depart_heure = datetime.strptime(f"{date_depart} {heure_depart}", '%Y-%m-%d %H:%M')
        date_retour_heure = datetime.strptime(f"{date_retour} {heure_retour}", '%Y-%m-%d %H:%M')

        date_depart_heure -= timedelta(hours=1)
        date_retour_heure -= timedelta(hours=1)

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

                    frais_livraison = FraisLivraison.objects.filter(depart_id=lieu_depart, retour_id=lieu_retour)
                    for frais in frais_livraison:
                        total += frais.montant if frais else 0

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

                if total > 0:
                    prix_par_jour = total / total_days if total_days > 0 else 0
                    total_ = get_options_total + total
                
                result.append({
                    'is_available':"yes",
                    'old_total':get_total,
                    'new_total':total_,
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

def option_ma_reservation(ref, country_code):
    try:
        result = []
        reservation = Reservation.objects.filter(name=ref).first()
        category = reservation.categorie.id
        nb_jour = reservation.nbr_jour_reservation
        options = Options.objects.filter(    
            (Q(option_code__icontains="KLM_ILLIMITED") | 
            Q(option_code__icontains="P_ANTICIPE") | 
            Q(option_code__icontains="P_CARBURANT") | 
            Q(option_code__icontains="S_BEBE_5") | 
            Q(option_code__icontains="S_BEBE_13") | 
            Q(option_code__icontains="S_BEBE_18") | 
            Q(option_code__icontains="ND_DRIVER"))
            & (Q(categorie_id=category)|
            Q(categorie=None)
            ))
        if country_code == "DZ":
            taux= TauxChange.objects.filter(id=2).first()
            taux_change = taux.montant
            for option in options :
                option_total = option.prix * nb_jour * taux_change if option.type_tarif == "jour" else option.prix * taux_change
                if "KLM_ILLIMITED" in option.option_code :
                    result.append({
                        "option_name": option.name,
                        "option_prix":option.prix * taux_change,
                        "option_total": option_total,
                        "klm_limit":option.limit_Klm * nb_jour,
                        "penalite_klm": option.penalite_Klm * int(taux_change)
                    })
                else :
                    result.append({
                        "option_name": option.name,
                        "option_prix":option.prix * taux_change,
                        "option_total": option_total,
                    })
        else :
            for option in options :
                option_total = option.prix * nb_jour if option.type_tarif == "jour" else option.prix
                if "KLM_ILLIMITED" in option.option_code :
                    result.append({
                        "option_name": option.name,
                        "option_prix":option.prix,
                        "option_total": option_total,
                        "klm_limit":option.limit_Klm * nb_jour,
                        "penalite_klm": option.penalite_Klm
                    })
                else :
                    result.append({
                        "option_name": option.name,
                        "option_prix":option.prix,
                        "option_total": option_total,
                    })

        return result

    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}

def ma_reservation_detail(ref, email, country_code):
    try:
        ma_reservation =Reservation.objects.filter(name=ref, email=email).first()
        if not ma_reservation :
            return {"error": "reservation non trouvé"}
        result =[]
        annulation = ConditionAnnulation.objects.filter(id=1).first()
        periodes = Periode.objects.all()
        date = ma_reservation.date_heure_debut.date()
        saison_id = None
        for periode in periodes:
            if periode.date_debut <= date <= periode.date_fin:
                saison_id = periode.saison
                break
        jour_annulation = 0
        if saison_id == annulation.haute_saison :
            jour_annulation += annulation.haute_montant
        else :
            jour_annulation += annulation.basse_montant
        
        today = datetime.today().date()
        can_cancel = "yes" if (date - today).days >= jour_annulation else "no"
        can_midify = "yes" if (date - today).days >= 2 else "no"
        retour = ma_reservation.date_heure_fin.date()
        can_modify_return = "yes" if (retour - today).days >= 2 else "no"
        address = ma_reservation.lieu_depart.address
        frais_livraison = ma_reservation.frais_de_dossier
        lieu_rdv = ma_reservation.lieu_depart.rendez_vous
        
        if country_code =="DZ":
            taux = TauxChange.objects.filter(id=2).first()
            taux_change = taux.montant
            if ma_reservation :
                result.append({
                    'can_cancel': can_cancel,
                    "can_midify":can_midify,
                    "can_modify_return":can_modify_return,
                    'id': ma_reservation.id,
                    'reference': ma_reservation.name,
                    'client_nom': ma_reservation.nom,
                    'client_perenom': ma_reservation.prenom,
                    'lieu_depart': ma_reservation.lieu_depart.id,
                    'lieu_retour': ma_reservation.lieu_retour.id,
                    'address_lieu': address,
                    'lieu_rdv': lieu_rdv,
                    'frais_livraison':frais_livraison,
                    'date_depart': ma_reservation.date_heure_debut,
                    'date_retour': ma_reservation.date_heure_fin,
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
                })
        else :  
            if ma_reservation :
                result.append({
                    'can_cancel': can_cancel,
                    "can_midify":can_midify,
                    "can_modify_return":can_modify_return,
                    'id':ma_reservation.id,
                    'reference': ma_reservation.name,
                    'client_nom': ma_reservation.nom,
                    'client_perenom': ma_reservation.prenom,
                    'lieu_depart': ma_reservation.lieu_depart.id,
                    'lieu_retour': ma_reservation.lieu_retour.id,
                    'address_lieu': address,
                    'lieu_rdv': lieu_rdv,
                    'frais_livraison':frais_livraison,
                    'date_depart': ma_reservation.date_heure_debut,
                    'date_retour': ma_reservation.date_heure_fin,
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
                })  

        return result

    except Exception as e:
        return {"message": f"Erreur: {str(e)}", "reservation_id": None}

def create_account(email, nom, prenom, phone , birthday, permis_date):
    try:
        client = ListeClient.objects.filter(nom=nom, prenom=prenom).first()
        if client:
            return {"created": False, "message": "Le client existe déjà avec ce nom et prénom."}
        
        client = ListeClient.objects.filter(nom=prenom, prenom=nom).first()
        if client:
            return {"created": False, "message": "Le client existe déjà avec prénom et nom inversés."}
        
        client = ListeClient.objects.create(
            email=email,
            nom=nom,
            prenom=prenom,
            telephone=phone,
            date_de_naissance=birthday,
            date_de_permis=permis_date
        )
        otp_response = otp_send(email)
        if not otp_response["sent"]:
            return {"created": True, "message": "Client créé, mais échec de l'envoi de l'OTP.", "client_id": client.id}
        
        return {"created": True, "message": "Client créé avec succès et OTP envoyé.", "client_id": client.id}
            
    except Exception as e:
        return {"message": f"Erreur inattendue : {str(e)}", "client_id": None}

from django.utils.html import strip_tags
from django.template.loader import render_to_string

def otp_send(email):
    try:
        client = ListeClient.objects.filter(email=email).first()
        if not client:
            return {"message": "Aucun client trouvé avec cet email.", "client_id": None}

        otp_code = f"{random.randint(100000, 999999)}"
        client.otp = otp_code
        client.otp_created_at = datetime.now()
        client.save()

        sujet = "Votre code OTP"
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
            return {"sent": True, "message": "Email envoyé avec succès.", "client_id": client.id}
        except Exception as e:
            return {"message": f"Erreur lors de l'envoi de l'email : {str(e)}", "client_id": client.id}
    except Exception as e:
        return {"message": f"Erreur inattendue : {str(e)}", "client_id": None}
    
def otp_verify(email, otp, client_id):
    try:
        client = ListeClient.objects.filter(id=client_id).first()
        if not client:
            return {"success": False, "message": "Aucun client trouvé avec cet email."}

        if str(client.otp) == str(otp):
            client.otp = None
            client.otp_created_at = None
            client.save()
            return {"success": True, "message": "OTP vérifié avec succès."}
        else:
            return {"success": False, "message": "OTP invalide ou expiré.", "otp": client.otp}
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
        etat_reservation__in=["reserve", "loue"],  
    ).values_list("vehicule_id", flat=True)

    available_vehicles = Vehicule.objects.filter(
        active_test=True,  
        date_debut_service__lte=date_heure_debut.date(),
        zone_id=int(zone) 
    ).exclude(id__in=reserved_vehicles)  

    return available_vehicles

def search_option(code, total_days):
    try:
        option = Options.objects.filter(option_code=code).first()
        return {
            'name': option.name,
            'prix': option.prix,
            'total': option.prix * total_days if option.type_tarif == 'jour' else option.prix,
            'categorie': option.categorie.id if option.categorie else None,
            'limit': (option.limit_Klm or 0) * total_days,
            'penalite': option.penalite_Klm or 0,
            'caution': option.caution or 0
        }
    except Options.DoesNotExist:
        return {'name': None, 'prix': 0, 'total': 0, 'limit': 0, 'penalite': 0, 'caution': 0, 'categorie': 0}
 
def search_option_dzd(code, total_days):
    try:
        option = Options.objects.filter(option_code=code).first()
        taux = TauxChange.objects.filter(id=2).first()
        
        if not option or not taux:
            return {'name': None, 'prix': 0, 'total': 0, 'limit': 0, 'penalite': 0, 'caution': 0, 'categorie': 0}
        
        prix = float(option.prix) if option.prix is not None else 0
        montant_taux = float(taux.montant) if taux.montant is not None else 0
        limit_Klm = float(option.limit_Klm) if option.limit_Klm is not None else 0
        penalite_Klm = float(option.penalite_Klm) if option.penalite_Klm is not None else 0
        caution = float(option.caution) if option.caution is not None else 0

        return {
            'name': option.name,
            'prix': prix * montant_taux,
            'total': prix * float(total_days) * montant_taux if option.type_tarif == 'jour' else prix * montant_taux,
            'categorie': option.categorie.id if option.categorie else None,
            'limit': limit_Klm * total_days,
            'penalite': penalite_Klm * montant_taux,
            'caution': caution * montant_taux
        }
    
    except Options.DoesNotExist:
        return {'name': None, 'prix': 0, 'total': 0, 'limit': 0, 'penalite': 0, 'caution': 0, 'categorie': 0} 
    
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

def search_result(lieu_depart_id, lieu_retour_id, date_depart, heure_depart, date_retour, heure_retour, client_id, prime_code, country_code):
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
    promotions = Promotion.objects.filter(
        debut_visibilite__lte=today,
        fin_visibilite__gte=today,
        date_debut__lte=date_depart,
        date_fin__gte=date_retour,
        active_passive=True
    ).first()
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

    if country_code == "DZ":
        if client_id:
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
            parent_client = ListeClient.objects.filter(prime_code=prime_code).first() 
            if parent_client :
                parent_sold = SoldeParrainage.objects.filter(name="Solde Parrainage").first()
                prime_red = float(parent_sold.parrain_solde) * taux_change if parent_sold.parrain_solde is not None else 0

        available_vehicles = get_available_vehicles(date_depart, heure_depart, date_retour, heure_retour, zone_id)

        frais_livraison = FraisLivraison.objects.filter(depart_id=lieu_depart_id, retour_id=lieu_retour_id)
        for frais in frais_livraison:
            total += float(frais.montant) * taux_change if frais.montant is not None else 0        

        supplements = Supplement.objects.filter(
            Q(heure_debut__lte=heure_depart, heure_fin__gte=heure_depart) |
            Q(heure_debut__lte=heure_retour, heure_fin__gte=heure_retour)
        )
        for supplement in supplements:
            total += float(supplement.montant) * taux_change if supplement else 0

        frais_dossier = search_option_dzd("FRAIS_DOSSIER", total_days)
        total += frais_dossier["total"] * taux_change

        paiement_anticipe = search_option_dzd("P_ANTICIPE", total_days)
        opt_payment_name = paiement_anticipe["name"]
        opt_payment_unit = paiement_anticipe["prix"]
        opt_payment_total = paiement_anticipe["total"]

        klm_illimite = search_option_dzd("KLM_ILLIMITED", total_days)
        opt_klm_name = klm_illimite["name"]
        opt_klm_unit = klm_illimite["prix"]
        opt_klm_total = klm_illimite["total"]
        opt_klm_limit = klm_illimite["limit"]
        opt_klm_penalite = klm_illimite["penalite"]

        klm_illimite_b = search_option_dzd("KLM_ILLIMITED_B", total_days)
        opt_klm_b_name = klm_illimite_b["name"]
        opt_klm_b_unit = klm_illimite_b["prix"]
        opt_klm_b_total = klm_illimite_b["total"]
        opt_klm_b_limit = klm_illimite_b["limit"]
        opt_klm_b_penalite = klm_illimite_b["penalite"]

        klm_illimite_c = search_option_dzd("KLM_ILLIMITED_C", total_days)
        opt_klm_c_name = klm_illimite_c["name"]
        opt_klm_c_unit = klm_illimite_c["prix"]
        opt_klm_c_total = klm_illimite_c["total"]
        opt_klm_c_limit = klm_illimite_c["limit"]
        opt_klm_c_penalite = klm_illimite_c["penalite"]

        nd_driver = search_option_dzd("ND_DRIVER", total_days)
        opt_nd_driver_name = nd_driver["name"]
        opt_nd_driver_unit = nd_driver["prix"]
        opt_nd_driver_total = nd_driver["total"]

        plein_carburant = search_option_dzd("P_CARBURANT", total_days)
        opt_carburant_name = plein_carburant["name"]
        opt_carburant_unit = plein_carburant["prix"]
        opt_carburant_total = plein_carburant["total"]

        siege_a = search_option_dzd("S_BEBE_5", total_days)
        opt_siege_a_name = siege_a["name"]
        opt_siege_a_unit = siege_a["prix"]
        opt_siege_a_total = siege_a["total"]

        siege_b = search_option_dzd("S_BEBE_13", total_days)
        opt_siege_b_name = siege_b["name"]
        opt_siege_b_unit = siege_b["prix"]
        opt_siege_b_total = siege_b["total"]

        siege_c = search_option_dzd("S_BEBE_18", total_days)
        opt_siege_c_name = siege_c["name"]
        opt_siege_c_unit = siege_c["prix"]
        opt_siege_c_total = siege_c["total"]
    
        base_a = search_option_dzd("BASE_P_1", total_days)
        base_a_name = base_a["name"]
        base_a_unit = base_a["prix"]
        base_a_total = base_a["total"]
        base_a_category = base_a["categorie"]
        base_a_caution = base_a["caution"]

        base_b = search_option_dzd("BASE_P_2", total_days)
        base_b_name = base_b["name"]
        base_b_unit = base_b["prix"]
        base_b_total = base_b["total"]
        base_b_category = base_b["categorie"]
        base_b_caution = base_b["caution"]
        
        base_c = search_option_dzd("BASE_P_3", total_days)
        base_c_name = base_c["name"]
        base_c_unit = base_c["prix"]
        base_c_total = base_c["total"]
        base_c_category = base_c["categorie"]
        base_c_caution = base_c["caution"]
        
        standart_a = search_option_dzd("STANDART_P_1", total_days)
        standart_a_name = standart_a["name"]
        standart_a_unit = standart_a["prix"]
        standart_a_total = standart_a["total"]
        standart_a_caution = standart_a["caution"]

        standart_b = search_option_dzd("STANDART_P_2", total_days)
        standart_b_name = standart_b["name"]
        standart_b_unit = standart_b["prix"]
        standart_b_total = standart_b["total"]
        standart_b_caution = standart_b["caution"]
        
        standart_c = search_option_dzd("STANDART_P_3", total_days)
        standart_c_name = standart_c["name"]
        standart_c_unit = standart_c["prix"]
        standart_c_total = standart_c["total"]
        standart_c_caution = standart_c["caution"]

        max_a = search_option_dzd("MAX_P_1", total_days)
        max_a_name = max_a["name"]
        max_a_unit = max_a["prix"]
        max_a_total = max_a["total"]
        max_a_caution = max_a["caution"]

        max_b = search_option_dzd("MAX_P_2", total_days)
        max_b_name = max_b["name"]
        max_b_unit = max_b["prix"]
        max_b_total = max_b["total"]
        max_b_caution = max_b["caution"]
        
        max_c = search_option_dzd("MAX_P_3", total_days)
        max_c_name = max_c["name"]
        max_c_unit = max_c["prix"]
        max_c_total = max_c["total"]
        max_c_caution = max_c["caution"]

        modeles_ajoutes = set()
        total_brut = 0

        for vehicle in available_vehicles:
            if vehicle.modele.id in modeles_ajoutes:
                continue

            tarif = Tarifs.objects.filter(
                modele=vehicle.modele,  
                nbr_de__lte=total_days, 
                nbr_au__gte=total_days
            ).filter(
                Q(date_depart_one__lte=date_depart, date_fin_one__gte=date_retour) |
                Q(date_depart_two__lte=date_depart, date_fin_two__gte=date_retour) |
                Q(date_depart_three__lte=date_depart, date_fin_three__gte=date_retour) |
                Q(date_depart_four__lte=date_depart, date_fin_four__gte=date_retour)
            ).first()

            if tarif:
                prix_jour = float(tarif.prix) * taux_change
                total_brut = total + (prix_jour * total_days)
                for supplement in supplements:

                    start_hour = float(heure_depart[:2]) + float(heure_depart[3:])/60
                    end_hour = float(heure_retour[:2]) + float(heure_retour[3:])/60

                    duration = end_hour - start_hour

                    if duration > supplement.reatrd:
                        total += (prix_jour * supplement.valeur) / 100
                if total_brut > 0 and total_days > 0:
                    prix_unitaire = total_brut / total_days
                
                modeles_ajoutes.add(vehicle.modele.id)
                if int(client_pr) > promotion_value :
                    promotion = "yes"
                    percentage = client_pr
                    total_red = (100 - percentage) * total_brut / 100
                    prix_unitaire_red = total_red / total_days
                elif promotion_value > int(client_pr) and promotions.tout_modele == "oui":
                    promotion = "yes"
                    percentage = promotion_value
                    total_red = (100 - percentage) * total_brut / 100
                    prix_unitaire_red = total_red / total_days
                elif model_one is not None and model_one.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    total_red = (100 - percentage) * total_brut / 100
                    prix_unitaire_red = total_red / total_days
                elif model_two is not None and model_two.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    total_red = (100 - percentage) * total_brut / 100
                    prix_unitaire_red = total_red / total_days
                elif model_three is not None and model_three.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    total_red = (100 - percentage) * total_brut / 100
                    prix_unitaire_red = total_red / total_days
                elif model_four is not None and model_four.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    total_red = (100 - percentage) * total_brut / 100
                    prix_unitaire_red = total_red / total_days
                elif model_five is not None and model_five.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    total_red = (100 - percentage) * total_brut / 100
                    prix_unitaire_red = total_red / total_days
                else :
                    promotion = "no"
                    percentage = 0
                    total_red = total_brut
                    prix_unitaire_red = prix_unitaire 

                if int(client_sold) > 0 : 
                    total_brut = total_brut - client_sold
                
                if int(prime_red) > 0 :
                    total_brut = total_brut - prime_red

                if vehicle.categorie.id == base_a_category :

                    result.append({
                        "promotion": promotion,
                        "percentage": percentage,
                        "currency": "DZD",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total_brut,
                        "last_total":total_red,
                        "prix": prix_unitaire,
                        "last_prix": prix_unitaire_red,
                        "klm_name": opt_klm_name ,
                        "klm_price": opt_klm_unit,
                        "klm_total": opt_klm_total,
                        "klm_limit":opt_klm_limit,
                        "klm_penalite":opt_klm_penalite,
                        "carburant_name": opt_carburant_name,
                        "carburant_price": opt_carburant_unit,
                        "carburant_total": opt_carburant_total,
                        "nd_driver_name": opt_nd_driver_name,
                        "nd_driver_price": opt_nd_driver_unit,
                        "nd_driver_total": opt_nd_driver_total,
                        "paiement_name": opt_payment_name,
                        "paiement_price": opt_payment_unit,
                        "paiement_total": opt_payment_total,
                        "sb_5_name": opt_siege_a_name,
                        "sb_5_price": opt_siege_a_unit,
                        "sb_5_total": opt_siege_a_total,
                        "sb_13_name": opt_siege_b_name,
                        "sb_13_price": opt_siege_b_unit,
                        "sb_13_total": opt_siege_b_total,
                        "sb_18_name": opt_siege_c_name,
                        "sb_18_price": opt_siege_c_unit,
                        "sb_18_total": opt_siege_c_total,
                        "base_protection_name": base_a_name,
                        "base_protection_price": base_a_unit,
                        "base_protection_total": base_a_total,
                        "base_protection_caution": base_a_caution,
                        "standart_protection_name": standart_a_name,
                        "standart_protection_price": standart_a_unit,
                        "standart_protection_total": standart_a_total,
                        "standart_protection_caution": standart_a_caution,
                        "max_protection_name": max_a_name,
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
                        "currency": "DZD",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total_brut,
                        "last_total":total_red,
                        "prix": prix_unitaire,
                        "last_prix": prix_unitaire_red,
                        "klm_name": opt_klm_b_name ,
                        "klm_price": opt_klm_b_unit,
                        "klm_total": opt_klm_b_total,
                        "klm_limit":opt_klm_b_limit,
                        "klm_penalite":opt_klm_b_penalite,
                        "carburant_name": opt_carburant_name,
                        "carburant_price": opt_carburant_unit,
                        "carburant_total": opt_carburant_total,
                        "nd_driver_name": opt_nd_driver_name,
                        "nd_driver_price": opt_nd_driver_unit,
                        "nd_driver_total": opt_nd_driver_total,
                        "paiement_name": opt_payment_name,
                        "paiement_price": opt_payment_unit,
                        "paiement_total": opt_payment_total,
                        "sb_5_name": opt_siege_a_name,
                        "sb_5_price": opt_siege_a_unit,
                        "sb_5_total": opt_siege_a_total,
                        "sb_13_name": opt_siege_b_name,
                        "sb_13_price": opt_siege_b_unit,
                        "sb_13_total": opt_siege_b_total,
                        "sb_18_name": opt_siege_c_name,
                        "sb_18_price": opt_siege_c_unit,
                        "sb_18_total": opt_siege_c_total,
                        "base_protection_name": base_b_name,
                        "base_protection_price": base_b_unit,
                        "base_protection_total": base_b_total,
                        "base_protection_caution": base_b_caution,
                        "standart_protection_name": standart_b_name,
                        "standart_protection_price": standart_b_unit,
                        "standart_protection_total": standart_b_total,
                        "standart_protection_caution": standart_b_caution,
                        "max_protection_name": max_b_name,
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
                        "currency": "DZD",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total_brut,
                        "last_total":total_red,
                        "prix": prix_unitaire,
                        "last_prix": prix_unitaire_red,
                        "klm_name": opt_klm_c_name ,
                        "klm_price": opt_klm_c_unit,
                        "klm_total": opt_klm_c_total,
                        "klm_limit":opt_klm_c_limit,
                        "klm_penalite":opt_klm_c_penalite,
                        "carburant_name": opt_carburant_name,
                        "carburant_price": opt_carburant_unit,
                        "carburant_total": opt_carburant_total,
                        "nd_driver_name": opt_nd_driver_name,
                        "nd_driver_price": opt_nd_driver_unit,
                        "nd_driver_total": opt_nd_driver_total,
                        "paiement_name": opt_payment_name,
                        "paiement_price": opt_payment_unit,
                        "paiement_total": opt_payment_total,
                        "sb_5_name": opt_siege_a_name,
                        "sb_5_price": opt_siege_a_unit,
                        "sb_5_total": opt_siege_a_total,
                        "sb_13_name": opt_siege_b_name,
                        "sb_13_price": opt_siege_b_unit,
                        "sb_13_total": opt_siege_b_total,
                        "sb_18_name": opt_siege_c_name,
                        "sb_18_price": opt_siege_c_unit,
                        "sb_18_total": opt_siege_c_total,
                        "base_protection_name": base_c_name,
                        "base_protection_price": base_c_unit,
                        "base_protection_total": base_c_total,
                        "base_protection_caution": base_c_caution,
                        "standart_protection_name": standart_c_name,
                        "standart_protection_price": standart_c_unit,
                        "standart_protection_total": standart_c_total,
                        "standart_protection_caution": standart_c_caution,
                        "max_protection_name": max_c_name,
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
                        'photo_link': vehicle.photo_link,
                        'photo_link_nd': vehicle.photo_link_nd,
                        'age_min': vehicle.age_min,
                        'sticker': vehicle.sticker,
                        'vehicule_type':vehicle.modele.vehicule_type,
                        "date_annulation":date_annulation,
                    })
    else :
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
            parent_client = ListeClient.objects.filter(prime_code=prime_code).first() 
            if parent_client :
                parent_sold = SoldeParrainage.objects.filter(name="Solde Parrainage").first()
                prime_red = parent_sold.parrain_solde

        available_vehicles = get_available_vehicles(date_depart, heure_depart, date_retour, heure_retour, zone_id)

        frais_livraison = FraisLivraison.objects.filter(depart_id=lieu_depart_id, retour_id=lieu_retour_id)
        for frais in frais_livraison:
            total += frais.montant if frais else 0
            
        supplements = Supplement.objects.filter(
            Q(heure_debut__lte=heure_depart, heure_fin__gte=heure_depart) |
            Q(heure_debut__lte=heure_retour, heure_fin__gte=heure_retour)
        )
        for supplement in supplements:
            total += supplement.montant if supplement else 0
            

        frais_dossier = search_option("FRAIS_DOSSIER", total_days)
        total += frais_dossier["total"]
        
        paiement_anticipe = search_option("P_ANTICIPE", total_days)
        opt_payment_name = paiement_anticipe["name"]
        opt_payment_unit = paiement_anticipe["prix"]
        opt_payment_total = paiement_anticipe["total"]

        klm_illimite = search_option("KLM_ILLIMITED", total_days)
        opt_klm_name = klm_illimite["name"]
        opt_klm_unit = klm_illimite["prix"]
        opt_klm_total = klm_illimite["total"]
        opt_klm_limit = klm_illimite["limit"]
        opt_klm_penalite = klm_illimite["penalite"]
        
        klm_illimite_b = search_option("KLM_ILLIMITED_B", total_days)
        opt_klm_b_name = klm_illimite_b["name"]
        opt_klm_b_unit = klm_illimite_b["prix"]
        opt_klm_b_total = klm_illimite_b["total"]
        opt_klm_b_limit = klm_illimite_b["limit"]
        opt_klm_b_penalite = klm_illimite_b["penalite"]

        klm_illimite_c = search_option("KLM_ILLIMITED_C", total_days)
        opt_klm_c_name = klm_illimite_c["name"]
        opt_klm_c_unit = klm_illimite_c["prix"]
        opt_klm_c_total = klm_illimite_c["total"]
        opt_klm_c_limit = klm_illimite_c["limit"]
        opt_klm_c_penalite = klm_illimite_c["penalite"]

        nd_driver = search_option("ND_DRIVER", total_days)
        opt_nd_driver_name = nd_driver["name"]
        opt_nd_driver_unit = nd_driver["prix"]
        opt_nd_driver_total = nd_driver["total"]

        plein_carburant = search_option("P_CARBURANT", total_days)
        opt_carburant_name = plein_carburant["name"]
        opt_carburant_unit = plein_carburant["prix"]
        opt_carburant_total = plein_carburant["total"]

        siege_a = search_option("S_BEBE_5", total_days)
        opt_siege_a_name = siege_a["name"]
        opt_siege_a_unit = siege_a["prix"]
        opt_siege_a_total = siege_a["total"]

        siege_b = search_option("S_BEBE_13", total_days)
        opt_siege_b_name = siege_b["name"]
        opt_siege_b_unit = siege_b["prix"]
        opt_siege_b_total = siege_b["total"]

        siege_c = search_option("S_BEBE_18", total_days)
        opt_siege_c_name = siege_c["name"]
        opt_siege_c_unit = siege_c["prix"]
        opt_siege_c_total = siege_c["total"]
    
        base_a = search_option("BASE_P_1", total_days)
        base_a_name = base_a["name"]
        base_a_unit = base_a["prix"]
        base_a_total = base_a["total"]
        base_a_category = base_a["categorie"]
        base_a_caution = base_a["caution"]

        base_b = search_option("BASE_P_2", total_days)
        base_b_name = base_b["name"]
        base_b_unit = base_b["prix"]
        base_b_total = base_b["total"]
        base_b_category = base_b["categorie"]
        base_b_caution = base_b["caution"]
        
        base_c = search_option("BASE_P_3", total_days)
        base_c_name = base_c["name"]
        base_c_unit = base_c["prix"]
        base_c_total = base_c["total"]
        base_c_category = base_c["categorie"]
        base_c_caution = base_c["caution"]
        
        standart_a = search_option("STANDART_P_1", total_days)
        standart_a_name = standart_a["name"]
        standart_a_unit = standart_a["prix"]
        standart_a_total = standart_a["total"]
        standart_a_caution = standart_a["caution"]

        standart_b = search_option("STANDART_P_2", total_days)
        standart_b_name = standart_b["name"]
        standart_b_unit = standart_b["prix"]
        standart_b_total = standart_b["total"]
        standart_b_caution = standart_b["caution"]
        
        standart_c = search_option("STANDART_P_3", total_days)
        standart_c_name = standart_c["name"]
        standart_c_unit = standart_c["prix"]
        standart_c_total = standart_c["total"]
        standart_c_caution = standart_c["caution"]

        max_a = search_option("MAX_P_1", total_days)
        max_a_name = max_a["name"]
        max_a_unit = max_a["prix"]
        max_a_total = max_a["total"]
        max_a_caution = max_a["caution"]

        max_b = search_option("MAX_P_2", total_days)
        max_b_name = max_b["name"]
        max_b_unit = max_b["prix"]
        max_b_total = max_b["total"]
        max_b_caution = max_b["caution"]
        
        max_c = search_option("MAX_P_3", total_days)
        max_c_name = max_c["name"]
        max_c_unit = max_c["prix"]
        max_c_total = max_c["total"]
        max_c_caution = max_c["caution"]

        modeles_ajoutes = set()
        total_brut = 0

        for vehicle in available_vehicles:
            if vehicle.modele.id in modeles_ajoutes:
                continue

            tarif = Tarifs.objects.filter(
                modele=vehicle.modele,  
                nbr_de__lte=total_days, 
                nbr_au__gte=total_days
            ).filter(
                Q(date_depart_one__lte=date_depart, date_fin_one__gte=date_retour) |
                Q(date_depart_two__lte=date_depart, date_fin_two__gte=date_retour) |
                Q(date_depart_three__lte=date_depart, date_fin_three__gte=date_retour) |
                Q(date_depart_four__lte=date_depart, date_fin_four__gte=date_retour)
            ).first()

            if tarif:
                prix_jour = tarif.prix  
                total_brut = total + (prix_jour * total_days)
            
                for supplement in supplements:

                    start_hour = float(heure_depart[:2]) + float(heure_depart[3:])/60
                    end_hour = float(heure_retour[:2]) + float(heure_retour[3:])/60

                    duration = end_hour - start_hour

                    if duration > supplement.reatrd:
                        total += (prix_jour * supplement.valeur) / 100
                if total_brut > 0 and total_days > 0:
                    prix_unitaire = total_brut / total_days
                
                modeles_ajoutes.add(vehicle.modele.id)
                if int(client_pr) > promotion_value :
                    promotion = "yes"
                    percentage = client_pr
                    total_red = (100 - percentage) * total_brut / 100
                    prix_unitaire_red = total_red / total_days
                elif promotion_value > int(client_pr) and promotions.tout_modele == "oui":
                    promotion = "yes"
                    percentage = promotion_value
                    total_red = (100 - percentage) * total_brut / 100
                    prix_unitaire_red = total_red / total_days
                elif model_one is not None and model_one.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    total_red = (100 - percentage) * total_brut / 100
                    prix_unitaire_red = total_red / total_days
                elif model_two is not None and model_two.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    total_red = (100 - percentage) * total_brut / 100
                    prix_unitaire_red = total_red / total_days
                elif model_three is not None and model_three.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    total_red = (100 - percentage) * total_brut / 100
                    prix_unitaire_red = total_red / total_days
                elif model_four is not None and model_four.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    total_red = (100 - percentage) * total_brut / 100
                    prix_unitaire_red = total_red / total_days
                elif model_five is not None and model_five.id == vehicle.modele.id :
                    promotion = "yes"
                    percentage = promotion_value
                    total_red = (100 - percentage) * total_brut / 100
                    prix_unitaire_red = total_red / total_days
                else :
                    promotion = "no"
                    percentage = 0
                    total_red = total_brut
                    prix_unitaire_red = prix_unitaire

                if client_pr is not None and int(client_sold) > 0: 
                    total_brut = total_brut - client_sold
                
                if client_pr is not None and int(prime_red) > 0:
                    total_brut = total_brut - prime_red

                if vehicle.categorie.id == base_a_category :
                    result.append({
                        "promotion": promotion,
                        "percentage": percentage,
                        "currency": "EUR",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total_brut,
                        "last_total":total_red,
                        "prix": prix_unitaire,
                        "last_prix": prix_unitaire_red,
                        "klm_name": opt_klm_name ,
                        "klm_price": opt_klm_unit,
                        "klm_total": opt_klm_total,
                        "klm_limit":opt_klm_limit,
                        "klm_penalite":opt_klm_penalite,
                        "carburant_name": opt_carburant_name,
                        "carburant_price": opt_carburant_unit,
                        "carburant_total": opt_carburant_total,
                        "nd_driver_name": opt_nd_driver_name,
                        "nd_driver_price": opt_nd_driver_unit,
                        "nd_driver_total": opt_nd_driver_total,
                        "paiement_name": opt_payment_name,
                        "paiement_price": opt_payment_unit,
                        "paiement_total": opt_payment_total,
                        "sb_5_name": opt_siege_a_name,
                        "sb_5_price": opt_siege_a_unit,
                        "sb_5_total": opt_siege_a_total,
                        "sb_13_name": opt_siege_b_name,
                        "sb_13_price": opt_siege_b_unit,
                        "sb_13_total": opt_siege_b_total,
                        "sb_18_name": opt_siege_c_name,
                        "sb_18_price": opt_siege_c_unit,
                        "sb_18_total": opt_siege_c_total,
                        "base_protection_name": base_a_name,
                        "base_protection_price": base_a_unit,
                        "base_protection_total": base_a_total,
                        "base_protection_caution": base_a_caution,
                        "standart_protection_name": standart_a_name,
                        "standart_protection_price": standart_a_unit,
                        "standart_protection_total": standart_a_total,
                        "standart_protection_caution": standart_a_caution,
                        "max_protection_name": max_a_name,
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
                        "currency": "EUR",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total_brut,
                        "last_total":total_red,
                        "prix": prix_unitaire,
                        "last_prix": prix_unitaire_red,
                        "klm_name": opt_klm_b_name ,
                        "klm_price": opt_klm_b_unit,
                        "klm_total": opt_klm_b_total,
                        "klm_limit":opt_klm_b_limit,
                        "klm_penalite":opt_klm_b_penalite,
                        "carburant_name": opt_carburant_name,
                        "carburant_price": opt_carburant_unit,
                        "carburant_total": opt_carburant_total,
                        "nd_driver_name": opt_nd_driver_name,
                        "nd_driver_price": opt_nd_driver_unit,
                        "nd_driver_total": opt_nd_driver_total,
                        "paiement_name": opt_payment_name,
                        "paiement_price": opt_payment_unit,
                        "paiement_total": opt_payment_total,
                        "sb_5_name": opt_siege_a_name,
                        "sb_5_price": opt_siege_a_unit,
                        "sb_5_total": opt_siege_a_total,
                        "sb_13_name": opt_siege_b_name,
                        "sb_13_price": opt_siege_b_unit,
                        "sb_13_total": opt_siege_b_total,
                        "sb_18_name": opt_siege_c_name,
                        "sb_18_price": opt_siege_c_unit,
                        "sb_18_total": opt_siege_c_total,
                        "base_protection_name": base_b_name,
                        "base_protection_price": base_b_unit,
                        "base_protection_total": base_b_total,
                        "base_protection_caution": base_b_caution,
                        "standart_protection_name": standart_b_name,
                        "standart_protection_price": standart_b_unit,
                        "standart_protection_total": standart_b_total,
                        "standart_protection_caution": standart_b_caution,
                        "max_protection_name": max_b_name,
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
                        "currency": "EUR",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total_brut,
                        "last_total":total_red,
                        "prix": prix_unitaire,
                        "last_prix": prix_unitaire_red,
                        "klm_name": opt_klm_c_name ,
                        "klm_price": opt_klm_c_unit,
                        "klm_total": opt_klm_c_total,
                        "klm_limit":opt_klm_c_limit,
                        "klm_penalite":opt_klm_c_penalite,
                        "carburant_name": opt_carburant_name,
                        "carburant_price": opt_carburant_unit,
                        "carburant_total": opt_carburant_total,
                        "nd_driver_name": opt_nd_driver_name,
                        "nd_driver_price": opt_nd_driver_unit,
                        "nd_driver_total": opt_nd_driver_total,
                        "paiement_name": opt_payment_name,
                        "paiement_price": opt_payment_unit,
                        "paiement_total": opt_payment_total,
                        "sb_5_name": opt_siege_a_name,
                        "sb_5_price": opt_siege_a_unit,
                        "sb_5_total": opt_siege_a_total,
                        "sb_13_name": opt_siege_b_name,
                        "sb_13_price": opt_siege_b_unit,
                        "sb_13_total": opt_siege_b_total,
                        "sb_18_name": opt_siege_c_name,
                        "sb_18_price": opt_siege_c_unit,
                        "sb_18_total": opt_siege_c_total,
                        "base_protection_name": base_c_name,
                        "base_protection_price": base_c_unit,
                        "base_protection_total": base_c_total,
                        "base_protection_caution": base_c_caution,
                        "standart_protection_name": standart_c_name,
                        "standart_protection_price": standart_c_unit,
                        "standart_protection_total": standart_c_total,
                        "standart_protection_caution": standart_c_caution,
                        "max_protection_name": max_c_name,
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
                        'photo_link': vehicle.photo_link,
                        'photo_link_nd': vehicle.photo_link_nd,
                        'age_min': vehicle.age_min,
                        'sticker': vehicle.sticker,
                        'vehicule_type':vehicle.modele.vehicule_type,
                        "date_annulation":date_annulation,
                    })

    result.sort(key=lambda x: x["prix"])
    return result 

            

            







    


    

        
 




