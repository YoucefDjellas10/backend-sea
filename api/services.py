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


def add_options_request(ref, nd_driver, carburant, sb_a, sb_b, sb_c):
    try:
        result = []
        reservations = Reservation.objects.filter(name=ref).first()
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


def otp_send(email):
    try:
        client = ListeClient.objects.filter(email=email).first()
        if not client:
            return {"message": "Aucun client trouvé avec cet email.", "client_id": None}

        # Générer un OTP de 6 chiffres
        otp_code = f"{random.randint(100000, 999999)}"
        client.otp = otp_code
        client.otp_created_at = datetime.now()
        client.save()

        # Contenu de l'email
        sujet = "Votre code OTP"
        contenu = f"Bonjour {client.nom} {client.prenom},\n\nVotre code OTP est : {otp_code}. Il est valide pendant 5 minutes."
        expediteur = settings.EMAIL_HOST_USER
        try:
            send_mail(
                sujet,
                contenu,
                expediteur,
                [email],
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
        dossier_option = Options.objects.get(option_code='FRAIS_DOSSIER')
        frais_dossier = dossier_option.prix

    except Options.DoesNotExist:
        frais_dossier = 0


    try:
        klm_option = Options.objects.get(option_code='KLM_ILLIMITED')
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
        carburant_option = Options.objects.get(option_code='P_CARBURANT')
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
        nd_driver_option = Options.objects.get(option_code='ND_DRIVER')
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
        paiement_option = Options.objects.get(option_code='P_ANTICIPE')
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
        sb_5_option = Options.objects.get(option_code='S_BEBE_5')
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
        sb_13_option = Options.objects.get(option_code='S_BEBE_13')
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
        sb_18_option = Options.objects.get(option_code='S_BEBE_18')
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
        base_protection_1_option = Options.objects.get(option_code='BASE_P_1')
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
        base_protection_2_option = Options.objects.get(option_code='BASE_P_2')
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
        base_protection_3_option = Options.objects.get(option_code='BASE_P_3')
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
        standart_protection_1_option = Options.objects.get(option_code='STANDART_P_1')
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
        standart_protection_2_option = Options.objects.get(option_code='STANDART_P_2')
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
        standart_protection_3_option = Options.objects.get(option_code='STANDART_P_3')
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
        max_protection_1_option = Options.objects.get(option_code='MAX_P_1')
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
        max_protection_2_option = Options.objects.get(option_code='MAX_P_2')
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
        max_protection_3_option = Options.objects.get(option_code='MAX_P_3')
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
                lieu_depart = Lieux.objects.get(pk=lieu_depart_id)

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
                lieu_depart = Lieux.objects.get(pk=lieu_depart_id)

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
                lieu_depart = Lieux.objects.get(pk=lieu_depart_id)

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


def search_availability(lieu_depart_id, lieu_retour_id, date_depart, heure_depart, date_retour, heure_retour):

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
        dossier_option = Options.objects.get(option_code='FRAIS_DOSSIER')
        frais_dossier = dossier_option.prix

    except Options.DoesNotExist:
        frais_dossier = 0


    

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

            modele_id = record.modele.id
            lieu_depart = Lieux.objects.get(pk=lieu_depart_id)

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
