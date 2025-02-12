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
        if nd_driver == "yes" and not reservations.opt_nd_driver_name:
            tarif_nd = Options.objects.filter(option_code="ND_DRIVER").first()
            nd_driver_price = tarif_nd.prix
            nd_driver_name = tarif_nd.name
            nd_driver_total = nd_driver_price * reservations.nbr_jour_reservation
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
            result.append({
                "sb_c_name": sb_c_name,
                "sb_c_price": sb_c_price ,
                "sb_c_total": sb_c_total,
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

def ma_reservation_detail(ref, email):
    try:
        ma_reservation=Reservation.objects.filter(name=ref, email=email)
        result =[]
        for record in ma_reservation:
            if ma_reservation :
                result.append({
                    'id':record.id,
                    'reference': record.name,
                    'client_nom': record.nom,
                    'client_perenom': record.prenom,
                    'lieu_depart': record.lieu_depart.id,
                    'lieu_retour': record.lieu_retour.id,
                    'date_depart': record.date_heure_debut,
                    'date_retour': record.date_heure_fin,
                    'mobile': record.numero_lieu,
                    'status': record.status,
                    'opt_payment': record.opt_payment_name,
                    'opt_payment_price': record.opt_payment_price,
                    'opt_payment_total': record.opt_payment_total,
                    'opt_klm': record.opt_klm_name ,
                    'opt_kilometrage': record.opt_kilometrage,
                    'opt_klm_price': record.opt_klm_price,
                    'opt_klm_total': record.opt_klm_total,
                    'opt_protection': record.opt_protection_name,
                    'opt_protection_caution': record.opt_protection_caution,
                    'opt_protection_price': record.opt_protection_price,
                    'opt_protection_total': record.opt_protection_total,
                    'opt_nd_driver': record.opt_nd_driver_name,
                    'opt_nd_driver_price': record.opt_nd_driver_price,
                    'opt_nd_driver_total': record.opt_nd_driver_total,
                    'opt_plein_carburant': record.opt_plein_carburant_name,
                    'opt_plein_carburant_price': record.opt_plein_carburant_prix,
                    'opt_plein_carburant_total': record.opt_plein_carburant_total,
                    'opt_siege_a': record.opt_siege_a_name,
                    'opt_siege_a_price': record.opt_siege_a_prix,
                    'opt_siege_a_total': record.opt_siege_a_total,
                    'opt_siege_b': record.opt_siege_b_name,
                    'opt_siege_b_price': record.opt_siege_b_prix,
                    'opt_siege_b_total': record.opt_siege_b_total,
                    'opt_siege_c': record.opt_siege_c_name,
                    'opt_siege_c_price': record.opt_siege_c_prix,
                    'opt_siege_c_total': record.opt_siege_c_total,
                    'vehicule_id': record.vehicule.id,
                    'modele_name': record.model_name,
                    'marketing_text_fr': record.marketing_text_fr,
                    'photo_link': record.photo_link,
                    'photo_link_nd': record.photo_link_nd,
                    'nombre_deplace': record.nombre_deplace,
                    'nombre_de_porte': record.nombre_de_porte,
                    'nombre_de_bagage': record.nombre_de_bagage,
                    'boite_vitesse': record.boite_vitesse,
                    'carburant': record.carburant,
                    'age_min': record.age_min,
                    'nbr_jour_reservation': record.nbr_jour_reservation,
                    'total_reduit_euro': record.total_reduit_euro,
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
            'client': client,
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

def search_result(lieu_depart_id, lieu_retour_id, date_depart, heure_depart, date_retour, heure_retour):

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
    modele_repete = []

    try:
        dossier_option = Options.objects.filter(option_code='FRAIS_DOSSIER').first()
        frais_dossier = dossier_option.prix

    except Options.DoesNotExist:
        frais_dossier = 0


    try:
        klm_option = Options.objects.filter(option_code='KLM_ILLIMITED').first()
        KLM_ILLIMITED_name = klm_option.name
        KLM_ILLIMITED_prix = klm_option.prix
        KLM_ILLIMITED_limit = klm_option.limit_Klm * total_days
        KLM_ILLIMITED_penalite = klm_option.penalite_Klm
        if klm_option.type_tarif == 'jour':
            KLM_ILLIMITED_total = KLM_ILLIMITED_prix * total_days
        else:
            KLM_ILLIMITED_total = KLM_ILLIMITED_prix
    except Options.DoesNotExist:
        KLM_ILLIMITED_name = None
        KLM_ILLIMITED_prix = 0
        KLM_ILLIMITED_total = 0
        KLM_ILLIMITED_limit = 0
        KLM_ILLIMITED_penalite = 0


    try:
        carburant_option = Options.objects.filter(option_code='P_CARBURANT').first()
        P_CARBURANT_name = carburant_option.name
        P_CARBURANT_prix = carburant_option.prix
        if carburant_option.type_tarif == 'jour':
            P_CARBURANT_total = P_CARBURANT_prix * total_days
        else:
            P_CARBURANT_total = P_CARBURANT_prix
    except Options.DoesNotExist:
        P_CARBURANT_name = None
        P_CARBURANT_prix = 0
        P_CARBURANT_total = 0

    try:
        nd_driver_option = Options.objects.filter(option_code='ND_DRIVER').first()
        ND_DRIVER_name = nd_driver_option.name
        ND_DRIVER_prix = nd_driver_option.prix
        if nd_driver_option.type_tarif == 'jour':
            ND_DRIVER_total = ND_DRIVER_prix * total_days
        else:
            ND_DRIVER_total = ND_DRIVER_prix
    except Options.DoesNotExist:
        ND_DRIVER_name = None
        ND_DRIVER_prix = 0
        ND_DRIVER_total = 0

    try:
        paiement_option = Options.objects.filter(option_code='P_ANTICIPE').first()
        P_ANTICIPE_name = paiement_option.name
        P_ANTICIPE_prix = paiement_option.prix
        if paiement_option.type_tarif == 'jour':
            P_ANTICIPE_total = P_ANTICIPE_prix * total_days
        else:
            P_ANTICIPE_total = P_ANTICIPE_prix
    except Options.DoesNotExist:
        P_ANTICIPE_name = None
        P_ANTICIPE_prix = 0
        P_ANTICIPE_total = 0


    try:
        sb_5_option = Options.objects.filter(option_code='S_BEBE_5').first()
        S_BEBE_5_name = sb_5_option.name
        S_BEBE_5_prix = sb_5_option.prix
        if sb_5_option.type_tarif == 'jour':
            S_BEBE_5_total = S_BEBE_5_prix * total_days
        else:
            S_BEBE_5_total = S_BEBE_5_prix
    except Options.DoesNotExist:
        S_BEBE_5_name = None
        S_BEBE_5_prix = 0
        S_BEBE_5_total = 0


    try:
        sb_13_option = Options.objects.filter(option_code='S_BEBE_13').first()
        S_BEBE_13_name = sb_13_option.name
        S_BEBE_13_prix = sb_13_option.prix
        if sb_13_option.type_tarif == 'jour':
            S_BEBE_13_total = S_BEBE_13_prix * total_days
        else:
            S_BEBE_13_total = S_BEBE_13_prix
    except Options.DoesNotExist:
        S_BEBE_13_name = None
        S_BEBE_13_prix = 0
        S_BEBE_13_total = 0

    try:
        sb_18_option = Options.objects.filter(option_code='S_BEBE_18').first()
        S_BEBE_18_name = sb_18_option.name
        S_BEBE_18_prix = sb_18_option.prix
        if sb_18_option.type_tarif == 'jour':
            S_BEBE_18_total = S_BEBE_18_prix * total_days
        else:
            S_BEBE_18_total = S_BEBE_18_prix
    except Options.DoesNotExist:
        S_BEBE_18_name = None
        S_BEBE_18_prix = 0
        S_BEBE_18_total = 0

    try:
        base_protection_1_option = Options.objects.filter(option_code='BASE_P_1').first()
        BASE_P_1_name = base_protection_1_option.name
        BASE_P_1_prix = base_protection_1_option.prix
        BASE_P_1_caution = base_protection_1_option.caution
        BASE_P_1_categorie = base_protection_1_option.categorie.id
        if base_protection_1_option.type_tarif == 'jour':
            BASE_P_1_total = BASE_P_1_prix * total_days
        else:
            BASE_P_1_total = BASE_P_1_prix
    except Options.DoesNotExist:
        BASE_P_1_name = None
        BASE_P_1_prix = 0
        BASE_P_1_total = 0
        BASE_P_1_caution = 0
        BASE_P_1_categorie = 0

    try:
        base_protection_2_option = Options.objects.filter(option_code='BASE_P_2').first()
        BASE_P_2_name = base_protection_2_option.name
        BASE_P_2_prix = base_protection_2_option.prix
        BASE_P_2_caution = base_protection_2_option.caution
        BASE_P_2_categorie = base_protection_2_option.categorie.id
        if base_protection_2_option.type_tarif == 'jour':
            BASE_P_2_total = BASE_P_2_prix * total_days
        else:
            BASE_P_2_total = BASE_P_2_prix
    except Options.DoesNotExist:
        BASE_P_2_name = None
        BASE_P_2_prix = 0
        BASE_P_2_total = 0
        BASE_P_2_caution = 0
        BASE_P_2_categorie = 0

    try:
        base_protection_3_option = Options.objects.filter(option_code='BASE_P_3').first()
        BASE_P_3_name = base_protection_3_option.name
        BASE_P_3_prix = base_protection_3_option.prix
        BASE_P_3_caution = base_protection_3_option.caution
        BASE_P_3_categorie = base_protection_3_option.categorie.id
        if base_protection_3_option.type_tarif == 'jour':
            BASE_P_3_total = BASE_P_3_prix * total_days
        else:
            BASE_P_3_total = BASE_P_3_prix
    except Options.DoesNotExist:
        BASE_P_3_name = None
        BASE_P_3_prix = 0
        BASE_P_3_total = 0
        BASE_P_3_caution = 0
        BASE_P_3_categorie = 0


    try:
        standart_protection_1_option = Options.objects.filter(option_code='STANDART_P_1').first()
        STANDART_P_1_name = standart_protection_1_option.name
        STANDART_P_1_prix = standart_protection_1_option.prix
        STANDART_P_1_caution = standart_protection_1_option.caution
        STANDART_P_1_categorie = standart_protection_1_option.categorie.id
        if standart_protection_1_option.type_tarif == 'jour':
            STANDART_P_1_total = STANDART_P_1_prix * total_days
        else:
            STANDART_P_1_total = STANDART_P_1_prix
    except Options.DoesNotExist:
        STANDART_P_1_name = None
        STANDART_P_1_prix = 0
        STANDART_P_1_total = 0
        STANDART_P_1_caution = 0
        STANDART_P_1_categorie = 0

    try:
        standart_protection_2_option = Options.objects.filter(option_code='STANDART_P_2').first()
        STANDART_P_2_name = standart_protection_2_option.name
        STANDART_P_2_prix = standart_protection_2_option.prix
        STANDART_P_2_caution = standart_protection_2_option.caution
        STANDART_P_2_categorie = standart_protection_2_option.categorie.id
        if standart_protection_2_option.type_tarif == 'jour':
            STANDART_P_2_total = STANDART_P_2_prix * total_days
        else:
            STANDART_P_2_total = STANDART_P_2_prix
    except Options.DoesNotExist:
        STANDART_P_2_name = None
        STANDART_P_2_prix = 0
        STANDART_P_2_total = 0
        STANDART_P_2_caution = 0
        STANDART_P_2_categorie = 0

    try:
        standart_protection_3_option = Options.objects.filter(option_code='STANDART_P_3').first()
        STANDART_P_3_name = standart_protection_3_option.name
        STANDART_P_3_prix = standart_protection_3_option.prix
        STANDART_P_3_caution = standart_protection_3_option.caution
        STANDART_P_3_categorie = standart_protection_3_option.categorie.id
        if standart_protection_3_option.type_tarif == 'jour':
            STANDART_P_3_total = STANDART_P_3_prix * total_days
        else:
            STANDART_P_3_total = STANDART_P_3_prix
    except Options.DoesNotExist:
        STANDART_P_3_name = None
        STANDART_P_3_prix = 0
        STANDART_P_3_total = 0
        STANDART_P_3_caution = 0
        STANDART_P_3_categorie = 0

    try:
        max_protection_1_option = Options.objects.filter(option_code='MAX_P_1').first()
        MAX_P_1_name = max_protection_1_option.name
        MAX_P_1_prix = max_protection_1_option.prix
        MAX_P_1_caution = max_protection_1_option.caution
        MAX_P_1_categorie = max_protection_1_option.categorie.id
        if max_protection_1_option.type_tarif == 'jour':
            MAX_P_1_total = MAX_P_1_prix * total_days
        else:
            MAX_P_1_total = MAX_P_1_prix
    except Options.DoesNotExist:
        MAX_P_1_name = None
        MAX_P_1_prix = 0
        MAX_P_1_total = 0
        MAX_P_1_caution = 0
        MAX_P_1_categorie = 0

    try:
        max_protection_2_option = Options.objects.filter(option_code='MAX_P_2').first()
        MAX_P_2_name = max_protection_2_option.name
        MAX_P_2_prix = max_protection_2_option.prix
        MAX_P_2_caution = max_protection_2_option.caution
        MAX_P_2_categorie = max_protection_2_option.categorie.id
        if max_protection_2_option.type_tarif == 'jour':
            MAX_P_2_total = MAX_P_2_prix * total_days
        else:
            MAX_P_2_total = MAX_P_2_prix
    except Options.DoesNotExist:
        MAX_P_2_name = None
        MAX_P_2_prix = 0
        MAX_P_2_total = 0
        MAX_P_2_caution = 0
        MAX_P_2_categorie = 0


    try:
        max_protection_3_option = Options.objects.filter(option_code='MAX_P_3').first()
        MAX_P_3_name = max_protection_3_option.name
        MAX_P_3_prix = max_protection_3_option.prix
        MAX_P_3_caution = max_protection_3_option.caution
        MAX_P_3_categorie = max_protection_3_option.categorie.id
        if max_protection_3_option.type_tarif == 'jour':
            MAX_P_3_total = MAX_P_3_prix * total_days
        else:
            MAX_P_3_total = MAX_P_3_prix
    except Options.DoesNotExist:
        MAX_P_3_name = None
        MAX_P_3_prix = 0
        MAX_P_3_total = 0
        MAX_P_3_caution = 0
        MAX_P_3_categorie = 0

    for record in tarifs:
        total = 0
        prix_unitaire = 0
        total += frais_dossier

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
            if record.categorie.id == MAX_P_1_categorie :

                modele_id = record.modele.id
                lieu_depart = Lieux.objects.filter(pk=lieu_depart_id).first()

                date_depart_heure_ = datetime.strptime(f"{date_depart} {heure_depart}", '%Y-%m-%d %H:%M')
                date_retour_heure_ = datetime.strptime(f"{date_retour} {heure_retour}", '%Y-%m-%d %H:%M')

                zone_lieu_depart = lieu_depart.zone

                vehicules_disponibles = Vehicule.objects.filter(
                    Q(zone=zone_lieu_depart) &
                    ~Q(reservation__date_heure_debut__lt=date_retour_heure_, reservation__date_heure_fin__gt=date_depart_heure_)  # Non réservé dans l'intervalle
                ).distinct()


                for record in vehicules_disponibles:
                    if record.modele.id == modele_id and record.modele.id not in modele_repete:
                        modele_repete.append(record.modele.id)
                        resultats.append({
                            "modele_id": record.modele.id,
                            "categorie":record.categorie.id,
                            "total": total,
                            "prix": prix_par_jour,
                            "klm_name": KLM_ILLIMITED_name,
                            "klm_price": KLM_ILLIMITED_prix,
                            "klm_total": KLM_ILLIMITED_total,
                            "klm_limit":KLM_ILLIMITED_limit,
                            "klm_penalite":KLM_ILLIMITED_penalite,
                            "carburant_name": P_CARBURANT_name,
                            "carburant_price": P_CARBURANT_prix,
                            "carburant_total": P_CARBURANT_total,
                            "nd_driver_name": ND_DRIVER_name,
                            "nd_driver_price": ND_DRIVER_prix,
                            "nd_driver_total": ND_DRIVER_total,
                            "paiement_name": P_ANTICIPE_name,
                            "paiement_price": P_ANTICIPE_prix,
                            "paiement_total": P_ANTICIPE_total,
                            "sb_5_name": S_BEBE_5_name,
                            "sb_5_price": S_BEBE_5_prix,
                            "sb_5_total": S_BEBE_5_total,
                            "sb_13_name": S_BEBE_13_name,
                            "sb_13_price": S_BEBE_13_prix,
                            "sb_13_total": S_BEBE_13_total,
                            "sb_18_name": S_BEBE_18_name,
                            "sb_18_price": S_BEBE_18_prix,
                            "sb_18_total": S_BEBE_18_total,
                            "base_protection_name": BASE_P_1_name,
                            "base_protection_price": BASE_P_1_prix,
                            "base_protection_total": BASE_P_1_total,
                            "base_protection_caution": BASE_P_1_caution,
                            "standart_protection_name": STANDART_P_1_name,
                            "standart_protection_price": STANDART_P_1_prix,
                            "standart_protection_total": STANDART_P_1_total,
                            "standart_protection_caution": STANDART_P_1_caution,
                            "max_protection_name": MAX_P_1_name,
                            "max_protection_price": MAX_P_1_prix,
                            "max_protection_total": MAX_P_1_total,
                            "max_protection_caution": MAX_P_1_caution,
                            'id': record.id,
                            'model_name': record.model_name,
                            'nombre_deplace': record.nombre_deplace,
                            'nombre_de_bagage': record.nombre_de_bagage,
                            'nombre_de_porte': record.nombre_de_porte,
                            'boite_vitesse': record.boite_vitesse,
                            'carburant': record.carburant,
                            'marketing_text_fr': record.marketing_text_fr,
                            'photo_link': record.photo_link,
                            'photo_link_nd': record.photo_link_nd,
                            'age_min': record.age_min,
                            'sticker': record.sticker,
                        })
            elif record.categorie.id == MAX_P_2_categorie :

                modele_id = record.modele.id
                lieu_depart = Lieux.objects.filter(pk=lieu_depart_id).first()

                date_depart__heure = datetime.strptime(f"{date_depart} {heure_depart}", '%Y-%m-%d %H:%M')
                date_retour__heure = datetime.strptime(f"{date_retour} {heure_retour}", '%Y-%m-%d %H:%M')

                zone_lieu_depart = lieu_depart.zone

                vehicules_disponibles = Vehicule.objects.filter(
                    Q(zone=zone_lieu_depart) &
                    ~Q(reservation__date_heure_debut__lt=date_retour__heure, reservation__date_heure_fin__gt=date_depart__heure)  # Non réservé dans l'intervalle
                ).distinct()

                for record in vehicules_disponibles:
                    if record.modele.id == modele_id and record.modele.id not in modele_repete:
                        modele_repete.append(record.modele.id)
                        resultats.append({
                            "modele_id": record.modele.id,
                            "categorie":record.categorie.id,
                            "total": total,
                            "prix": prix_par_jour,
                            "klm_name": KLM_ILLIMITED_name,
                            "klm_price": KLM_ILLIMITED_prix,
                            "klm_total": KLM_ILLIMITED_total,
                            "klm_limit":KLM_ILLIMITED_limit,
                            "klm_penalite":KLM_ILLIMITED_penalite,
                            "carburant_name": P_CARBURANT_name,
                            "carburant_price": P_CARBURANT_prix,
                            "carburant_total": P_CARBURANT_total,
                            "nd_driver_name": ND_DRIVER_name,
                            "nd_driver_price": ND_DRIVER_prix,
                            "nd_driver_total": ND_DRIVER_total,
                            "paiement_name": P_ANTICIPE_name,
                            "paiement_price": P_ANTICIPE_prix,
                            "paiement_total": P_ANTICIPE_total,
                            "sb_5_name": S_BEBE_5_name,
                            "sb_5_price": S_BEBE_5_prix,
                            "sb_5_total": S_BEBE_5_total,
                            "sb_13_name": S_BEBE_13_name,
                            "sb_13_price": S_BEBE_13_prix,
                            "sb_13_total": S_BEBE_13_total,
                            "sb_18_name": S_BEBE_18_name,
                            "sb_18_price": S_BEBE_18_prix,
                            "sb_18_total": S_BEBE_18_total,
                            "base_protection_name": BASE_P_2_name,
                            "base_protection_price": BASE_P_2_prix,
                            "base_protection_total": BASE_P_2_total,
                            "base_protection_caution": BASE_P_2_caution,
                            "standart_protection_name": STANDART_P_2_name,
                            "standart_protection_price": STANDART_P_2_prix,
                            "standart_protection_total": STANDART_P_2_total,
                            "standart_protection_caution": STANDART_P_2_caution,
                            "max_protection_name": MAX_P_2_name,
                            "max_protection_price": MAX_P_2_prix,
                            "max_protection_total": MAX_P_2_total,
                            "max_protection_caution": MAX_P_2_caution,
                            'id': record.id,
                            'model_name': record.model_name,
                            'nombre_deplace': record.nombre_deplace,
                            'nombre_de_bagage': record.nombre_de_bagage,
                            'nombre_de_porte': record.nombre_de_porte,
                            'boite_vitesse': record.boite_vitesse,
                            'carburant': record.carburant,
                            'marketing_text_fr': record.marketing_text_fr,
                            'photo_link': record.photo_link,
                            'photo_link_nd': record.photo_link_nd,
                            'age_min': record.age_min,
                            'sticker': record.sticker,
                        })
            elif record.categorie.id == MAX_P_3_categorie :

                modele_id = record.modele.id
                lieu_depart = Lieux.objects.filter(pk=lieu_depart_id).first()

                date_depart_heure = datetime.strptime(f"{date_depart} {heure_depart}", '%Y-%m-%d %H:%M')
                date_retour_heure = datetime.strptime(f"{date_retour} {heure_retour}", '%Y-%m-%d %H:%M')

                zone_lieu_depart = lieu_depart.zone

                vehicules_disponibles = Vehicule.objects.filter(
                    Q(zone=zone_lieu_depart) &
                    ~Q(reservation__date_heure_debut__lt=date_retour_heure, reservation__date_heure_fin__gt=date_depart_heure)  # Non réservé dans l'intervalle
                ).distinct()

                for record in vehicules_disponibles:
                    if record.modele.id == modele_id and record.modele.id not in modele_repete:
                        modele_repete.append(record.modele.id)
                        resultats.append({
                            "modele_id": record.modele.id,
                            "categorie":record.categorie.id,
                            "total": total,
                            "prix": prix_par_jour,
                            "klm_name": KLM_ILLIMITED_name,
                            "klm_price": KLM_ILLIMITED_prix,
                            "klm_total": KLM_ILLIMITED_total,
                            "klm_limit":KLM_ILLIMITED_limit,
                            "klm_penalite":KLM_ILLIMITED_penalite,
                            "carburant_name": P_CARBURANT_name,
                            "carburant_price": P_CARBURANT_prix,
                            "carburant_total": P_CARBURANT_total,
                            "nd_driver_name": ND_DRIVER_name,
                            "nd_driver_price": ND_DRIVER_prix,
                            "nd_driver_total": ND_DRIVER_total,
                            "paiement_name": P_ANTICIPE_name,
                            "paiement_price": P_ANTICIPE_prix,
                            "paiement_total": P_ANTICIPE_total,
                            "sb_5_name": S_BEBE_5_name,
                            "sb_5_price": S_BEBE_5_prix,
                            "sb_5_total": S_BEBE_5_total,
                            "sb_13_name": S_BEBE_13_name,
                            "sb_13_price": S_BEBE_13_prix,
                            "sb_13_total": S_BEBE_13_total,
                            "sb_18_name": S_BEBE_18_name,
                            "sb_18_price": S_BEBE_18_prix,
                            "sb_18_total": S_BEBE_18_total,
                            "base_protection_name": BASE_P_3_name,
                            "base_protection_price": BASE_P_3_prix,
                            "base_protection_total": BASE_P_3_total,
                            "base_protection_caution": BASE_P_3_caution,
                            "standart_protection_name": STANDART_P_3_name,
                            "standart_protection_price": STANDART_P_3_prix,
                            "standart_protection_total": STANDART_P_3_total,
                            "standart_protection_caution": STANDART_P_3_caution,
                            "max_protection_name": MAX_P_3_name,
                            "max_protection_price": MAX_P_3_prix,
                            "max_protection_total": MAX_P_3_total,
                            "max_protection_caution": MAX_P_3_caution,
                            'id': record.id,
                            'model_name': record.model_name,
                            'nombre_deplace': record.nombre_deplace,
                            'nombre_de_bagage': record.nombre_de_bagage,
                            'nombre_de_porte': record.nombre_de_porte,
                            'boite_vitesse': record.boite_vitesse,
                            'carburant': record.carburant,
                            'marketing_text_fr': record.marketing_text_fr,
                            'photo_link': record.photo_link,
                            'photo_link_nd': record.photo_link_nd,
                            'age_min': record.age_min,
                            'sticker': record.sticker,
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
            'total': prix * float(total_days) * montant_taux if option.type_tarif == 'jour' else prix,
            'categorie': option.categorie.id if option.categorie else None,
            'limit': limit_Klm * total_days,
            'penalite': penalite_Klm * montant_taux,
            'caution': caution * montant_taux
        }
    
    except Options.DoesNotExist:
        return {'name': None, 'prix': 0, 'total': 0, 'limit': 0, 'penalite': 0, 'caution': 0, 'categorie': 0} 
    
def disponibilite_resultat(lieu_depart_id, lieu_retour_id, date_depart, heure_depart, date_retour, heure_retour, client_id, prime_code, country_code):
    try:
        date_depart = datetime.strptime(date_depart, "%Y-%m-%d").date()
        date_retour = datetime.strptime(date_retour, "%Y-%m-%d").date()
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
    free_options = []
    client_pr = 0 
    client_sold = 0
    total = 0
    total_red = 0
    prix_unitaire = 0
    prix_unitaire_red = 0
    prix_jour = 0
    promotion_models = []
    promotion_zone = []

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
                client_categori_id = client.categorie_client.id
                category_client = CategorieClient.objects.filter(id=client_categori_id).first()
                option_one = category_client.option_one
                option_two = category_client.option_two
                option_three = category_client.option_three
                option_four = category_client.option_four
                option_five = category_client.option_five
                option_six = category_client.option_six
                option_seven = category_client.option_seven
                option_eight = category_client.option_eight
                option_nine = category_client.option_nine
                option_ten = category_client.option_ten

                free_options.append({
                    "option_one": option_one if option_one else None,
                    "option_two": option_two if option_two else None,
                    "option_three": option_three if option_three else None,
                    "option_four": option_four if option_four else None,
                    "option_five": option_five if option_five else None,
                    "option_six": option_six if option_six else None,
                    "option_seven": option_seven if option_seven else None,
                    "option_eight": option_eight if option_eight else None,
                    "option_nine": option_nine if option_nine else None,
                    "option_ten": option_ten if option_ten else None
                })

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
        total += frais_dossier["total"]

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
                total += (prix_jour * total_days)
                for supplement in supplements:

                    start_hour = float(heure_depart[:2]) + float(heure_depart[3:])/60
                    end_hour = float(heure_retour[:2]) + float(heure_retour[3:])/60

                    duration = end_hour - start_hour

                    if duration > supplement.reatrd:
                        total += (prix_jour * supplement.valeur) / 100
                if total > 0 and total_days > 0:
                    prix_unitaire = total / total_days
                
                modeles_ajoutes.add(vehicle.modele.id)
                if int(client_pr) > 0 :
                    promotion = "yes"
                    percentage = client_pr
                    total_red = (100 - percentage) * total / 100
                    prix_unitaire_red = total_red / total_days
                else :
                    promotion = "no"
                    percentage = 0
                    total_red = total
                    prix_unitaire_red = prix_unitaire 

                if int(client_sold) > 0 : 
                    total = total - client_sold
                
                if int(prime_red) > 0 :
                    total = total - prime_red

                if vehicle.categorie.id == base_a_category :
                    result.append({
                        "promotion": promotion,
                        "percentage": percentage,
                        "currency": "DZD",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total,
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
                    })

                
                if vehicle.categorie.id == base_b_category :
                    result.append({
                        "promotion": promotion,
                        "percentage": percentage,
                        "currency": "EUR",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total,
                        "prix": prix_unitaire,
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
                    })

                if vehicle.categorie.id == base_c_category :
                    result.append({
                        "promotion": promotion,
                        "percentage": percentage,
                        "currency": "EUR",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total,
                        "prix": prix_unitaire,
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
                client_categori_id = client.categorie_client.id
                category_client = CategorieClient.objects.filter(id=client_categori_id).first()
                option_one = category_client.option_one
                option_two = category_client.option_two
                option_three = category_client.option_three
                option_four = category_client.option_four
                option_five = category_client.option_five
                option_six = category_client.option_six
                option_seven = category_client.option_seven
                option_eight = category_client.option_eight
                option_nine = category_client.option_nine
                option_ten = category_client.option_ten

                free_options.append({
                    "option_one": option_one if option_one else None,
                    "option_two": option_two if option_two else None,
                    "option_three": option_three if option_three else None,
                    "option_four": option_four if option_four else None,
                    "option_five": option_five if option_five else None,
                    "option_six": option_six if option_six else None,
                    "option_seven": option_seven if option_seven else None,
                    "option_eight": option_eight if option_eight else None,
                    "option_nine": option_nine if option_nine else None,
                    "option_ten": option_ten if option_ten else None
                })

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
                total += (prix_jour * total_days)
                for supplement in supplements:

                    start_hour = float(heure_depart[:2]) + float(heure_depart[3:])/60
                    end_hour = float(heure_retour[:2]) + float(heure_retour[3:])/60

                    duration = end_hour - start_hour

                    if duration > supplement.reatrd:
                        total += (prix_jour * supplement.valeur) / 100
                if total > 0 and total_days > 0:
                    prix_unitaire = total / total_days
                
                modeles_ajoutes.add(vehicle.modele.id)
                if client_pr is not None and int(client_pr) > 0 :
                    promotion = "yes"
                    percentage = client_pr
                    total_red = (100 - percentage) * total / 100
                    prix_unitaire_red = total_red / total_days
                else :
                    promotion = "no"
                    percentage = 0
                    total_red = total
                    prix_unitaire_red = prix_unitaire 

                if client_pr is not None and int(client_sold) > 0: 
                    total = total - client_sold
                
                if client_pr is not None and int(prime_red) > 0:
                    total = total - prime_red

                if vehicle.categorie.id == base_a_category :
                    result.append({
                        "promotion": promotion,
                        "percentage": percentage,
                        "currency": "EUR",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total,
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
                    })

                
                if vehicle.categorie.id == base_b_category :
                    result.append({
                        "promotion": promotion,
                        "percentage": percentage,
                        "currency": "EUR",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total,
                        "prix": prix_unitaire,
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
                    })

                if vehicle.categorie.id == base_c_category :
                    result.append({
                        "promotion": promotion,
                        "percentage": percentage,
                        "currency": "EUR",
                        "modele_id": vehicle.modele.id,
                        "categorie":vehicle.categorie.id,
                        "total": total,
                        "prix": prix_unitaire,
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
                    })

    return free_options,result 
            

            







    


    

        
 




