from django.shortcuts import render
from django.http import HttpResponse, Http404
from .models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from .services import *
from django.http import JsonResponse
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.decorators.http import require_http_methods
from django.utils.dateparse import parse_datetime
from django.test import RequestFactory
import json
from decimal import Decimal
from rest_framework.decorators import api_view
from rest_framework import status
stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
from django.utils import timezone
import time
import locale
from django.forms.models import model_to_dict
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework import status
import base64, mimetypes, os
from django.shortcuts import get_object_or_404
import logging
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from utils.client_info import ClientInfoExtractor


logger = logging.getLogger(__name__)

def relance_mail_view(request):
    try:
        reservation_id = request.GET.get("reservation_id")

        reservation = Reservation.objects.get(id=reservation_id)
        sujet = f"Besoin d'aide pour finaliser votre réservation ?"
        expediteur = settings.EMAIL_HOST_USER
        html_message = render_to_string('email/mail_relance_email.html', {
            'client_code':reservation.client.code_prime,
            'client_name':reservation.client.name,
        })
        send_mail(
            sujet,
            strip_tags(html_message),  
            expediteur,
            [reservation.email],
            html_message=html_message,
            fail_silently=False,
        )
        return JsonResponse({"message": "mail de relance envoyé."}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@csrf_exempt
@require_http_methods(["POST"])
def creer_reservation(request):
    try:
        data = json.loads(request.body)
        ref = data.get("ref")
        lieu_depart = data.get("lieu_depart")
        lieu_retour = data.get("lieu_retour")
        date_depart = data.get("date_depart")
        date_retour = data.get("date_retour")
        modele = data.get("modele")
        opt_nd_driver = data.get("opt_nd_driver")
        opt_nd_driver_prix = data.get("opt_nd_driver_prix")
        opt_carburant = data.get("opt_carburant")
        opt_carburant_prix = data.get("opt_carburant_prix")
        opt_sb_a = data.get("opt_sb_a")
        opt_sb_a_prix = data.get("opt_sb_a_prix")
        nom = data.get("nom")
        prenom = data.get("prenom")
        nd_nom = data.get("nd_nom")
        nd_prenom = data.get("nd_prenom")
        nd_date_permis = data.get("nd_date_permis")
        num_vol = data.get("num_vol")
        note_depart = data.get("note_depart")
        note_retour = data.get("note_retour")
        status = data.get("status")
        total = data.get("total")
        date_reservation = data.get("date_reservation")
        confirmation_date = data.get("confirmation_date")
        cancel_date = data.get("cancel_date")
        date_valid_depart = data.get("date_valid_depart")
        date_valid_retour = data.get("date_valid_retour")
        km_depart = data.get("km_depart")
        km_retour = data.get("km_retour")
        dep_note = data.get("dep_note")
        ret_note = data.get("ret_note")
        caution = data.get("caution")

        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str, "%d/%m/%Y %H:%M")
            except:
                return None
            
        def parse_only_date(date_str):
            if not date_str:
                return None
            try:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
                return dt.strftime("%Y-%m-%d")
            except Exception as e:
                print("Erreur parse_only_date:", e)
                return None

        lieu_depart_obj = Lieux.objects.filter(id=lieu_depart).first()
        if lieu_depart and lieu_retour:
            depart = Lieux.objects.filter(id=lieu_depart).first()
            retour = Lieux.objects.filter(id=lieu_retour).first()
            zone = Zone.objects.filter(id=depart.zone.id).first()
            depart_retour_string = f"{depart.name} → {retour.name}"
            if depart.zone != retour.zone:
                return JsonResponse({"error": "zone invalides."}, status=400) 
            
        fmt = "%d/%m/%Y %H:%M"

        dt_depart = datetime.strptime(date_depart, fmt)
        dt_retour = datetime.strptime(date_retour, fmt)
        date_depart_date = dt_depart.strftime("%d/%m/%Y")
        heure_depart = dt_depart.strftime("%H:%M")
        date_retour_date = dt_retour.strftime("%d/%m/%Y")
        heure_retour = dt_retour.strftime("%H:%M")
        du_au = f"{date_depart_date} {heure_depart} → {date_retour_date} {heure_retour}"
        nb_jr = (dt_retour.date() - dt_depart.date()).days
        duree = f"{nb_jr} jours"

        status_str = str(status) if status is not None else None
        status_char = None

        # Parser les autres dates
        dt_date_reservation = parse_date(date_reservation)
        dt_confirmation_date = parse_date(confirmation_date)
        dt_cancel_date = parse_date(cancel_date)
        dt_date_valid_depart = parse_date(date_valid_depart)
        dt_date_valid_retour = parse_date(date_valid_retour)
        dt_nd_date_permis = parse_only_date(nd_date_permis)

        nom = re.sub(r'\s+', ' ', nom.strip()).upper()
        prenom = re.sub(r'\s+', ' ', prenom.strip()).upper()
        client = None
        client=ListeClient.objects.filter(nom=nom, prenom=prenom).first()
        if not client:
            client=ListeClient.objects.filter(nom=prenom, prenom=nom).first()
            if not client: 
                return JsonResponse({"error": "pas de client"}, status=400)
        
        nd_client = None            
        if nd_nom and nd_prenom :
            nd_nom = re.sub(r'\s+', ' ', nd_nom.strip()).upper()
            nd_prenom = re.sub(r'\s+', ' ', nd_prenom.strip()).upper()
            nd_client=ListeClient.objects.filter(nom=nd_nom, prenom=nd_prenom).first()
            if not nd_client:
                nd_client=ListeClient.objects.filter(nom=nd_prenom, prenom=nd_nom).first()
                if not nd_client: 
                    nd_client = ListeClient.objects.create(
                        nom = nd_nom,
                        prenom = nd_prenom,
                    )
                    if not nd_client:
                        return JsonResponse({"error": "pas de nd client"}, status=400)
                
        searched_model = Modele.objects.filter(name=modele).first()

        model_name = None
        vehicule = None
        klm_a_illimite = None
        protection = None

        if not searched_model : 
            model_name = modele
            klm_a_illimite = Options.objects.filter(option_code__icontains="KLM_ILLIMITED", zone= lieu_depart_obj.zone).first()
                
            protection = Options.objects.filter(option_code__icontains="STANDART", zone= lieu_depart_obj.zone).first()

        else : 
            vehicules = Vehicule.objects.filter(modele=searched_model,zone=zone)
            for vehicule_ in vehicules:
                if status_str == "1":
                    nouvelle_depart = dt_depart  
                    nouvelle_retour = dt_retour  
                    
                    reservations_confirmees = Reservation.objects.filter(
                        vehicule=vehicule_,
                        status="confirmee"
                    )
                    
                    vehicule_dispo = True
                    for res in reservations_confirmees:
                        res_depart_str = f"{res.date_depart_char} {res.heure_depart_char}"
                        res_retour_str = f"{res.date_retour_char} {res.heure_retour_char}"
                        
                        res_depart = datetime.strptime(res_depart_str, "%d/%m/%Y %H:%M")
                        res_retour = datetime.strptime(res_retour_str, "%d/%m/%Y %H:%M")
                        
                        if res_depart < nouvelle_retour and res_retour > nouvelle_depart:
                            vehicule_dispo = False
                            break
                    
                    if vehicule_dispo:
                        vehicule = vehicule_
                        break
                else: 
                    vehicule = vehicule_
                    break
            if not vehicule and vehicules.exists():
                vehicule = vehicules.first()

            if not vehicule:
                return JsonResponse({"error": "Aucun véhicule disponible"}, status=400)
      
            klm_a_illimite = Options.objects.filter(option_code__icontains="KLM_ILLIMITED",categorie=searched_model.categorie, zone= lieu_depart_obj.zone).first()
                
            protection = Options.objects.filter(option_code__icontains="STANDART",categorie=searched_model.categorie, zone= lieu_depart_obj.zone).first()

        carburant = None
        sb_a = None
        nd_driver_opt = None
        if opt_carburant == "yes":
            carburant = Options.objects.filter(option_code="P_CARBURANT", zone= lieu_depart_obj.zone).first()

        
        if opt_sb_a == "yes":
            sb_a = Options.objects.filter(option_code="S_BEBE_5", zone= lieu_depart_obj.zone).first()

        
        if opt_nd_driver == "yes":
            nd_driver_opt = Options.objects.filter(option_code="ND_DRIVER", zone= lieu_depart_obj.zone).first()

        if status_str  == "1":
             status_char = "confirmee"
        elif status_str  == "2":
            status_char = "rejete"
        elif status_str  == "3":
            status_char = "annule"

        etat_reser = "reserve"

        
        now = datetime.now()
        if now > dt_depart :
            etat_reser = "loue"

        reservation = Reservation.objects.create(
            note_lv_d=note_depart,
            note_lv_r=note_retour,
            create_date=dt_date_reservation,
            status=status_char,
            etat_reservation=etat_reser,
            date_heure_debut = dt_depart,
            date_heure_fin = dt_retour,
            date_depart_char = date_depart_date,
            date_retour_char = date_retour_date,
            heure_depart_char = heure_depart,
            heure_retour_char = heure_retour,
            du_au = du_au,
            nbr_jour_reservation = nb_jr,
            duree_dereservation = duree,
            lieu_depart = depart,
            zone = depart.zone,
            address_fr = depart.address,
            address_en = depart.address_en,
            address_ar = depart.address_ar,
            lieu_retour = retour,
            depart_retour = depart_retour_string,
            vehicule = vehicule if vehicule else None,
            modele = vehicule.modele if vehicule else None,
            categorie = vehicule.categorie if vehicule else None,
            carburant = vehicule.carburant if vehicule else None,
            matricule = vehicule.matricule if vehicule else None,
            numero = vehicule.numero if vehicule else None,
            model_name = vehicule.model_name if vehicule else model_name,
            marketing_text_fr = vehicule.marketing_text_fr if vehicule else None,
            photo_link_nd = vehicule.photo_link_nd if vehicule else None,
            photo_link = vehicule.photo_link if vehicule else None,
            nombre_deplace = vehicule.nombre_deplace if vehicule else None,
            nombre_de_porte = vehicule.nombre_de_porte if vehicule else None,
            nombre_de_bagage = vehicule.nombre_de_bagage if vehicule else None,
            boite_vitesse = vehicule.boite_vitesse if vehicule else None,
            age_min = vehicule.age_min if vehicule else None,
            client = client,
            client_create_date = client.create_date if client.create_date is not None else None,
            nom = client.nom,
            prenom = client.prenom,
            email = client.email,
            date_de_naissance = client.date_de_naissance,
            mobile = client.mobile,
            telephone = client.telephone,
            risque = client.risque,
            note = client.note,
            categorie_client = client.categorie_client,
            code_prime = client.code_prime,
            solde = client.solde,
            nom_nd_condicteur = nd_nom if nd_nom else None,
            prenom_nd_condicteur = nd_prenom if nd_prenom else None,
            date_de_permis=dt_nd_date_permis,
            opt_klm = klm_a_illimite if klm_a_illimite else None,
            opt_klm_name = klm_a_illimite.name if klm_a_illimite else None,
            opt_klm_total = 0,
            opt_protection = protection if protection else None,
            opt_protection_name = protection.name if protection else None,
            opt_protection_caution= caution,
            opt_protection_price=0,
            opt_protection_total=0,
            opt_nd_driver=nd_driver_opt if nd_driver_opt else None,
            opt_nd_driver_name=nd_driver_opt.name if nd_driver_opt else None,
            opt_nd_driver_total=opt_nd_driver_prix if opt_nd_driver_prix else 0,
            opt_plein_carburant=carburant if carburant else None,
            opt_plein_carburant_name=carburant.name if carburant else None,
            opt_plein_carburant_prix= opt_carburant_prix if carburant else 0,
            opt_plein_carburant_total=opt_carburant_prix if carburant else 0,
            opt_siege_a = sb_a if sb_a else None,
            opt_siege_a_name=sb_a.name if sb_a else None,
            opt_siege_a_prix=opt_sb_a_prix if sb_a else None,
            opt_siege_a_total=opt_sb_a_prix if sb_a else None,
            num_vol=num_vol,
            total_reduit = total,
            total_reduit_euro = total,       
            confirmation_date=dt_confirmation_date,
            cancelation_date=dt_cancel_date,
            reste_payer = total,
            total_revenue = 0,
            montant_paye = 0,
            nd_client = nd_client if nd_client else None
        )  
        reservation.save()

        reservation.name = ref
        reservation.save()

        taux = TauxChange.objects.get(id=2)
        taux_change = taux.montant

        if now > dt_depart:

            payment = Payment.objects.create(
                reservation=reservation,
                vehicule=reservation.vehicule,  
                modele=reservation.modele,  
                zone=reservation.lieu_depart.zone,  
                total_reduit_euro=total,
                montant=total,
                montant_dzd=0,
                montant_eur_dzd=float(total) * float(taux_change),
                montant_dzd_eur=0,  
                note="Paiement effectué via Stripe",  
                total_reduit_dinar=float(total) * float(taux_change),
                ecart_eur=0,
                ecart_da=0,
                mode_paiement="carte", 
                total_encaisse=total,  
            )
            payment.save()
            reservation.reste_payer = 0
            reservation.montant_paye = total
            reservation.total_revenue = total
            reservation.save()
        
        else:
            payment = Payment.objects.create(
                create_date=datetime.now(),
                reservation=reservation,
                vehicule=reservation.vehicule,  
                modele=reservation.modele,  
                zone=reservation.lieu_depart.zone,  
                total_reduit_euro=total,
                montant=5,
                montant_dzd=0,
                montant_eur_dzd=float(5) * float(taux_change),
                montant_dzd_eur=0,  
                note="Paiement effectué via Stripe",  
                total_reduit_dinar=float(total) * float(taux_change),
                ecart_eur=0,
                ecart_da=0,
                mode_paiement="carte", 
                total_encaisse=5,  
            )
            payment.save()
            reservation.reste_payer = float(total) - float(5)
            reservation.montant_paye = 5
            reservation.total_revenue = 5
            reservation.save()


        if reservation.status == "confirmee":

            livraison = Livraison.objects.create(
                date_de_livraison = dt_date_valid_depart,
                kilomtrage = km_depart,
                lv_note = dep_note,
                reservation = reservation,
                name = reservation.name,
                opt_protection_caution = reservation.opt_protection.caution,
                opt_protection = reservation.opt_protection.name,
                opt_carburant = reservation.opt_plein_carburant,
                opt_carburant_check = True if reservation.opt_plein_carburant else False,
                opt_klm = reservation.opt_klm,
                opt_klm_check = True if reservation.opt_klm else False,
                opt_nd_driver = reservation.opt_nd_driver ,
                opt_nd_driver_check = True if reservation.opt_nd_driver else False,
                opt_sb_a = reservation.opt_siege_a,
                opt_sb_a_check = True if reservation.opt_siege_a else False,
                opt_sb_b = reservation.opt_siege_b,
                opt_sb_b_check = True if reservation.opt_siege_b else False,
                opt_sb_c = reservation.opt_siege_c,
                opt_sb_c_check = True if reservation.opt_siege_c else False,
                status = reservation.status,
                date_heure_debut = reservation.date_heure_debut,
                date_heure_fin = reservation.date_heure_fin,
                date_de_reservation = reservation.create_date,
                nbr_jour_reservation = reservation.nbr_jour_reservation,
                duree_dereservation = reservation.duree_dereservation,
                lieu_depart = reservation.lieu_depart,
                zone = reservation.zone,
                lieu_retour = reservation.lieu_retour,
                vehicule = reservation.vehicule,
                modele = reservation.modele,
                carburant = reservation.carburant,
                client = reservation.client,
                nom = reservation.nom,
                prenom = reservation.prenom,
                email = reservation.email,
                mobile = reservation.mobile,
                total_reduit_euro = reservation.reste_payer,
                total_payer = reservation.reste_payer,
                stage = 'reserve',
                lv_type = "livraison",
                action_lieu=reservation.lieu_depart.name,
                action_date=reservation.date_heure_debut,

            ) 
            livraison.save()
            

            restitution = Livraison.objects.create(
                date_de_livraison=dt_date_valid_retour,
                kilomtrage=km_retour,
                lv_note=ret_note,
                reservation = reservation,
                name = reservation.name,
                opt_protection_caution = reservation.opt_protection.caution,
                status = reservation.status,
                date_heure_debut = reservation.date_heure_debut,
                date_heure_fin = reservation.date_heure_fin,
                date_de_reservation = reservation.create_date,
                nbr_jour_reservation = reservation.nbr_jour_reservation,
                duree_dereservation = reservation.duree_dereservation,
                lieu_depart = reservation.lieu_depart,
                zone = reservation.zone,
                lieu_retour = reservation.lieu_retour,
                vehicule = reservation.vehicule,
                modele = reservation.modele,
                carburant = reservation.carburant,
                client = reservation.client,
                nom = reservation.nom,
                prenom = reservation.prenom,
                email = reservation.email,
                mobile = reservation.mobile,
                total_reduit_euro = reservation.reste_payer,
                total_payer = reservation.reste_payer,
                stage = 'reserve',
                lv_type = "restitution",
                action_lieu=reservation.lieu_retour.name,
                action_date=reservation.date_heure_fin,
            ) 
            restitution.save()
            if not livraison : 
                return JsonResponse({"error": "Livraison non creer"}, status=400) 
            if not restitution : 
                return JsonResponse({"error": "restitution non creer"}, status=400)
                
        if not payment : 
            return JsonResponse({"error": "payment non creer"}, status=400)
    
        return JsonResponse({"finish":True,"message": "record creer avec succé", "reservation_name":reservation.name}, status=200)       
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def ajuster_les_duree(request):
    try:
        reservations = Reservation.objects.all()

        for reservation in reservations:
            print("reservation number : ", reservation.name)
            try:
                date_depart_obj = datetime.strptime(reservation.date_depart_char, "%d/%m/%Y").date()
                date_retour_obj = datetime.strptime(reservation.date_retour_char, "%d/%m/%Y").date()
            except:
                date_depart_obj = datetime.strptime(reservation.date_depart_char, "%Y-%m-%d").date()
                date_retour_obj = datetime.strptime(reservation.date_retour_char, "%Y-%m-%d").date()
            total_days = (date_retour_obj - date_depart_obj).days
            duree = f"{total_days} jours"

            reservation.nbr_jour_reservation = total_days
            reservation.duree_dereservation = duree
            reservation.save()

            print("reservation : ",reservation.name,"depart retour : ",reservation.du_au,"total days : ",duree)
        return JsonResponse({"message": "fin"}, status=200)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def cancel__button_view(request):
    try:
        reservation_id = request.GET.get("reservation_id")
        motif_id = request.GET.get("motif")

        reservation = get_object_or_404(Reservation, id=reservation_id)

        if reservation.status in ["annule", "rejete"] or reservation.etat_reservation == "loue":
            return JsonResponse({"message": "La réservation ne peut pas être annulée"}, status=400)

        reservation.status = "annule"
        reservation.etat_reservation = "annule"
        reservation.save()

        Livraison.objects.filter(reservation=reservation).delete()

        days = (reservation.date_heure_debut.date() - date.today()).days

        periode = Periode.objects.filter(
            date_debut__lt=reservation.date_heure_debut.date(),
            date_fin__gt=reservation.date_heure_fin.date()
        ).first()

        if not periode:
            return JsonResponse({"message": "Période introuvable"}, status=400)

        condition = ConditionAnnulation.objects.get(id=1)

        montant_ref = None
        if periode.saison == condition.basse_saison:
            seuil = condition.basse_montant
        elif periode.saison == condition.haute_saison:
            seuil = condition.haute_montant
        else:
            return JsonResponse({"message": "Saison non reconnue"}, status=400)

        if days >= seuil:
            if reservation.montant_paye > reservation.prix_jour:
                montant_ref = reservation.montant_paye - reservation.prix_jour
        else:
            if reservation.montant_paye >= reservation.prix_jour:
                montant_ref = reservation.montant_paye - 15

        if montant_ref:
            remboursement = RefundTable.objects.create(
                name=reservation.name,
                reservation=reservation,
                amount=float(montant_ref),
                status='en_attente',
                date=datetime.now()
            )
            
            sujet = f"Annulation de votre reservation N°= {reservation.name}"
            sujet_ceo = f"Annulation de  reservation N°= {reservation.name}"
            expediteur = settings.EMAIL_HOST_USER
            
            html_message = render_to_string('email/annulation_email.html', {
                "referance":reservation.name,
                "annuler_raison":reservation.annuler_raison.name,
                "client":reservation.client.name,
            })
            html_message_ceo = """
                <p>Bonjour,</p>

                <p>Une réservation vient d’être <strong>annulée</strong>.<br>
                Voici les détails :</p>

                <ul>
                    <li><strong>Client :</strong> {reservation.client.name}</li>
                    <li><strong>Référence :</strong> {reservation.name}</li>
                    <li><strong>Cause d’annulation :</strong> {reservation.annuler_raison.name}</li>
                    <li><strong>Montant a rembourser :</strong> {montant_ref}</li>
                </ul>

                <p>Ceci est une notification automatique pour information.</p>

                <p>Cordialement,<br>
                Le système Backoffice</p>
                """

            send_mail(
                sujet,
                strip_tags(html_message),  
                expediteur,
                [reservation.email],
                html_message=html_message,
                fail_silently=False,
            )
            send_mail(
                sujet_ceo,
                strip_tags(html_message_ceo),  
                expediteur,
                ["contact@safarelamir.com"],
                html_message=html_message_ceo,
                fail_silently=False,
            )
            return JsonResponse({
                "message": "Réservation annulée avec succès, remboursement en attente",
                "remboursement_id": remboursement.id
            }, status=200)
        
        
        sujet = f"Annulation de votre reservation N°= {reservation.name}"
        sujet_ceo = f"Annulation de  reservation N°= {reservation.name}"
        expediteur = settings.EMAIL_HOST_USER
        
        html_message_ceo = """
                <p>Bonjour,</p>

                <p>Une réservation vient d’être <strong>annulée</strong>.<br>
                Voici les détails :</p>

                <ul>
                    <li><strong>Client :</strong> {reservation.client.name}</li>
                    <li><strong>Référence :</strong> {reservation.name}</li>
                    <li><strong>Cause d’annulation :</strong> {reservation.annuler_raison.name}</li>
                    <li><strong>Pas de remboursement</strong></li>
                </ul>

                <p>Ceci est une notification automatique pour information.</p>

                <p>Cordialement,<br>
                Le système Backoffice</p>
                """

        send_mail(
            sujet,
            strip_tags(html_message),  
            expediteur,
            [reservation.email],
            html_message=html_message,
            fail_silently=False,
        )
        send_mail(
            sujet_ceo,
            strip_tags(html_message_ceo),  
            expediteur,
            ["contact@safarelamir.com"],
            html_message=html_message_ceo,
            fail_silently=False,
        )

        return JsonResponse({"message": "Réservation annulée avec succès, pas de remboursement"}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def ajouter_ecart(request):
    try:
        reservation_id = request.GET.get("reservation_id")
        montant = request.GET.get("montant")

        reservation = Reservation.objects.get(id=reservation_id)
        
        old_total = reservation.total_reduit_euro if reservation.total_reduit_euro else 0
        old_reste = reservation.reste_payer if reservation.reste_payer else 0

        reservation.total_reduit_euro = float(old_total) + float(montant)
        reservation.reste_payer = float(old_reste) + float(montant) if (float(old_reste) + float(montant))>0 else 0

        livs = Livraison.objects.filter(name=reservation.name)

        for liv in livs:
            reste_payer_liv = liv.total_reduit_euro if liv.total_reduit_euro else 0
            total_payer_liv = liv.total_payer if liv.total_payer else 0

            liv.total_reduit_euro = float(reste_payer_liv) + float(montant) if (float(reste_payer_liv) + float(montant)) > 0 else 0
            liv.total_payer = float(total_payer_liv) + float(montant) if (float(total_payer_liv) + float(montant)) > 0 else 0
            liv.save()

        reservation.save()

        return HttpResponse({"status":"operation"}, status=200)    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


def poncarte_download_(request):
    livraison_id = request.GET.get("livraison_id")
    
    if not livraison_id:
        return HttpResponse("Livraison non disponible", status=404)
    
    livraison = get_object_or_404(Livraison, id=livraison_id)
    
    # Chemin correct de l'image (notez l'espace dans le nom)
    image_path = os.path.join(settings.BASE_DIR, 'api', 'static', 'images', 'nom (1).jpg')
    
    try:
        # Lire l'image et la convertir en base64
        with open(image_path, 'rb') as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        
        context = {
            "Nom": livraison.nom,
            "Prenom": livraison.prenom,
            "background_image": f"data:image/jpeg;base64,{image_base64}",
        }
    except FileNotFoundError:
        # Si l'image n'est pas trouvée, continuer sans fond
        context = {
            "Nom": livraison.nom,
            "Prenom": livraison.prenom,
            "background_image": "",
        }
    
    html_string = render_to_string("poncarte.html", context)
    html = HTML(string=html_string)
    pdf_file = html.write_pdf()
    
    safe_name = "".join(c for c in livraison.client.name if c.isalnum() or c in (' ', '-', '_')).strip()
    file_name = f"poncarte_{safe_name}.pdf"
    
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    
    return response


def confirme_reservation_view(request):
    try:
        reservation_id = request.GET.get("reservation_id")
        reservation = Reservation.objects.get(id=reservation_id)

        if not reservation :
            return JsonResponse({'operation': "reservation non trouvé"}, status=404)
        
        if reservation.status == "confirmee":
            return JsonResponse({'operation': "operation non autoriser"}, status=400)
        
        vehicule_final = reservation.vehicule

        reservations_existantes = Reservation.objects.filter(
            vehicule=reservation.vehicule,
            status="confirmee",
            date_heure_debut__lt=reservation.date_heure_fin,
            date_heure_fin__gt=reservation.date_heure_debut
        )
        blockage_existe = BlockCar.objects.filter(
            vehicule=reservation.vehicule,
            date_from__lte=reservation.date_heure_fin.date(),
            date_to__gte=reservation.date_heure_debut.date()
        )

        if reservations_existantes.exists() or blockage_existe:
            vehicule_alternatif_trouve = False

            vehicules_meme_modele = Vehicule.objects.filter(modele=reservation.modele,zone=reservation.zone).exclude(id=reservation.vehicule.id)
            
            for vehicule in vehicules_meme_modele:

                reservations_sur_vehicule = Reservation.objects.filter(
                    vehicule=vehicule,
                    status="confirmee",
                    date_heure_debut__lt=reservation.date_heure_fin,
                    date_heure_fin__gt=reservation.date_heure_debut
                )

                blockage_sur_vehicule = BlockCar.objects.filter(
                    vehicule=vehicule,
                    date_from__lte=reservation.date_heure_fin.date(),
                    date_to__gte=reservation.date_heure_debut.date()
                )

                if not reservations_sur_vehicule.exists() and not blockage_sur_vehicule.exists():
                    vehicule_final = vehicule
                    vehicule_alternatif_trouve = True
                    break

            if not vehicule_alternatif_trouve:
                return JsonResponse({"operation": "Le véhicule n'est pas disponible."}, status=400)
        
        reservation.vehicule = vehicule_final
        
        reservation.status = 'confirmee'
        reservation.save()

        livraison = Livraison.objects.create(
            reservation = reservation,
            name = reservation.name,
            opt_protection_caution = reservation.opt_protection.caution,
            opt_protection = reservation.opt_protection.name,
            opt_carburant = reservation.opt_plein_carburant,
            opt_carburant_check = True if reservation.opt_plein_carburant else False,
            opt_klm = reservation.opt_klm,
            opt_klm_check = True if reservation.opt_klm else False,
            opt_nd_driver = reservation.opt_nd_driver ,
            opt_nd_driver_check = True if reservation.opt_nd_driver else False,
            opt_sb_a = reservation.opt_siege_a,
            opt_sb_a_check = True if reservation.opt_siege_a else False,
            opt_sb_b = reservation.opt_siege_b,
            opt_sb_b_check = True if reservation.opt_siege_b else False,
            opt_sb_c = reservation.opt_siege_c,
            opt_sb_c_check = True if reservation.opt_siege_c else False,
            status = reservation.status,
            date_heure_debut = reservation.date_heure_debut,
            date_heure_fin = reservation.date_heure_fin,
            date_de_reservation = reservation.create_date,
            nbr_jour_reservation = reservation.nbr_jour_reservation,
            duree_dereservation = reservation.duree_dereservation,
            lieu_depart = reservation.lieu_depart,
            zone = reservation.zone,
            lieu_retour = reservation.lieu_retour,
            vehicule = reservation.vehicule,
            modele = reservation.modele,
            carburant = reservation.carburant,
            client = reservation.client,
            nom = reservation.nom,
            prenom = reservation.prenom,
            email = reservation.email,
            mobile = reservation.mobile,
            total_reduit_euro = reservation.reste_payer,
            total_payer = reservation.reste_payer,
            stage = 'reserve',
            lv_type = "livraison",
            action_lieu=reservation.lieu_depart.name,
            action_date=reservation.date_heure_debut,
            date_depart_char_ = reservation.date_depart_char if reservation.date_depart_char else None,
            date_retour_char_ = reservation.date_retour_char if reservation.date_retour_char else None,
            heure_depart_char_ = reservation.heure_depart_char if reservation.heure_depart_char else None,
            heure_retour_char_ = reservation.heure_retour_char if reservation.heure_retour_char else None,
            num_vol = reservation.num_vol if reservation.num_vol else None,
        ) 
        livraison.save()

        restitution = Livraison.objects.create(
            reservation = reservation,
            name = reservation.name,
            opt_protection_caution = reservation.opt_protection.caution,
            opt_protection = reservation.opt_protection.name,
            opt_carburant = reservation.opt_plein_carburant,
            opt_carburant_check = True if reservation.opt_plein_carburant else False,
            opt_klm = reservation.opt_klm,
            opt_klm_check = True if reservation.opt_klm else False,
            opt_nd_driver = reservation.opt_nd_driver ,
            opt_nd_driver_check = True if reservation.opt_nd_driver else False,
            opt_sb_a = reservation.opt_siege_a,
            opt_sb_a_check = True if reservation.opt_siege_a else False,
            opt_sb_b = reservation.opt_siege_b,
            opt_sb_b_check = True if reservation.opt_siege_b else False,
            opt_sb_c = reservation.opt_siege_c,
            opt_sb_c_check = True if reservation.opt_siege_c else False,
            status = reservation.status,
            date_heure_debut = reservation.date_heure_debut,
            date_heure_fin = reservation.date_heure_fin,
            date_de_reservation = reservation.create_date,
            nbr_jour_reservation = reservation.nbr_jour_reservation,
            duree_dereservation = reservation.duree_dereservation,
            lieu_depart = reservation.lieu_depart,
            zone = reservation.zone,
            lieu_retour = reservation.lieu_retour,
            vehicule = reservation.vehicule,
            modele = reservation.modele,
            carburant = reservation.carburant,
            client = reservation.client,
            nom = reservation.nom,
            prenom = reservation.prenom,
            email = reservation.email,
            mobile = reservation.mobile,
            total_reduit_euro = reservation.reste_payer,
            total_payer = reservation.reste_payer,
            stage = 'reserve',
            lv_type = "restitution",
            action_lieu=reservation.lieu_retour.name,
            action_date=reservation.date_heure_fin,
            date_depart_char_ = reservation.date_depart_char if reservation.date_depart_char else None,
            date_retour_char_ = reservation.date_retour_char if reservation.date_retour_char else None,
            heure_depart_char_ = reservation.heure_depart_char if reservation.heure_depart_char else None,
            heure_retour_char_ = reservation.heure_retour_char if reservation.heure_retour_char else None,
            num_vol = reservation.num_vol if reservation.num_vol else None,
        ) 
        restitution.save()
        sujet = f"Confirmation de votre reservation N°= {reservation.name}"
        expediteur = settings.EMAIL_HOST_USER

        html_message = render_to_string('email/confirmation_email.html', {
            "referance":reservation.name,
            "mobile_one":reservation.lieu_depart.mobile,
            "adresse_one":reservation.lieu_depart.address,
            "mobile_two":reservation.lieu_retour.mobile,
            "adresse_two":reservation.lieu_retour.address,
            'client': reservation.client.nom,
            'client_prenom':reservation.client.prenom,
            'durrée':reservation.duree_dereservation,
            'model_name':reservation.model_name,
            'reste_paye':reservation.reste_payer,
            'caution':reservation.opt_protection_caution,
            "date_depart_char" : reservation.date_depart_char,
            "date_retour_char" : reservation.date_retour_char,
            "heure_depart_char" : reservation.heure_depart_char,
            "heure_retour_char" : reservation.heure_retour_char,
            'date_depart':reservation.date_depart_char,
            'heure_depart':reservation.heure_depart_char,
            'date_retoure':reservation.date_retour_char,
            'haure_retour':reservation.heure_retour_char,
            'lieu_depart':reservation.lieu_depart.name,
            'lieu_depart_id':f"https://api.safarelamir.com/location-description/?lieu_id={reservation.lieu_depart.id}",
            'lieu_retour':reservation.lieu_retour.name,
            'lieu_retour_id':f"https://api.safarelamir.com/location-description/?lieu_id={reservation.lieu_retour.id}",

        })

        send_mail(
            sujet,
            strip_tags(html_message),  
            expediteur,
            [reservation.email],
            html_message=html_message,
            fail_silently=False,
        )


        return JsonResponse({'operation': "operation terminé"}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

def combined_document_download(request):
    reservation_id = request.GET.get("reservation_id")
    livraison_id = request.GET.get("livraison_id")
    
    if reservation_id:
        reservation = Reservation.objects.get(id=reservation_id)
        livraison = Livraison.objects.filter(reservation=reservation).first()  
    elif livraison_id:
        livraison = Livraison.objects.get(id=livraison_id)
        reservation = livraison.reservation
    else:
        return HttpResponse("Aucun ID fourni", status=404)

    date_heure_depart = reservation.date_heure_debut
    date_heure_retour = reservation.date_heure_fin

    date_debut = reservation.date_depart_char
    heure_debut = reservation.heure_depart_char 
    date_fin = reservation.date_retour_char
    heure_fin = reservation.heure_retour_char
    birthday_date = None
    permis = None

    birthday_date = reservation.client.date_de_naissance
    birthday = birthday_date.strftime("%d %B %Y") if birthday_date else None 
    permis = reservation.client.date_de_permis
    permit_date = permis.strftime("%B/%Y") if permis else None

    taux_change = TauxChange.objects.get(id=2)
    taux = taux_change.montant

    protection = reservation.opt_protection 
    protection_name = " "
    protection_dercription = " "

    if protection and "MAX" in protection.option_code :
        protection_name = " ✔      Assurance Protection :  Maximale:"
        protection_dercription = "Cette couverture inclut la protection des pneus, des vitres de portes , ainsi le bris de glace involontaire. Elle permet également de bénéficier d'une caution réduite par rapport à la protection standard."
    elif protection and "STANDART" in protection.option_code :
        protection_name = "✔      Assurance Protection :  Standard:"
        protection_dercription = "Cette couverture inclut la protection des pneus, des vitres de portes. Elle permet également de bénéficier d'une caution réduite par rapport à la protection Basique."

    nd_clinet = None
    if reservation.nd_client_id:  
        nd_clinet = reservation.nd_client
    
    nd_client_name = " "
    permi_desc = " "
    nd_client_name_ = nd_clinet.name if nd_clinet else " "
    permis_nd = nd_clinet.date_de_permis if nd_clinet else " "
    permit_date_nd = permis_nd.strftime("%B/%Y") if nd_clinet and permis_nd else None
    
    if nd_clinet :
        nd_client_name = f"✔ 2ème conducteur : {nd_client_name_} -"
        permi_desc = f" Permis de conduire délivré le :{permit_date_nd}"

    limit_klm = livraison.nbr_jour_reservation * 250

    confirmation_context = {
        "REF": reservation.name,
        "SERVICE": reservation.lieu_depart.mobile,
        "LIEU_DEPART": reservation.lieu_depart.name,
        "address": reservation.lieu_depart.address,
        "LIEU_RETOIUR": reservation.lieu_retour.name,
        "NOM": reservation.nom,
        "PRÉNOM": reservation.prenom,
        "DATE_DE_NAISSANCE": birthday,
        "DATE_PERMIS": permit_date,
        "NOM_2EME_CONDUCTEUR": reservation.nom_nd_condicteur if reservation.nom_nd_condicteur else None,
        "Prenom_2EME_CONDUCTEUR":reservation.prenom_nd_condicteur if reservation.prenom_nd_condicteur else None,
        "DATE_PERMIS_2EME": permi_desc,
        "DATE_DEPART": reservation.date_depart_char,
        "HEURE_DEPART": reservation.heure_depart_char,
        "DATE_RETOUR": reservation.date_retour_char,
        "HEUERE_RETOUR": reservation.heure_retour_char,
        "DUREE_RESERVATION": reservation.duree_dereservation,
        "NOM_VEHICULE": reservation.modele.name,
        "MATRICULE": reservation.vehicule.matricule,
        "CAUTION": reservation.opt_protection_caution,
        "TOTAL": reservation.total_reduit_euro,
        "PROTECTION_NAME": protection_name,
        "DESCRIPTION_PROTECTION": protection_dercription,
        "NUM_VOL": reservation.num_vol,
        "RESTE_PAYE": reservation.reste_payer,
        "VERSER": reservation.total_reduit_euro - reservation.reste_payer,
        "klm_limit": f"{limit_klm} km (0,4 €/km supplémentaire)" if not reservation.opt_klm or not reservation.opt_klm_name else "Kilométrage illimité",
        "protection": reservation.opt_protection.name
    }
    print("-------------------- ici 11111")
    birthday_contract = None
    permis_contract = None

    birthday_date_contract = livraison.client.date_de_naissance if livraison.client else None
    birthday_contract = birthday_date_contract.strftime("%d %B %Y") if birthday_contract else None 
    permis_contract = livraison.client.date_de_permis
    permit_date_contract = permis_contract.strftime("%B/%Y") if permis_contract else None 

    signature_url = f"https://api.safarelamir.com/signature/{livraison.id}/"

    contract_context = {
        "REF": reservation.name,
        "SERVICE": livraison.lieu_depart.mobile,
        "NOM": livraison.nom,
        "PRÉNOM": livraison.prenom,
        "DATE_DE_NAISSANCE": birthday_contract,
        "DATE_PERMIS": permit_date_contract,
        "NOM_2EME_CONDUCTEUR": reservation.nom_nd_condicteur if reservation.nom_nd_condicteur else None,
        "Prenom_2EME_CONDUCTEUR":reservation.prenom_nd_condicteur if reservation.prenom_nd_condicteur else None,
        "DATE_PERMIS_2EME": f" - Permis de conduire délivré le : {permi_desc}",
        "DATE_DEPART": reservation.date_depart_char,
        "HEURE_DEPART": reservation.heure_depart_char,
        "DATE_RETOUR": reservation.date_retour_char,
        "HEUERE_RETOUR": reservation.heure_retour_char,
        "DUREE_RESERVATION": livraison.duree_dereservation,
        "NOM_VEHICULE": livraison.modele.name,
        "MATRICULE": livraison.vehicule.matricule,
        "CAUTION": reservation.opt_protection_caution * taux,
        "TOTAL": reservation.total_reduit_euro * taux,
        "SIGNATURE_URL": signature_url,
        "PROTECTION_NAME": protection_name,
        "DESCRIPTION_PROTECTION": protection_dercription,
    }
    print("-------------------- ici 222222")

    # Charger l'image en base64
    image_path = os.path.join(settings.BASE_DIR, 'api', 'static', 'images', 'nom (1).jpg')
    try:
        with open(image_path, 'rb') as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        background_image = f"data:image/jpeg;base64,{image_base64}"
    except FileNotFoundError:
        background_image = ""

    poncarte_context = {
        "Nom": livraison.nom,
        "Prenom": livraison.prenom,
        "background_image": background_image,
    }
    print("-------------------- ici 33333333333")

    # Générer les pages séparément
    confirmation_html_string = render_to_string("confirmation_pdf.html", confirmation_context)
    contract_html_string = render_to_string("contract_pdf.html", contract_context)
    poncarte_html = render_to_string("poncarte.html", poncarte_context)

    # CSS pour les marges des deux premières pages
    css_with_margins = CSS(string='''
        @page { margin: 4px 12px 4px 12px; padding: 0; }
        body, html { margin: 4px 12px 4px 12px; padding: 0; }
    ''')

    # CSS pour la page poncarte (sans marges)
    css_no_margins = CSS(string='''
        @page { margin: 0; padding: 0; }
        body, html { margin: 0; padding: 0; }
    ''')

    # Générer les PDFs séparément
    confirmation_pdf = HTML(string=confirmation_html_string).write_pdf(stylesheets=[css_with_margins])
    contract_pdf = HTML(string=contract_html_string).write_pdf(stylesheets=[css_with_margins])
    poncarte_pdf = HTML(string=poncarte_html).write_pdf(stylesheets=[css_no_margins])

    # Fusionner les PDFs avec PyPDF2
    from PyPDF2 import PdfMerger
    import io

    merger = PdfMerger()
    merger.append(io.BytesIO(confirmation_pdf))
    merger.append(io.BytesIO(contract_pdf))
    merger.append(io.BytesIO(poncarte_pdf))

    output = io.BytesIO()
    merger.write(output)
    merger.close()
    output.seek(0)

    file_name = f"document_{reservation.name}.pdf"
    response = HttpResponse(output.read(), content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response

def confirmation_download(request):
    resrevation_id = request.GET.get("resrevation_id")

    if not resrevation_id : 
        return HttpResponse("Reservation non disponible", status=404)

    livraison = Reservation.objects.get(id=resrevation_id)
    date_heure_depart = livraison.date_heure_debut
    date_heure_retour = livraison.date_heure_fin

    date_debut = date_heure_depart.strftime("%d %B %Y") 
    heure_debut = date_heure_depart.strftime("%H:%M")  

    date_fin = date_heure_retour.strftime("%d %B %Y")
    heure_fin = date_heure_retour.strftime("%H:%M")

    birthday_date = livraison.client.date_de_naissance
    birthday = birthday_date.strftime("%d %B %Y") if birthday_date else None

    permis = livraison.client.date_de_permis
    permit_date = permis.strftime("%B/%Y") if permis else None

    taux_change = TauxChange.objects.get(id=2)
    taux = taux_change.montant

    protection = livraison.opt_protection 

    protection_name = " "
    protection_dercription = " "

    if protection and "MAX" in protection.option_code :
        protection_name = " ✔      Assurance Protection :  Maximale:"
        protection_dercription = "Cette couverture inclut la protection des pneus, des vitres de portes , ainsi le bris de glace involontaire. Elle permet également de bénéficier d’une caution réduite par rapport à la protection standard."
    elif protection and "STANDART" in protection.option_code :
        protection_name = "✔      Assurance Protection :  Standard:"
        protection_dercription = "Cette couverture inclut la protection des pneus, des vitres de portes. Elle permet également de bénéficier d’une caution réduite par rapport à la protection Basique."
    else :
        protection_name = " "
        protection_dercription = " "

    print("protection name : ", protection_name)
    print("protection desc")

    reservation = livraison
    nd_clinet = None
    if reservation.nd_client_id:  
        nd_clinet = reservation.nd_client
    nd_client_name = " "
    permi_desc = " "
    nd_client_name_ = nd_clinet.name if nd_clinet else None
    permis_nd = nd_clinet.date_de_permis if nd_clinet else None
    permit_date_nd = permis_nd.strftime("%B/%Y") if nd_clinet else None
    if nd_clinet :
        nd_client_name = f"✔ 2ème conducteur : {nd_client_name_} -"
        permi_desc = f" Permis de conduire délivré le :{permit_date_nd}"
    else : 
        nd_client_name = " "
        permi_desc = " "

    limit_klm = livraison.nbr_jour_reservation * 250
    
    context = {
        "REF": livraison.name,
        "SERVICE":livraison.lieu_depart.mobile,
        "LIEU_DEPART":livraison.lieu_depart.name,
        "address":livraison.lieu_depart.address,
        "LIEU_RETOIUR":livraison.lieu_retour.name,
        "NOM": livraison.nom,
        "PRÉNOM": livraison.prenom,
        "DATE_DE_NAISSANCE": birthday,
        "DATE_PERMIS":permit_date,
        "NOM_2EME_CONDUCTEUR":reservation.nom_nd_condicteur if reservation.nom_nd_condicteur else None,
        "Prenom_2EME_CONDUCTEUR":reservation.prenom_nd_condicteur if reservation.prenom_nd_condicteur else None,
        "DATE_PERMIS_2EME":permi_desc,
        "DATE_DEPART": livraison.date_depart_char,
        "HEURE_DEPART": livraison.heure_depart_char,
        "DATE_RETOUR": livraison.date_retour_char,
        "HEUERE_RETOUR": livraison.heure_retour_char,
        "DUREE_RESERVATION": livraison.duree_dereservation,
        "NOM_VEHICULE": livraison.modele.name,
        "MATRICULE": livraison.vehicule.matricule,
        "CAUTION": livraison.opt_protection_caution,
        "TOTAL": livraison.total_reduit_euro ,
        "PROTECTION_NAME" : protection_name,
        "DESCRIPTION_PROTECTION": protection_dercription,
        "NUM_VOL": livraison.num_vol,
        "RESTE_PAYE":livraison.reste_payer,
        "VERSER": livraison.total_reduit_euro - livraison.reste_payer,
        "klm_limit": f"{limit_klm} km (0,4 €/km supplémentaire)" if not livraison.opt_klm or not livraison.opt_klm_name else "Kilométrage illimité",
        "protection":livraison.opt_protection.name

    }

    html_string = render_to_string("confirmation_pdf.html", context)

    css_no_margins = CSS(string='''
        @page {
            margin: 4px 12px 4px 12px;
            padding: 0;
        }
        
        body {
            margin:  4px 12px 4px 12px;
            padding: 0;
        }
        
        html {
            margin:  4px 12px 4px 12px;
            padding: 0;
        }
    ''')

    html = HTML(string=html_string)
    pdf_file = html.write_pdf(stylesheets=[css_no_margins])

    file_name = f"confirmation_{livraison.name}.pdf"

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename= "{file_name}"'
    return response

def lieu_rendez_vous_view(request):
    try:
        lieu_id = request.GET.get("lieu_id")        
        if not lieu_id:
            return JsonResponse({'error': 'livraison_id is required'}, status=404)
        if lieu_id == "1" :
            context = {}
            return render(request, 'lieu_oran_airport.html', context)
        elif lieu_id == "2" :
            context = {}
            return render(request, 'lieu_tlemcen.html', context)
        elif lieu_id == "3" :
            context = {}
            return render(request, 'lieu_alger_airport.html', context)
        elif lieu_id == "4" :
            context = {}
            return render(request, 'lieu_constantine.html', context)
        elif lieu_id == "5" or lieu_id == "6" or lieu_id == "9" or lieu_id == "6" or lieu_id == "14" or lieu_id == "15":
            context = {}
            return render(request, 'lieu_other.html', context)
        elif lieu_id == "16" :
            context = {}
            return render(request, 'lieu_alger_agence.html', context)
        elif lieu_id == "17" :
            context = {}
            return render(request, 'lieu_oran_agence.html', context)
        else :
            return JsonResponse({'error': 'lieu non trouvé'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

def update_category_email_view(request):
    try:
        client_id = request.GET.get("client_id")
        category = request.GET.get("category")

        client = ListeClient.objects.get(id=client_id)

        if not client_id or not client or not category :
            return HttpResponse("veillez remplir tous les parametres", status=404)

        elif category == "DRIVER":
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    sujet = f"Mis à jours des point pour {client.name}"
                    expediteur = settings.EMAIL_HOST_USER
                    html_message = render_to_string('email/update_driver_email.html', {
                        "clien_name" : client.name,
                        "points": client.total_points,
                        "category_name": client.category_client_name
                        
                    })
                    
                    send_mail(
                        sujet,
                        strip_tags(html_message),
                        expediteur,
                        [client.email],
                        html_message=html_message,
                        fail_silently=False,
                    ) 

                    return JsonResponse({'message': "Opération réussie"}, status=200)      
                    
                except Exception as mail_error:
                    if attempt == max_retries - 1:  
                        print(f"Erreur envoi email: {mail_error}")
                    else:
                        time.sleep(2) 

        elif category == "ESSENTIEL":
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    sujet = f"Mis à jours des point pour {client.name}"
                    expediteur = settings.EMAIL_HOST_USER
                    html_message = render_to_string('email/update_esssentiel_email.html', {
                        "clien_name" : client.name,
                        "points": client.total_points,
                        "category_name": client.category_client_name
                        
                    })
                    
                    send_mail(
                        sujet,
                        strip_tags(html_message),
                        expediteur,
                        [client.email],
                        html_message=html_message,
                        fail_silently=False,
                    ) 

                    return JsonResponse({'message': "Opération réussie"}, status=200)      
                    
                except Exception as mail_error:
                    if attempt == max_retries - 1:  
                        print(f"Erreur envoi email: {mail_error}")
                    else:
                        time.sleep(2)

        elif category == "EXELLENT":
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    sujet = f"Mis à jours des point pour {client.name}"
                    expediteur = settings.EMAIL_HOST_USER
                    html_message = render_to_string('email/update_exellent_email.html', {
                        "clien_name" : client.name,
                        "points": client.total_points,
                        "category_name": client.category_client_name
                        
                    })
                    
                    send_mail(
                        sujet,
                        strip_tags(html_message),
                        expediteur,
                        [client.email],
                        html_message=html_message,
                        fail_silently=False,
                    ) 

                    return JsonResponse({'message': "Opération réussie"}, status=200)      
                    
                except Exception as mail_error:
                    if attempt == max_retries - 1:  
                        print(f"Erreur envoi email: {mail_error}")
                    else:
                        time.sleep(2)

        elif category == "VIP":
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    sujet = f"Mis à jours des point pour {client.name}"
                    expediteur = settings.EMAIL_HOST_USER
                    html_message = render_to_string('email/update_vip_email.html', {
                        "clien_name" : client.name,
                        "points": client.total_points,
                        "category_name": client.category_client_name
                        
                    })
                    
                    send_mail(
                        sujet,
                        strip_tags(html_message),
                        expediteur,
                        [client.email],
                        html_message=html_message,
                        fail_silently=False,
                    ) 

                    return JsonResponse({'message': "Opération réussie"}, status=200)      
                    
                except Exception as mail_error:
                    if attempt == max_retries - 1:  
                        print(f"Erreur envoi email: {mail_error}")
                    else:
                        time.sleep(2)
                        
        else : 
            return JsonResponse({'message': "Opération échoué"}, status=400)

    except Exception as e:
        return HttpResponse(f"Erreur: {e}", status=500)

def reciept_download(request):
    livraison_id = request.GET.get("livraison_id")

    if not livraison_id : 
        return HttpResponse("Livraison non disponible", status=404)

    livraison = Livraison.objects.get(id=livraison_id)

    today = datetime.today()
    taux_change = TauxChange.objects.get(id=2)
    taux = taux_change.montant
    euro = Decimal(livraison.montant_euro_pay) if livraison.montant_euro_pay else 0
    dinar = Decimal(livraison.montant_dz_pay) if livraison.montant_dz_pay else 0
    price = (euro * Decimal(taux)) + dinar

    context = {
        "ref": livraison.reservation.name,
        "reciept_number":f"Rec-1-{livraison.reservation.name}",
        "client": livraison.client.name,
        "date": today, 
        "motif": "Frais des dégradations",
        "model":livraison.modele.name,
        "duration":livraison.duree_dereservation,
        "degradation":livraison.total_da,
        "kilometrage":livraison.penalit_klm_dinar,
        "carburant":livraison.penalit_carburant,
        "reste_paye":Decimal(livraison.total_reduit_euro) * Decimal(taux),
        "price":price

    }

    html_string = render_to_string("payment_reciept_template.html", context)

    css_no_margins = CSS(string='''
        @page {
            size: 50mm auto;   /* largeur 50mm, hauteur auto selon le contenu */
            margin: 0;         /* pas de marges inutiles */
        }

        body {
            font-size: 10px;   /* police plus petite pour tickets */
            margin: 0;
            padding: 2mm;
        }

        html {
            margin: 0;
            padding: 0;
        }
    ''')

    html = HTML(string=html_string)
    pdf_file = html.write_pdf(stylesheets=[css_no_margins])

    file_name = f"Reçu_{livraison.reservation.name}.pdf"

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename= "{file_name}"'
    return response

def restitution_email_view(request):
    try:
        livraison_id = request.GET.get("livraison_id")
        review = request.GET.get("review")

        reviews_link = None

        livraison = Livraison.objects.get(id=livraison_id)

        if not livraison or livraison is None : 
            return JsonResponse({'error': "there are not livraison with this ref"}, status=status.HTTP_400_BAD_REQUEST)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                sujet = f"Réstitution réussite N = {livraison.reservation.name}"
                expediteur = settings.EMAIL_HOST_USER
            
                html_message = render_to_string('email/restitution_email.html', {
                    "clien_name" : livraison.client.name,
                    "reviews": review,
                    "reviews_link" : reviews_link,
                    "reciept_link":f"https://api.safarelamir.com/reciept-download/?livraison_id={livraison_id}"
                    
                })
                
                send_mail(
                    sujet,
                    strip_tags(html_message),
                    expediteur,
                    [livraison.email],
                    html_message=html_message,
                    fail_silently=False,
                ) 

                return JsonResponse({'message': "Opération réussie"}, status=200)      
                
            except Exception as mail_error:
                if attempt == max_retries - 1:  
                    print(f"Erreur envoi email: {mail_error}")
                else:
                    time.sleep(2)  
        
            
        else:
            return JsonResponse({'message': "l'email n'existe pas"}, status=404)

    except Exception as e:
        return HttpResponse(f"Erreur: {e}", status=500)
    
def pick_up_mail_view(request):
    try:
        livraison_id = request.GET.get("livraison_id")

        livraison = Livraison.objects.get(id=livraison_id)

        if not livraison or livraison is None : 
            return JsonResponse({'error': "there are not livraison with this ref"}, status=status.HTTP_400_BAD_REQUEST)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                sujet = f"Livraison réussite N = {livraison.reservation.name}"
                expediteur = settings.EMAIL_HOST_USER
                html_message = render_to_string('email/livraison_email.html', {
                    "clien_name" : livraison.client.name,
                    "photos_link": f"https://api.safarelamir.com/inspection-report/?livraison_id={livraison_id}",
                    "contract_link":f"https://api.safarelamir.com/contract-download/?livraison_id={livraison_id}"
                    
                })
                
                send_mail(
                    sujet,
                    strip_tags(html_message),
                    expediteur,
                    [livraison.email],
                    html_message=html_message,
                    fail_silently=False,
                ) 

                return JsonResponse({'message': "Opération réussie"}, status=200)      
                
            except Exception as mail_error:
                if attempt == max_retries - 1:  
                    print(f"Erreur envoi email: {mail_error}")
                else:
                    time.sleep(2)  
        
            
        else:
            return JsonResponse({'message': "l'email n'existe pas"}, status=404)

    except Exception as e:
        return HttpResponse(f"Erreur: {e}", status=500)

def contract_download_(request):
    livraison_id = request.GET.get("livraison_id")

    if not livraison_id : 
        return HttpResponse("Livraison non disponible", status=404)

    livraison = Livraison.objects.get(id=livraison_id)
    date_heure_depart = livraison.date_heure_debut
    date_heure_retour = livraison.date_heure_fin

    date_debut = date_heure_depart.strftime("%d %B %Y") 
    heure_debut = date_heure_depart.strftime("%H:%M")  

    date_fin = date_heure_retour.strftime("%d %B %Y")
    heure_fin = date_heure_retour.strftime("%H:%M")

    birthday_date = livraison.client.date_de_naissance
    birthday = birthday_date.strftime("%d %B %Y") if birthday_date is not None else 0

    permis = livraison.client.date_de_permis
    permit_date = permis.strftime("%B/%Y") if permis is not None else 0

    taux_change = TauxChange.objects.get(id=2)
    taux = taux_change.montant



    protection = livraison.reservation.opt_protection 

    protection_name = " "
    protection_dercription = " "

    if protection and "MAX" in protection.option_code :
        protection_name = " ✔      Assurance Protection :  Maximale:"
        protection_dercription = "Cette couverture inclut la protection des pneus, des vitres de portes , ainsi le bris de glace involontaire. Elle permet également de bénéficier d’une caution réduite par rapport à la protection standard."
    elif protection and "STANDART" in protection.option_code :
        protection_name = "✔      Assurance Protection :  Standard:"
        protection_dercription = "Cette couverture inclut la protection des pneus, des vitres de portes. Elle permet également de bénéficier d’une caution réduite par rapport à la protection Basique."
    else :
        protection_name = " "
        protection_dercription = " "

    print("protection : ",protection)
    print("protection code : ", protection.option_code)

    print("protection name : ", protection_name)
    print("protection desc")

    reservation = livraison.reservation
    nd_clinet = None
    if reservation.nd_client_id:  
        nd_clinet = reservation.nd_client
    nd_client_name = " "
    permi_desc = " "
    nd_client_name_ = nd_clinet.name if nd_clinet else " "
    permis_nd = nd_clinet.date_de_permis if nd_clinet else " "
    permit_date_nd = permis_nd.strftime("%B/%Y") if nd_clinet else None
    if nd_clinet :
        nd_client_name = f"✔ 2ème conducteur : {nd_client_name_} -"
        permi_desc = f" Permis de conduire délivré le :{permit_date_nd}"
    else : 
        nd_client_name = " "
        permi_desc = " "
       
    signature_url = f"https://api.safarelamir.com/signature/{livraison_id}/"

    
    context = {
        "REF": livraison.reservation.name,
        "SERVICE":livraison.lieu_depart.mobile,
        "NOM": livraison.nom,
        "PRÉNOM": livraison.prenom,
        "DATE_DE_NAISSANCE": birthday,
        "DATE_PERMIS":permit_date,
        "NOM_2EME_CONDUCTEUR":livraison.reservation.nom_nd_condicteur if livraison.reservation.nom_nd_condicteur else None,
        "Prenom_2EME_CONDUCTEUR":livraison.reservation.prenom_nd_condicteur if livraison.reservation.prenom_nd_condicteur else None,
        "DATE_PERMIS_2EME":f" - Permis de conduire délivré le : {permi_desc}",
        "DATE_DEPART": date_debut,
        "HEURE_DEPART": heure_debut,
        "DATE_RETOUR": date_fin,
        "HEUERE_RETOUR": heure_fin,
        "DUREE_RESERVATION": livraison.duree_dereservation,
        "NOM_VEHICULE": livraison.modele.name,
        "MATRICULE": livraison.vehicule.matricule,
        "CAUTION": livraison.reservation.opt_protection_caution * taux,
        "TOTAL": livraison.reservation.total_reduit_euro * taux,
        "SIGNATURE_URL": signature_url,
        "PROTECTION_NAME" : protection_name,
        "DESCRIPTION_PROTECTION": protection_dercription,

    }

    html_string = render_to_string("contract_pdf.html", context)

    css_no_margins = CSS(string='''
        @page {
            margin: 4px 12px 4px 12px;
            padding: 0;
        }
        
        body {
            margin:  4px 12px 4px 12px;
            padding: 0;
        }
        
        html {
            margin:  4px 12px 4px 12px;
            padding: 0;
        }
    ''')

    html = HTML(string=html_string)
    pdf_file = html.write_pdf(stylesheets=[css_no_margins])

    file_name = f"contrat_{livraison.reservation.name}.pdf"

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename= "{file_name}"'
    return response

def get_signature_by_id(request, livraison_id):
    try:
        attachment = IrAttachment.objects.filter(
            name='signature',
            res_model='livraison',
            res_id=livraison_id,
            mimetype__startswith='image/'
        ).first()

        if not attachment or not attachment.store_fname:
            return HttpResponse("Aucune signature trouvée", status=404)

        ODOO_DATA_DIR = '/mnt/odoo-filestore/safarelamir'
        path = os.path.join(ODOO_DATA_DIR, *attachment.store_fname.split('/'))

        if not os.path.exists(path):
            raise Http404(f"Signature introuvable: {path}")

        with open(path, 'rb') as f:
            raw = f.read()

        mimetype = attachment.mimetype or mimetypes.guess_type(attachment.name or '')[0] or 'application/octet-stream'

        response = HttpResponse(raw, content_type=mimetype)
        response['Content-Disposition'] = f'inline; filename="signature_{livraison_id}.png"'
        response['Cache-Control'] = 'no-cache'
        return response

    except Exception as e:
        return HttpResponse(f"Erreur: {e}", status=500)

def success_pick_up_view(request):
    try:
        livraison_id = request.GET.get("livraison_id")

        
        
        if not livraison_id:
            return JsonResponse({'error': 'livraison_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        livraison = get_object_or_404(Livraison, id=livraison_id)

        date_heure_depart = livraison.date_heure_debut
        date_debut = date_heure_depart.strftime("%d %B %Y") 
        heure_debut = date_heure_depart.strftime("%H:%M")  

        photos = LivraisonIrAttachmentRel.objects.filter(livraison_id=livraison_id)

        photos_list = []
        for i, p in enumerate(photos, start=1):
            url = f'https://api.safarelamir.com/livraison/{livraison.id}/photo/{p.ir_attachment_id}/'
            photos_list.append({
                "number": i,
                "label": f"Photo {i}",   
                "url": url
            })

        context = {
            'livraison': livraison,
            'contract_number': livraison.reservation.name,  
            'client_name': livraison.client.name if livraison.client and livraison.client.name else 'Client',
            'vehicle_name': livraison.modele.name if livraison.modele and livraison.modele.name else 'Véhicule',
            'pickup_date': date_debut if date_debut else 'Date non définie',
            'pickup_time': heure_debut if heure_debut else 'Heure non définie',
            'photos': photos_list,
            'city':livraison.lieu_depart.city.name,
            'lieu':livraison.lieu_depart.name

        }

        return render(request, 'photo_livraison_template.html', context)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

def livraison_photo_by_res(request, livraison_id, attachment_id):
    logger.info(f"Requête reçue: livraison_id={livraison_id}, attachment_id={attachment_id}")
    
    try:
        rel_exists = LivraisonIrAttachmentRel.objects.filter(
            livraison_id=livraison_id,
            ir_attachment_id=attachment_id
        ).exists()

        if not rel_exists:
            raise Http404("Ce fichier n'est pas lié à cette livraison")

        att = get_object_or_404(IrAttachment, pk=attachment_id)
        
        ODOO_DATA_DIR = '/mnt/odoo-filestore/safarelamir'
        path = os.path.join(ODOO_DATA_DIR, *att.store_fname.split('/'))
        
        if not os.path.exists(path):
            logger.error(f"Fichier introuvable: {path}")
            raise Http404(f"Fichier introuvable : {path}")
        
        with open(path, 'rb') as f:
            raw = f.read()
        mimetype = att.mimetype or mimetypes.guess_type(att.name or '')[0] or 'application/octet-stream'
        return HttpResponse(raw, content_type=mimetype)
        
    except Exception as e:
        logger.error(f"Erreur dans livraison_photo_by_res: {str(e)}")
        raise

def coming_soon_email_view(request):
    try:
        ref = request.GET.get("ref")

        
        reservation = Reservation.objects.get(name=ref)

        if not reservation or reservation is None : 
            return JsonResponse({'error': "there are not reservation with this ref"}, status=status.HTTP_400_BAD_REQUEST)
        
        date_heure_depart = reservation.date_heure_debut
        date_heure_retour = reservation.date_heure_fin

        date_debut = date_heure_depart.strftime("%d %B %Y") 
        heure_debut = date_heure_depart.strftime("%H:%M")  

        date_fin = date_heure_retour.strftime("%d %B %Y")
        heure_fin = date_heure_retour.strftime("%H:%M")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                sujet = f"Coming-Up-Soon N = {reservation.name}"
                expediteur = settings.EMAIL_HOST_USER
                html_message = render_to_string('email/coming_soon_email.html', {
                    "clien_name" : reservation.client.name,
                    "reference": ref,
                    "rest_payer": reservation.reste_payer if reservation.reste_payer else 0,
                    "caution": reservation.opt_protection_caution if reservation.opt_protection_caution else 0,
                    "link":"link", #generation du lien
                    "model_name" : reservation.model_name,
                    "duree": reservation.duree_dereservation,
                    "date_depart":date_debut,
                    "heur_depart":heure_debut,
                    "lieu_depart":reservation.lieu_depart.name,
                    "lieu_depart_mobile":reservation.lieu_depart.mobile,
                    "address_one":reservation.lieu_depart.address,
                    "date_retour":date_fin,
                    "heure_fin":heure_fin,
                    "lieu_retour":reservation.lieu_retour.name,
                    "lieu_retour_mobile":reservation.lieu_retour.mobile,
                    "address_two":reservation.lieu_retour.address
                })
                
                send_mail(
                    sujet,
                    strip_tags(html_message),
                    expediteur,
                    [reservation.email],
                    html_message=html_message,
                    fail_silently=False,
                ) 

                return JsonResponse({'message': "Opération réussie"}, status=200)      
                
            except Exception as mail_error:
                if attempt == max_retries - 1:  
                    print(f"Erreur envoi email: {mail_error}")
                else:
                    time.sleep(2)  
        
            
        else:
            return JsonResponse({'message': "l'email n'existe pas"}, status=404)
    
    
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


def solde_history_view_(request):
    try :
        client_id = request.GET.get("client_id")
        page_number = request.GET.get("page")

        country_code = request.headers.get("X-Country-Code")

        if not client_id:
            return JsonResponse({'error': 'client_id est requis'}, status=status.HTTP_400_BAD_REQUEST)

        client = ListeClient.objects.filter(id=client_id).first()

        if not client:
            return JsonResponse({'error': 'Client non trouvé'}, status=status.HTTP_404_NOT_FOUND)
        
        history_queryset = HistoriqueSolde.objects.filter(client=client).order_by('-create_date')  
        
        paginator = Paginator(history_queryset, 10)  
        
        try:
            history_page = paginator.page(page_number)
        except PageNotAnInteger:
            history_page = paginator.page(1)
        except EmptyPage:
            history_page = paginator.page(paginator.num_pages)
        
        taux = 1
        currency = "EUR"

        total_consome = client.solde_consomer

        if country_code =="DZ" :
            currency = "DA"
            taux_change = TauxChange.objects.get(id=2)
            taux = taux_change.montant
        else : 
            taux = 1
        
        history_data = []
        if history_page is not None:
            for record in history_page:
                record_dict = {
                    'currency': currency,
                    'label': record.reservation.name,
                    'label_en': record.reservation.name,
                    'label_ar': record.reservation.name,
                    'montant': float(record.montant) * float(taux) if record.montant is not None else 0,
                    'status':"paiement",
                    'reservation': record.reservation.name
                }
                history_data.append(record_dict)
        
        response_data = {
            'data': history_data,
            'pagination': {
                'total':float(total_consome) * float(taux) if total_consome is not None else 0,
                'current_page': history_page.number,
                'total_pages': paginator.num_pages,
                'total_records': paginator.count,
                'has_next': history_page.has_next(),
                'has_previous': history_page.has_previous(),
                'next_page': history_page.next_page_number() if history_page.has_next() else None,
                'previous_page': history_page.previous_page_number() if history_page.has_previous() else None,
                'per_page': 10
            }
        }
        
        return JsonResponse(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

def client_info_view(request):
    try:
        client_id = request.GET.get("client_id")
        country_code = request.headers.get("X-Country-Code")

        client = ListeClient.objects.filter(id=client_id).first()

        if not client :
            return JsonResponse({'message': "le client n'existe pas"}, status=404)
        
        newsletter_exist = NewsLetter.objects.filter(email=client.email,subscribe="oui").first()

        taux_change = TauxChange.objects.filter(id=2).first()
        taux = taux_change.montant
        
        result = {
            "currency":"DA" if country_code == "DZ" else "EUR",
            "client_id":client.id,
            "nom": client.nom,
            "prenom": client.prenom,
            "email": client.email,
            "birthday": client.date_de_naissance,
            "phone": client.telephone,
            "pemit_date": client.date_de_permis,
            "newsletter": "yes" if newsletter_exist else "no",
            "category":client.categorie_client.name,
            "category_en":client.categorie_client.name_en,
            "category_ar":client.categorie_client.name_ar,
            "solde":float(client.solde) * float(taux) if country_code == "DZ" and client.solde else client.solde,
            "prime_code":client.code_prime,
            "points_total":client.total_points,

        }
        return JsonResponse({'result': result}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

def unsubscribe_newsletter_view(request):
    try:
        email = request.GET.get("email")
        email_exist = NewsLetter.objects.filter(email=email).first()
        
        if email_exist:
            email_exist.subscribe = "non"
            email_exist.save()
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    sujet = f"Désabonnement newsletter"
                    expediteur = settings.EMAIL_HOST_USER
                    html_message = render_to_string('email/newsletter_deconnection_email.html', {
                        "email": email
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
            
            return JsonResponse({'message': "Opération réussie"}, status=200)
        else:
            return JsonResponse({'message': "l'email n'existe pas"}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    

def create_news_letter(request):
    try:
        email = request.GET.get("email")
        email_exist = NewsLetter.objects.filter(email=email).first()
        if not email_exist : 
            NewsLetter.objects.create(
                        email=email,
                    )
            sujet = f"Enregistrement newsletter"
            expediteur = settings.EMAIL_HOST_USER

            html_message = render_to_string('email/newsletter_email.html', {
                "email":email
            })
            send_mail(
                sujet,
                strip_tags(html_message),  
                expediteur,
                [email],
                html_message=html_message,
                fail_silently=False,
            )

            return JsonResponse({'message': "Opération réussie"}, status=status.HTTP_201_CREATED)
        elif email_exist and email_exist.subscribe == "non":
            email_exist.subscribe = "oui"
            email_exist.save()
            sujet = f"Enregistrement newsletter"
            expediteur = settings.EMAIL_HOST_USER

            html_message = render_to_string('email/newsletter_email.html', {
                "email":email
            })
            send_mail(
                sujet,
                strip_tags(html_message),  
                expediteur,
                [email],
                html_message=html_message,
                fail_silently=False,
            )
            return JsonResponse({'message': "Opération réussie"}, status=status.HTTP_201_CREATED)
        else :
            return JsonResponse({'message': "email existe deja"}, status=208)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

def promotion_hompage(request):
    try:
        now = datetime.now()
        promotion_periode = Promotion.objects.filter(fin_visibilite__gte=now, date_fin__gte=now).first()
        
        if not promotion_periode:
            return JsonResponse({"message": "Aucune promotion en cours."}, status=404)
        if promotion_periode.active_passive == True : 

            date_debut = promotion_periode.date_debut
            date_fin = promotion_periode.date_fin

            # Configurer les locales
            locale.setlocale(locale.LC_TIME, "fr_FR.utf8")
            mois_fr_debut = date_debut.strftime("%B")
            mois_fr_fin = date_fin.strftime("%B")

            locale.setlocale(locale.LC_TIME, "en_US.utf8")
            mois_en_debut = date_debut.strftime("%B")
            mois_en_fin = date_fin.strftime("%B")

            # Mapping manuel pour les mois en arabe
            mois_ar_map = {
                "January": "يناير", "February": "فبراير", "March": "مارس", "April": "أبريل",
                "May": "مايو", "June": "يونيو", "July": "يوليو", "August": "أغسطس",
                "September": "سبتمبر", "October": "أكتوبر", "November": "نوفمبر", "December": "ديسمبر"
            }

            # Traduire les mois en arabe
            mois_ar_debut = mois_ar_map.get(mois_en_debut, mois_fr_debut)
            mois_ar_fin = mois_ar_map.get(mois_en_fin, mois_fr_fin)

            # Construction des textes
            if date_debut.month == date_fin.month and date_debut.year == date_fin.year:
                du_au = f"Du {date_debut.day} au {date_fin.day} {mois_fr_fin} {date_fin.year}"
                du_au_en = f"From {date_debut.day} to {date_fin.day} {mois_en_fin} {date_fin.year}"
                du_au_ar = f"من {date_debut.day} إلى {date_fin.day} {mois_ar_fin} {date_fin.year}"
            else:
                du_au = f"Du {date_debut.day} {mois_fr_debut} au {date_fin.day} {mois_fr_fin} {date_fin.year}"
                du_au_en = f"From {date_debut.day} {mois_en_debut} to {date_fin.day} {mois_en_fin} {date_fin.year}"
                du_au_ar = f"من {date_debut.day} {mois_ar_debut} إلى {date_fin.day} {mois_ar_fin} {date_fin.year}"

            return JsonResponse({
                "text_one": f"⚡ {promotion_periode.name} : jusqu'à -{promotion_periode.reduction}%",
                "text_two": f"{du_au}, profitez d'une remise exceptionnelle de *-{promotion_periode.reduction}%* sur toute notre flotte ! 🚗✨",
                "text_one_en": f"⚡ {promotion_periode.name} : up to -{promotion_periode.reduction}%",
                "text_two_en": f"{du_au_en}, take advantage of an exceptional *-{promotion_periode.reduction}%* discount! 🚗✨",
                "text_one_ar": f"⚡ حتى %{promotion_periode.reduction} : {promotion_periode.name}",
                "text_two_ar": f"{du_au_ar}، استفد من خصم استثنائي بقيمة ٪{promotion_periode.reduction} 🚗✨"
            }, status=200, json_dumps_params={'ensure_ascii': False}) 
        else : 
            return JsonResponse({"text":" "}, status=404, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({"message": f"Erreur inattendue : {str(e)}"}, status=500)

def vip_reduction_view(request):

    try:
        country_code = request.headers.get("X-Country-Code")
        response = vip_reduction(country_code=country_code)
        return JsonResponse({"result" :response}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"message": "Données JSON invalides."}, status=400)
    except Exception as e:
        return JsonResponse({"message": f"Erreur inattendue : {str(e)}"}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def protection_put_view(request):
    try:
        data = json.loads(request.body)
        ref = data.get("ref")
        protection = data.get("protection")
        country_code = request.headers.get("X-Country-Code")

        try:
            resultats = modify_protection_request(
                ref=ref,
                protection=protection,
                country_code=None
            )
            reservation = Reservation.objects.filter(name=ref).first()
            to_day = date.today()

            to_pay_value = resultats.get("to_pay")

            if to_pay_value is not None:
                request_factory = RequestFactory()
                fake_request = request_factory.post(
                    path="/create-payment-session-protection/",
                    data=json.dumps({
                        "product_name": f"{reservation.name} | Protection {protection}" ,
                        "description": "montant qui sera prélevé pour ajouter cette protection à vôtre location.",
                        "images": [reservation.photo_link] if reservation.photo_link else [],
                        "unit_amount": int(to_pay_value * 100),
                        "quantity": 1,
                        "currency": "eur",
                        "reservation_id": reservation.id
                    }),
                    content_type="application/json"
                )

                payment_session_response = create_payment_session_protection(fake_request)

                if payment_session_response.status_code != 200:
                    return JsonResponse({"message": "Erreur lors de la création de la session de paiement."}, status=500)

                payment_session_data = json.loads(payment_session_response.content)
                session_id = payment_session_data.get("session_id", "")
                payment_url = payment_session_data.get("url", "")

                return JsonResponse({"refund_message": False, "message": "Modification effectuée avec succès.", "session_id": session_id, "payment_url": payment_url}, status=200)

            return JsonResponse({"message": "Aucune modification requise."}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Données JSON invalides."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def create_payment_session_protection(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

        data = json.loads(request.body)
        product_name = data.get("product_name")
        description = data.get("description")
        images = data.get("images", [])
        unit_amount = data.get("unit_amount")
        quantity = data.get("quantity")
        currency = data.get("currency", "eur")
        reservation_id = data.get("reservation_id")

        if not all([product_name, description, unit_amount, quantity]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        unit_amount = int(unit_amount)
        quantity = int(quantity)

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": product_name,
                            "description": description,
                            "images": images,
                        },
                        "unit_amount": unit_amount,
                    },
                    "quantity": quantity,
                },
            ],
            mode="payment",
            success_url= f"https://safarelamir.com/confirmation?id={reservation_id}",
            cancel_url="https://safarelamir.com/cancel",
        )

        return JsonResponse({"session_id": checkout_session.id, "url": checkout_session.url}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    
def protection_request_view(request):

    ref = request.GET.get("ref")
    protection = request.GET.get("protection")
    country_code = request.headers.get("X-Country-Code")

    if not ref or not protection:
        return JsonResponse({"error": "Les paramètres 'ref' et 'protection' sont requis."}, status=400)

    try:
        resultats = modify_protection_request(
            ref=ref,
            protection=protection,
            country_code=country_code
        )
        return JsonResponse({"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})


def get_all_categories(request):
    categories = CategorieClient.objects.all()
    
    categories_list = []

    for cat in categories:
        category_data = {
            "id": cat.id,
            "name": cat.name,
            "name_en": cat.name_en,
            "name_ar": cat.name_ar,
            "du_pts": cat.du_pts,
            "au_pts": cat.au_pts if cat.au_pts < 10000 else "+∞",
            "reduction": cat.reduction,
        }

        # Options FR
        options_fr = [
            f"Réduction de {cat.reduction}%" if cat.reduction > 0 else None,
            cat.option_one.name if cat.option_one else None,
            cat.option_two.name if cat.option_two else None,
            cat.option_three.name if cat.option_three else None,
            cat.option_four.name if cat.option_four else None,
            cat.option_five.name if cat.option_five else None,
            cat.option_six.name if cat.option_six else None,
            cat.option_seven.name if cat.option_seven else None,
            cat.option_eight.name if cat.option_eight else None,
            cat.option_nine.name if cat.option_nine else None,
            cat.option_ten.name if cat.option_ten else None,
        ]
        options_fr = [opt for opt in options_fr if opt is not None]
        options_fr = list(dict.fromkeys(options_fr))
        options_fr = [
            "Assurance protection Maximale offerte" if opt.strip().lower() == "maximale" else opt
            for opt in options_fr
        ]

        # Options EN
        options_en = [
            f"{cat.reduction}% discount" if cat.reduction > 0 else None,
            cat.option_one.name_en if cat.option_one else None,
            cat.option_two.name_en if cat.option_two else None,
            cat.option_three.name_en if cat.option_three else None,
            cat.option_four.name_en if cat.option_four else None,
            cat.option_five.name_en if cat.option_five else None,
            cat.option_six.name_en if cat.option_six else None,
            cat.option_seven.name_en if cat.option_seven else None,
            cat.option_eight.name_en if cat.option_eight else None,
            cat.option_nine.name_en if cat.option_nine else None,
            cat.option_ten.name_en if cat.option_ten else None,
        ]
        options_en = [opt for opt in options_en if opt is not None]
        options_en = list(dict.fromkeys(options_en))
        options_en = [
            "Free Maximal Protection Insurance" if opt.strip().lower() == "maximum" else opt
            for opt in options_en
        ]

        # Options AR
        options_ar = [
            f"خصم %{cat.reduction}" if cat.reduction > 0 else None,
            cat.option_one.name_ar if cat.option_one else None,
            cat.option_two.name_ar if cat.option_two else None,
            cat.option_three.name_ar if cat.option_three else None,
            cat.option_four.name_ar if cat.option_four else None,
            cat.option_five.name_ar if cat.option_five else None,
            cat.option_six.name_ar if cat.option_six else None,
            cat.option_seven.name_ar if cat.option_seven else None,
            cat.option_eight.name_ar if cat.option_eight else None,
            cat.option_nine.name_ar if cat.option_nine else None,
            cat.option_ten.name_ar if cat.option_ten else None,
        ]
        options_ar = [opt for opt in options_ar if opt is not None]
        options_ar = list(dict.fromkeys(options_ar))
        options_ar = [
            "تأمين حماية قصوى مجاني" if "الحد الأقصى" in opt.replace("الاقصى", "الأقصى").strip() else opt
            for opt in options_ar
        ]

        # Si on a au moins une option dans une des langues
        if options_fr or options_en or options_ar:
            category_data["option"] = {
                "fr": options_fr,
                "en": options_en,
                "ar": options_ar
            }

        categories_list.append(category_data)

    return JsonResponse({"categories": categories_list}, safe=False, json_dumps_params={'ensure_ascii': False})

@csrf_exempt
def ajouter_liste_attente(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            client_id = data.get('client_id')
            client = None 
            if client_id is not None: 
                try:
                    client = ListeClient.objects.get(id=client_id)
                except ObjectDoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Client non trouvé'}, status=404)
            else : 
                full_name = data.get('full_name')
                email = data.get('email')
                phone = data.get('phone')

            car_model_id = data.get('car_model_id')
            lieu_depart_id = data.get('lieu_depart_id')
            lieu_retour_id = data.get('lieu_retour_id')
            date_depart = data.get('date_depart')
            date_retour = data.get('date_retour')
            heure_debut = data.get('heure_debut')
            heure_fin = data.get('heure_fin')


            try:
                if car_model_id is not None:
                    car_model = Modele.objects.get(id=car_model_id)
                else:
                    car_model = None
                lieu_depart = Lieux.objects.get(id=lieu_depart_id)
                lieu_retour = Lieux.objects.get(id=lieu_retour_id)
            except ObjectDoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Modèle ou lieu non trouvé'}, status=404)
            
            def generate_unique_name():
                while True:
                    code = str(random.randint(1000, 9999))
                    if not ListeAttente.objects.filter(name=code).exists():
                        return code

            nouvelle_liste_attente = ListeAttente(
                name=generate_unique_name(),
                client=client,
                full_name=f"{client.nom} {client.prenom}" if client is not None else full_name ,
                email=client.email if client is not None else email,
                phone_number=client.telephone if client is not None else phone,
                car_model=car_model,
                lieu_depart=lieu_depart,
                date_depart=date_depart,
                lieu_retour=lieu_retour,
                date_retour=date_retour,
                heure_debut=heure_debut,
                heure_fin=heure_fin
            )

            nouvelle_liste_attente.save()

            return JsonResponse({'status': 'success', 'message': 'Enregistrement ajouté avec succès'}, status=201)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    else:
        return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)

@csrf_exempt
def create_contact_message(request):
    if request.method == 'POST':
        try:
            print("inside")
            data = json.loads(request.body.decode('utf-8'))
            nom_complet = data.get('nom_complet')
            email = data.get('email')
            message_text = data.get('message') 
            client_id = data.get('client_id')

            print(nom_complet)
            print(email)
            print(message_text)


            if not nom_complet or not email or not message_text : 
                return JsonResponse({"created": False, "message": "les champs nom_complet et email et message_text sont requis."}, status=405)


            name = str(random.randint(1000, 9999))

            create_date = datetime.now()
            if client_id : 
                client = ListeClient.objects.filter(id=client_id).first()
            else : 
                client = None

            ContactMessage.objects.create(
                name=name,
                nom_complet=nom_complet,
                email=email,
                message=message_text, 
                client=client,
                create_date=create_date,
            )

            return JsonResponse({'message': "Opération réussie"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return JsonResponse({"created": False, "message": "Seules les requêtes POST sont autorisées."}, status=405)
        
@csrf_exempt
def create_account_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            email = data.get('email')
            nom = data.get('nom')
            prenom = data.get('prenom')
            phone = data.get('phone')
            birthday = data.get('birthday')
            permis_date = data.get('permis_date')

            if not all([email, nom, prenom, phone, birthday, permis_date]):
                return JsonResponse({"created": False, "message": "Tous les champs sont requis."}, status=400)

            response = create_account(email, nom, prenom, phone, birthday, permis_date)
            return JsonResponse(response, status=200 if response["created"] else 400)

        except json.JSONDecodeError:
            return JsonResponse({"created": False, "message": "Données JSON invalides."}, status=400)
        except Exception as e:
            return JsonResponse({"created": False, "message": f"Erreur inattendue : {str(e)}"}, status=500)

    return JsonResponse({"created": False, "message": "Seules les requêtes POST sont autorisées."}, status=405)


def verify_and_edit(ref, lieu_depart, lieu_retour, date_depart, heure_depart, date_retour, heure_retour, country_code):
    try:
        ma_reservation = Reservation.objects.filter(name=ref).first()
        if not ma_reservation:
            return {"message": "Réservation non trouvée."}
        date_depart_heure = datetime.strptime(f"{date_depart} {heure_depart}", '%Y-%m-%d %H:%M')
        date_retour_heure = datetime.strptime(f"{date_retour} {heure_retour}", '%Y-%m-%d %H:%M')
        date_depart_heure += timedelta(hours=1)
        date_retour_heure += timedelta(hours=1)

        verify_value = verify_and_calculate(
            ref,
            lieu_depart,
            lieu_retour,
            date_depart,
            heure_depart,
            date_retour,
            heure_retour,
            country_code
        )
        lieu_depart_obj = Lieux.objects.filter(id=lieu_depart).first()
        ma_reservation = Reservation.objects.filter(name=ref).first()
        get_vehicule_id = ma_reservation.vehicule.numero
        vehicule = Vehicule.objects.get(numero=get_vehicule_id)
        vehicle_reservations = Reservation.objects.filter(vehicule=vehicule)
        is_available = True
        diff = 0

        for reservation in vehicle_reservations:
            if (date_depart_heure < reservation.date_heure_fin and date_retour_heure > reservation.date_heure_debut and ref != ma_reservation.name):
                is_available = False
                break
        if is_available == True :
            get_total = ma_reservation.total_reduit_euro
            get_options_total = ma_reservation.options_total
            get_status = ma_reservation.status
            get_reservation_satus = ma_reservation.etat_reservation
            if get_status != "confirmee" or get_reservation_satus != 'reserve' :
                return {"modified":"no","message": "Réservation mise à jour avec succès."}
        if verify_value and verify_value[0].get('is_available') == "yes":
            date_depart = datetime.strptime(date_depart, "%Y-%m-%d").date()
            date_retour = datetime.strptime(date_retour, "%Y-%m-%d").date()
            total_days = (date_retour - date_depart).days
            tarifs = Tarifs.objects.filter(
                Q(modele = ma_reservation.modele)&
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
                frais_dossier_prix = 0
                nbr_jour = 0
                frais_livraison_prix = 0
                supplement_prix = 0
                retard_prix = 0



                if total > 0:
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
                    
                    frais_dossier = Options.objects.filter(option_code="FRAIS_DOSSIER", zone= lieu_depart_obj.zone).first()
                    if frais_dossier:
                        total += frais_dossier.prix
                        frais_dossier_prix = frais_dossier.prix
                    
                    frais_livraison = FraisLivraison.objects.filter(depart_id=lieu_depart, retour_id=lieu_retour)
                    if frais_livraison :
                        for frais in frais_livraison:
                            total += frais.montant if frais else 0
                    else :
                        trajets = list(FraisLivraison.objects.all().values('depart_id', 'retour_id', 'montant'))
                        chemins_possibles = [(lieu_depart, 0, set())]  # (position, total, lieux_visités)

                        meilleur_cout = None

                        while chemins_possibles:
                            pos, cout, visites = chemins_possibles.pop()
                            visites = visites | {pos}

                            for t in trajets:
                                if t['depart_id'] == pos and t['retour_id'] not in visites:
                                    nouveau_cout = cout + (t['montant'] or 0)
                                    if t['retour_id'] == lieu_retour:
                                        if meilleur_cout is None or nouveau_cout < meilleur_cout:
                                            meilleur_cout = nouveau_cout
                                    else:
                                        chemins_possibles.append((t['retour_id'], nouveau_cout, visites))

                        total += (meilleur_cout or 0)    
                        frais_livraison_prix = (meilleur_cout or 0) 
                    supplements = Supplement.objects.filter(
                        Q(heure_debut__lte=heure_depart, heure_fin__gte=heure_depart) |
                        Q(heure_debut__lte=heure_retour, heure_fin__gte=heure_retour)
                    )
                    for supplement in supplements:
                        total += supplement.montant if supplement else 0
                        supplement_prix += supplement.montant if supplement else 0
                    supplements = Supplement.objects.filter(
                        Q(valeur__gt=0)
                    )
                    for supplement in supplements:
                        start_hour = float(heure_depart[:2]) + float(heure_depart[3:])/60
                        end_hour = float(heure_retour[:2]) + float(heure_retour[3:])/60
                        duration = end_hour - start_hour
                        if duration > supplement.reatrd:
                            total += (prix_unitaire * supplement.valeur) / 100
                            retard_prix = (prix_unitaire * supplement.valeur) / 100
                
                    prix_par_jour = total / total_days if total_days > 0 else 0
                    total_ = get_options_total + total
            return {"modified":"yes","message": "Réservation mise à jour avec succès.", "session_id": "", "payment_url": "payment_url"}
        else:
            return {"modified":"no","message": "Les modifications ne peuvent pas être effectuées : véhicule non disponible."}
    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}
    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}
    

def verify_and_do(ref, lieu_depart, lieu_retour, date_depart, heure_depart, date_retour, heure_retour, backoffice, did_by):
    try:
        verify_value = verify_and_calculate(
            ref,
            lieu_depart,
            lieu_retour,
            date_depart,
            heure_depart,
            date_retour,
            heure_retour,
            None
        )
        if not verify_value[0].get('is_available') or not verify_value[0].get('old_total') or not verify_value[0].get('new_total'):
            return {"success": "no"}

        user = Users.objects.get(id=did_by)

        print("********** ref : ",ref)
        print("********** lieu_depart : ",lieu_depart)
        print("********** lieu_retour : ",lieu_retour)
        print("********** date_depart : ",date_depart)
        print("********** heure_depart : ",heure_depart)
        print("********** date_retour : ",date_retour)
        print("********** heure_retour : ",heure_retour)
        print("********** backoffice : ",backoffice)
        print("********** did_by : ",did_by)

        if verify_value and verify_value[0].get('is_available') == "yes":
            reservation_obj = Reservation.objects.get(name=ref)
            lieu_depart_obj = Lieux.objects.get(id=lieu_depart)
            lieu_retour_obj = Lieux.objects.get(id=lieu_retour)
            date_depart_obj = datetime.strptime(date_depart, "%Y-%m-%d" if '-' in date_depart else "%d/%m/%Y").date()
            heure_depart_obj = datetime.strptime(heure_depart, "%H:%M").time()
            date_retour_obj = datetime.strptime(date_retour, "%Y-%m-%d" if '-' in date_retour else "%d/%m/%Y").date()
            heure_retour_obj = datetime.strptime(heure_retour, "%H:%M").time()
            old_total = verify_value[0].get('old_total') 
            new_total = verify_value[0].get('new_total')
            diff_prix = float(new_total) - float(old_total) if (float(new_total) - float(old_total))>0 else 0
            session_id = None
            payment_url = None
            anciennes_dates = reservation_obj.du_au 
            prolongation_id = None
            retour_avance_id = None

            taux_change = TauxChange.objects.get(id=2)
            taux = taux_change.montant

            if backoffice == "yes":
                if (reservation_obj.date_heure_debut != datetime.combine(date_depart_obj, heure_depart_obj)) or (reservation_obj.date_heure_fin != datetime.combine(date_retour_obj, heure_retour_obj)):
                    nouvelle_date_heure_fin = datetime.combine(date_retour_obj, heure_retour_obj)
                    lvs = Livraison.objects.filter(name=reservation_obj.name)
                    if nouvelle_date_heure_fin > reservation_obj.date_heure_fin:
                        prolongation_obj = Prolongation.objects.create(
                            reservation=reservation_obj,
                            date_heure_debut=datetime.combine(date_depart_obj, heure_depart_obj),
                            date_heure_fin=datetime.combine(date_retour_obj, heure_retour_obj),
                            lieu_depart=lieu_depart_obj,
                            lieu_retour=lieu_retour_obj,
                            total_prolongation= diff_prix,
                            prix_prolongation_devise = diff_prix,
                            date_du_au = anciennes_dates,
                            date_du_au_new = f"{date_depart_obj} {heure_depart} → {date_retour_obj} {heure_retour}",
                            date_prolongation = datetime.now(),
                            effectuer_par = user if user else None 
                        )
                        prolongation_id = prolongation_obj.id
                        reservation_obj.total_prolone = diff_prix if not reservation_obj.total_prolone else float(reservation_obj.total_prolone) + float(diff_prix)
                        reservation_obj.total_reduit_euro = new_total
                        reservation_obj.reste_payer = diff_prix if not reservation_obj.reste_payer else float(reservation_obj.reste_payer) + float(diff_prix)

                    elif nouvelle_date_heure_fin < reservation_obj.date_heure_fin:
                        retour_avance_obj = RetourAvance.objects.create(
                            reservation=reservation_obj,
                            lieu_depart=lieu_depart_obj,
                            lieu_retour=lieu_retour_obj,
                            prix_retour_avance= diff_prix,
                            date_du_au = anciennes_dates,
                            date_du_au_new = f"{date_depart_obj} {heure_depart} → {date_retour_obj} {heure_retour}",
                            date_retour_avance = datetime.now(),
                            effectuer_par = user if user else None
                        )

                        retour_avance_id = retour_avance_obj.id
                        reservation_obj.total_reduit_euro = new_total
                        reservation_obj.reste_payer = diff_prix if not reservation_obj.reste_payer else float(reservation_obj.reste_payer) + float(diff_prix)
                    reservation_obj.du_au_modifier = reservation_obj.du_au
                    reservation_obj.du_au = f"{date_depart_obj} {heure_depart} → {date_retour_obj} {heure_retour}"
                    reservation_obj.date_depart_char = date_depart_obj
                    reservation_obj.date_retour_char = date_retour_obj
                    reservation_obj.heure_depart_char = heure_depart
                    reservation_obj.heure_retour_char = heure_retour
                    reservation_obj.date_heure_debut = datetime.combine(date_depart_obj, heure_depart_obj)
                    reservation_obj.date_heure_fin = datetime.combine(date_retour_obj, heure_retour_obj)

                    for lv in lvs:
                        lv.date_heure_debut = datetime.combine(date_depart_obj, heure_depart_obj)
                        lv.date_heure_fin = datetime.combine(date_retour_obj, heure_retour_obj)
                        lv.total_reduit_euro = diff_prix if not lv.total_reduit_euro else float(lv.total_reduit_euro) + float(diff_prix)
                        lv.total_payer = diff_prix if not lv.total_payer else float(lv.total_payer) + float(diff_prix)
                        lv.total_payer_dz = float(diff_prix) * float(taux) if not lv.total_payer_dz else (float(lv.total_payer_dz) + float(diff_prix)) * float(taux)
                        lv.save()

                if reservation_obj.lieu_depart != lieu_depart_obj or reservation_obj.lieu_retour != lieu_retour_obj :
                    reservation_obj.ancien_lieu = f"{reservation_obj.lieu_depart.name} → {reservation_obj.lieu_retour.name}"
                    reservation_obj.depart_retour = f"{lieu_depart_obj.name} → {lieu_retour_obj.name}"
                    reservation_obj.lieu_depart = lieu_depart_obj
                    reservation_obj.lieu_retour = lieu_retour_obj
                reservation_obj.save()

                sujet = f"Confirmation de votre reservation N°= {reservation_obj.name}"
                expediteur = settings.EMAIL_HOST_USER

                html_message = render_to_string('email/confirmation_email.html', {
                    "referance":reservation_obj.name,
                    "mobile_one":reservation_obj.lieu_depart.mobile,
                    "adresse_one":reservation_obj.lieu_depart.address,
                    "mobile_two":reservation_obj.lieu_retour.mobile,
                    "adresse_two":reservation_obj.lieu_retour.address,
                    'client': reservation_obj.client.nom,
                    'client_prenom':reservation_obj.client.prenom,
                    'durrée':reservation_obj.duree_dereservation,
                    'model_name':reservation_obj.model_name,
                    'reste_paye':reservation_obj.reste_payer,
                    'caution':reservation_obj.opt_protection_caution,
                    "date_depart_char" : reservation_obj.date_depart_char,
                    "date_retour_char" : reservation_obj.date_retour_char,
                    "heure_depart_char" : reservation_obj.heure_depart_char,
                    "heure_retour_char" : reservation_obj.heure_retour_char,
                    'date_depart':date_depart,
                    'heure_depart':heure_depart,
                    'date_retoure':date_retour,
                    'haure_retour':heure_retour,
                    'lieu_depart':reservation_obj.lieu_depart.name,
                    'lieu_depart_id':f"https://api.safarelamir.com/location-description/?lieu_id={reservation_obj.lieu_depart.id}",
                    'lieu_retour':reservation_obj.lieu_retour.name,
                    'lieu_retour_id':f"https://api.safarelamir.com/location-description/?lieu_id={reservation_obj.lieu_retour.id}",

                })

                send_mail(
                    sujet,
                    strip_tags(html_message),  
                    expediteur,
                    [reservation_obj.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                a = {"success": "yes" , 
                    "prolongation_id": prolongation_id,
                    "retour_avance_id":retour_avance_id, 
                    "reservation":reservation_obj.id}
                print("result : ",a)

                return {"success": "yes" , 
                        "prolongation_id": prolongation_id,
                        "retour_avance_id":retour_avance_id, 
                        "reservation":reservation_obj.id}
                
            if float(old_total) == float(new_total) or ((float(old_total) > float(new_total)) and (float(old_total) - float(new_total))<= 150):
                if (reservation_obj.date_heure_debut != datetime.combine(date_depart_obj, heure_depart_obj)) or (reservation_obj.date_heure_fin != datetime.combine(date_retour_obj, heure_retour_obj)):
                    reservation_obj.du_au_modifier = (f"{reservation_obj.date_heure_debut.strftime('%d/%m/%Y %H:%M')} → "
                                                      f"{reservation_obj.date_heure_fin.strftime('%d/%m/%Y %H:%M')}")
                    reservation_obj.date_heure_debut = datetime.combine(date_depart_obj, heure_depart_obj)
                    reservation_obj.date_heure_fin = datetime.combine(date_retour_obj, heure_retour_obj)
                if reservation_obj.lieu_depart != lieu_depart_obj or reservation_obj.lieu_retour != lieu_retour_obj :
                    reservation_obj.ancien_lieu = f"{reservation_obj.lieu_depart.name} → {reservation_obj.lieu_retour.name}"
                    reservation_obj.lieu_depart = lieu_depart_obj
                    reservation_obj.lieu_retour = lieu_retour_obj
                reservation_obj.save()

            elif float(old_total) > float(new_total) and (float(old_total) - float(new_total)) > 150:
                reservation_obj.client.solde += Decimal(float(old_total) - float(new_total))
                reservation_obj.client.solde_total += (float(old_total) - float(new_total))
                if (reservation_obj.date_heure_debut != datetime.combine(date_depart_obj, heure_depart_obj)) or (reservation_obj.date_heure_fin != datetime.combine(date_retour_obj, heure_retour_obj)):
                    reservation_obj.du_au_modifier = (f"{reservation_obj.date_heure_debut.strftime('%d/%m/%Y %H:%M')} → "
                                                      f"{reservation_obj.date_heure_fin.strftime('%d/%m/%Y %H:%M')}")
                    reservation_obj.date_heure_debut = datetime.combine(date_depart_obj, heure_depart_obj)
                    reservation_obj.date_heure_fin = datetime.combine(date_retour_obj, heure_retour_obj)
                if reservation_obj.lieu_depart != lieu_depart_obj or reservation_obj.lieu_retour != lieu_retour_obj :
                    reservation_obj.ancien_lieu = f"{reservation_obj.lieu_depart.name} → {reservation_obj.lieu_retour.name}"
                    reservation_obj.lieu_depart = lieu_depart_obj
                    reservation_obj.lieu_retour = lieu_retour_obj
                reservation_obj.save()
            elif float(old_total) < float(new_total):
                if reservation_obj.opt_payment_name : 
                    
                    if (reservation_obj.date_heure_debut != datetime.combine(date_depart_obj, heure_depart_obj)) or (reservation_obj.date_heure_fin != datetime.combine(date_retour_obj, heure_retour_obj)):
                        reservation_obj.du_au_modifier = (f"{reservation_obj.date_heure_debut.strftime('%d/%m/%Y %H:%M')} → "
                                                        f"{reservation_obj.date_heure_fin.strftime('%d/%m/%Y %H:%M')}")
                        reservation_obj.date_heure_debut = datetime.combine(date_depart_obj, heure_depart_obj)
                        reservation_obj.date_heure_fin = datetime.combine(date_retour_obj, heure_retour_obj)
                    if reservation_obj.lieu_depart != lieu_depart_obj or reservation_obj.lieu_retour != lieu_retour_obj :
                        reservation_obj.ancien_lieu = f"{reservation_obj.lieu_depart.name} → {reservation_obj.lieu_retour.name}"
                        reservation_obj.lieu_depart = lieu_depart_obj
                        reservation_obj.lieu_retour = lieu_retour_obj
                    
                    reservation_obj.total_reduit_euro = new_total
                    reservation_obj.reste_payer = float(old_total) - float(new_total)
                    reservation_obj.save()
                else :
                    request_factory = RequestFactory()
                    fake_request = request_factory.post(
                        path="/create-payment-session-verify-calculate/",
                        data=json.dumps({
                            "product_name": f"Réservation N° : {reservation_obj.name}",
                            "description": f"Réservation du {reservation_obj.model_name} du {date_depart} à {heure_depart} au {date_retour} à {heure_retour}",
                            "images": [reservation_obj.vehicule.modele.photo_link_pay] if reservation_obj.vehicule.modele.photo_link_pay else [],
                            "unit_amount": int((float(new_total) - float(old_total)) * 100),
                            "quantity": 1,
                            "currency": "eur",
                            "reservation_id": reservation_obj.id,
                            "montant_paye":(float(new_total) - float(old_total)),
                            "email": reservation_obj.email,
                            "lieu_depart_id":lieu_depart,
                            "lieu_retour_id":lieu_retour,
                            "date_depart":date_depart,
                            "heure_depart":heure_depart,
                            "date_retour":date_retour,
                            "heure_retour":heure_retour

                        }),
                        content_type="application/json"
                    )
                    payment_session_response = create_payment_session_verify_calculate(fake_request)
                    if payment_session_response.status_code == 200:
                        payment_session_data = json.loads(payment_session_response.content)
                        session_id = payment_session_data.get("session_id", "")
                        payment_url = payment_session_data.get("url", "")
                    else : 
                        session_id = "Lost"
                        payment_url = "Lost"
                        return {"success": "no" ,"session_id": session_id, "payment_url": payment_url}
        
            return {"success": "yes" ,"session_id": session_id, "payment_url": payment_url}
        else : 
            return JsonResponse({"success": "no"}, status=400)

    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}
    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}

@csrf_exempt
def create_payment_session_verify_calculate(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

        data = json.loads(request.body)
        product_name = data.get("product_name")
        description = data.get("description")
        images = data.get("images", [])
        unit_amount = data.get("unit_amount")
        quantity = data.get("quantity")
        currency = data.get("currency", "eur")
        reservation_id = data.get("reservation_id")
        customer_email = data.get("email")
        lieu_depart = data.get("lieu_depart_id")
        lieu_retour = data.get("lieu_retour_id")
        date_depart = data.get("date_depart")
        heure_depart = data.get("heure_depart")
        date_retour = data.get("date_retour")
        heure_retour = data.get("heure_retour")

        if not all([product_name, description, unit_amount, quantity]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        unit_amount = int(unit_amount)
        quantity = int(quantity)

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": product_name,
                            "description": description,
                            "images": images,
                        },
                        "unit_amount": unit_amount,
                    },
                    "quantity": quantity,
                },
            ],
            mode="payment",
            success_url=f"https://safarelamir.com/confirmation/{reservation_id}",
            cancel_url="https://safarelamir.com/cancel",
            customer_email=customer_email,
            metadata={
                "reservation_id": str(reservation_id),
                "montant_paye": str(data.get("montant_paye", 0)),
                "lieu_depart_id":lieu_depart,
                "lieu_retour_id":lieu_retour,
                "date_depart":date_depart,
                "heure_depart":heure_depart,
                "date_retour":date_retour,
                "heure_retour":heure_retour,
                "type":"verify_calculate"
            }
        )


        return JsonResponse({"session_id": checkout_session.id, "url": checkout_session.url}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    
@csrf_exempt
def stripe_webhook_verfy_calculate(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET  

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return JsonResponse({"error": "Invalid payload"}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({"error": "Invalid signature"}, status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        reservation_id = session.get("metadata", {}).get("reservation_id")
        lieu_depart_id = session.get("metadata", {}).get("lieu_depart_id")
        lieu_retour_id = session.get("metadata", {}).get("lieu_retour_id")
        date_depart = session.get("metadata", {}).get("date_depart")
        heure_depart = session.get("metadata", {}).get("heure_depart")
        date_retour = session.get("metadata", {}).get("date_retour")
        heure_retour = session.get("metadata", {}).get("heure_retour")
        montant_paye = session.get("metadata", {}).get("montant_paye")

        reservation_obj = Reservation.objects.get(name=reservation_id)
        lieu_depart_obj = Lieux.objects.get(id=lieu_depart_id)
        lieu_retour_obj = Lieux.objects.get(id=lieu_retour_id)
        date_depart_obj = datetime.strptime(date_depart, "%Y-%m-%d").date()
        heure_depart_obj = datetime.strptime(heure_depart, "%H:%M").time()
        date_retour_obj = datetime.strptime(date_retour, "%Y-%m-%d").date()
        heure_retour_obj = datetime.strptime(heure_retour, "%H:%M").time()


        if (reservation_obj.date_heure_debut != datetime.combine(date_depart_obj, heure_depart_obj)) or (reservation_obj.date_heure_fin != datetime.combine(date_retour_obj, heure_retour_obj)):
            reservation_obj.du_au_modifier = (f"{reservation_obj.date_heure_debut.strftime('%d/%m/%Y %H:%M')} → "
                                                f"{reservation_obj.date_heure_fin.strftime('%d/%m/%Y %H:%M')}")
            reservation_obj.date_heure_debut = datetime.combine(date_depart_obj, heure_depart_obj)
            reservation_obj.date_heure_fin = datetime.combine(date_retour_obj, heure_retour_obj)
        if reservation_obj.lieu_depart != lieu_depart_obj or reservation_obj.lieu_retour != lieu_retour_obj :
            reservation_obj.ancien_lieu = f"{reservation_obj.lieu_depart.name} → {reservation_obj.lieu_retour.name}"
            reservation_obj.lieu_depart = lieu_depart_obj
            reservation_obj.lieu_retour = lieu_retour_obj
        reservation_obj.save()
        
        print(f"Paiement réussi pour la réservation ID: {reservation_id}")

    return JsonResponse({"status": "success"}, status=200)

def verify_and_do_view(request):
    ref = request.GET.get("ref")
    lieu_depart = request.GET.get("lieu_depart")
    lieu_retour = request.GET.get("lieu_retour")
    date_depart = request.GET.get("date_depart")
    heure_depart = request.GET.get("heure_depart")
    date_retour = request.GET.get("date_retour")
    heure_retour = request.GET.get("heure_retour")
    backoffice = request.GET.get("backoffice")
    did_by = request.GET.get("did_by")
    country_code = request.headers.get("X-Country-Code")

    if not date_retour or not date_depart or not lieu_depart or not lieu_retour or not heure_depart or not heure_retour:
        return JsonResponse({"error": "Tous les paramètres sont requis."}, status=400)

    try:
        resultats = verify_and_do(
            ref=ref,
            lieu_depart = lieu_depart,
            lieu_retour = lieu_retour,
            date_depart = date_depart,
            heure_depart = heure_depart,
            date_retour = date_retour,
            heure_retour = heure_retour,
            backoffice = backoffice,
            did_by = did_by
        )
        print("********** ref : ",ref)
        print("********** lieu_depart : ",lieu_depart)
        print("********** lieu_retour : ",lieu_retour)
        print("********** date_depart : ",date_depart)
        print("********** heure_depart : ",heure_depart)
        print("********** date_retour : ",date_retour)
        print("********** heure_retour : ",heure_retour)
        print("********** backoffice : ",backoffice)
        print("********** did_by : ",did_by)
        if resultats.get('success') == "yes":
            return JsonResponse({"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
        else :
            return JsonResponse({"results": resultats}, status=400, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})


def verify_client_view(request):
    email = request.GET.get("email")
    nom = request.GET.get("nom")
    prenom = request.GET.get("prenom")
    birthday = request.GET.get("birthday")
    permis = request.GET.get("permis")
    phone = request.GET.get("phone")
    nom_nd = request.GET.get("nom_nd")
    prenom_nd = request.GET.get("prenom_nd")
    birthday_nd = request.GET.get("birthday_nd")
    permis_nd = request.GET.get("permis_nd")

    if not nom or not prenom:
        return JsonResponse({"error": "Les paramètres 'nom' et 'prenom' sont requis."}, status=400)

    try:
        if not nom_nd :
            resultats = verify_client(
                email = email,
                nom = nom,
                prenom = prenom,
                birthday = birthday,
                permis = permis,
                phone =  phone,
            )
            return JsonResponse({"client_id": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
        if nom_nd :
            resultats = verify_client(
                email = email,
                nom = nom,
                prenom = prenom,
                birthday = birthday,
                permis = permis,
                phone =  phone,
            )
            resultats_nd = verify_client(
                email = email,
                nom = nom_nd,
                prenom = prenom_nd,
                birthday = birthday_nd,
                permis = permis_nd,
                phone = phone
            )
            return JsonResponse({"client_id": resultats, "nd_client_id":resultats_nd}, status=200, json_dumps_params={"ensure_ascii": False})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})

def country_code_to_emoji(country_code):
    if not country_code:
        return None
    country_code = country_code.upper()
    try:
        return ''.join(chr(127397 + ord(c)) for c in country_code)
    except:
        return None

@csrf_exempt
@require_http_methods(["POST"])
def add_reservation_post_view(request):
    try:

        data = json.loads(request.body)
        lieu_depart = data.get("lieu_depart")
        lieu_retour = data.get("lieu_retour")
        date_depart = data.get("date_depart")
        heure_depart = data.get("heure_depart")
        date_retour = data.get("date_retour")
        heure_retour = data.get("heure_retour")
        vehicule_id = data.get("vehicule_id")
        opt_paiement = data.get("opt_paiement")
        opt_klm = data.get("opt_klm")
        opt_protection = data.get("opt_protection")
        opt_nd_driver = data.get("opt_nd_driver")
        opt_carburant = data.get("opt_carburant")
        opt_sb_a = data.get("opt_sb_a")
        opt_sb_b = data.get("opt_sb_b")
        opt_sb_c = data.get("opt_sb_c")
        client_id = data.get("client_id")
        nd_driver_id = data.get("nd_driver_id")
        num_vol = data.get("num_vol")
        token = data.get("token")
        ccountry_code = request.META.get("HTTP_X_COUNTRY_CODE")
        pays_drapeau = country_code_to_emoji(ccountry_code)
        prix_jour = 0
        total = 0
        last_total = 0
        prix_unitaire = 0
        last_prix_unitaire = 0
        supp_total = 0 
        to_pay = 0
        ecart_montant = 0
        total_afficher_red = 0
        total_option = 0
        promo_value = 0
        client_solde = 0

        lieu_depart_obj = Lieux.objects.filter(id=lieu_depart).first()

        if not all([date_depart, heure_depart, date_retour, heure_retour]):
            return JsonResponse({"error": "les dates et les heures doivent être remplis."}, status=400)
        
        date_heure_debut = parse_datetime(f"{date_depart}T{heure_depart}")
        date_heure_fin = parse_datetime(f"{date_retour}T{heure_retour}")
        date_depart_obj = datetime.strptime(date_depart, "%Y-%m-%d").date()
        date_retour_obj = datetime.strptime(date_retour, "%Y-%m-%d").date()
        total_days = (date_retour_obj - date_depart_obj).days
        duree = f"{total_days} jours"
        if date_heure_debut and date_heure_fin:
            date_heure_debut_formate = date_heure_debut.strftime("%d/%m/%Y %H:%M")
            date_heure_fin_formate = date_heure_fin.strftime("%d/%m/%Y %H:%M")
            date_debut_char = date_heure_debut.strftime("%d/%m/%Y")
            date_fin_char = date_heure_fin.strftime("%d/%m/%Y")
            heure_debut_char = date_heure_debut.strftime("%H:%M")
            heure_fi_char = date_heure_fin.strftime("%H:%M")
            du_au_string = f"{date_heure_debut_formate} → {date_heure_fin_formate}"
        else :
            return JsonResponse({"error": "Les dates ou heures fournies sont invalides."}, status=400)

        if client_id :
            client = ListeClient.objects.filter(id=client_id).first()
            if client :
                client_solde = Decimal(client.solde) if client.solde else 0
                client_red_pr = client.categorie_client.reduction if client.categorie_client.reduction and client.categorie_client is not None else 0
            else :
                return JsonResponse({"error": "client non trouver."}, status=400)
        else:
            return JsonResponse({"error": "client non fournis."}, status=400)
            
        if lieu_depart and lieu_retour:
            depart = Lieux.objects.filter(id=lieu_depart).first()
            retour = Lieux.objects.filter(id=lieu_retour).first()
            depart_retour_string = f"{depart.name} → {retour.name}"

        
        if vehicule_id :
            vehicule = Vehicule.objects.filter(id=vehicule_id).first()
            date_heure_debut_av = datetime.strptime(f"{date_depart} {heure_depart}", "%Y-%m-%d %H:%M")
            date_heure_fin_av = datetime.strptime(f"{date_retour} {heure_retour}", "%Y-%m-%d %H:%M")
            reservations_existantes = Reservation.objects.filter(
                vehicule=vehicule,
                date_heure_debut__lt=date_heure_fin_av, 
                date_heure_fin__gt=date_heure_debut_av,
                status="confirmee" 
            )

            if reservations_existantes:
                return JsonResponse({"error": "Le véhicule est déjà réservé ou loué pour cette période."}, status=400)
            promotions = Promotion.objects.filter(
                date_debut__lte=date_depart,
                date_fin__gte=date_retour,
                active_passive=True
            ).first()

            if promotions and promotions.tout_modele == "oui" and promotions.tout_zone == "oui":
                promo_value = promotions.reduction
            elif promotions and promotions.tout_modele == "oui" and promotions.tout_zone == "non":
                if lieu_depart_obj.zone == promotions.zone_one or lieu_depart_obj.zone == promotions.zone_one or lieu_depart_obj.zone == promotions.zone_one :
                    promo_value = promotions.reduction
                else :
                    promo_value = 0
            elif promotions and (promotions.tout_modele == "non" or promotions.tout_modele == "aleatoire") and promotions.tout_zone == "oui":
                if promotions.model_one == vehicule.modele:
                    model_one = promotions.model_one
                    promo_value = promotions.reduction
                else :
                    model_one = None
                if promotions.model_two == vehicule.modele:
                    model_two = promotions.model_two
                    promo_value = promotions.reduction
                else :
                    model_two = None
                if promotions.model_three == vehicule.modele:
                    model_three = promotions.model_three
                    promo_value = promotions.reduction
                else :
                    model_three = None
                if promotions.model_four == vehicule.modele:
                    model_four = promotions.model_four
                    promo_value = promotions.reduction
                else :
                    model_four = None
                if promotions.model_five == vehicule.modele:
                    model_five = promotions.model_five
                    promo_value = promotions.reduction
                else :
                    model_five = None
            elif promotions and (promotions.tout_modele == "non" or promotions.tout_modele == "aleatoire") and promotions.tout_zone == "non":
                if lieu_depart_obj.zone == promotions.zone_one :
                    if promotions.model_one == vehicule.modele:
                        model_one = promotions.model_one
                        promo_value = promotions.reduction
                    else :
                        model_one = None
                    if promotions.model_two == vehicule.modele:
                        model_two = promotions.model_two
                        promo_value = promotions.reduction
                    else :
                        model_two = None
                    if promotions.model_three == vehicule.modele:
                        model_three = promotions.model_three
                        promo_value = promotions.reduction
                    else :
                        model_three = None
                    if promotions.model_four == vehicule.modele:
                        model_four = promotions.model_four
                        promo_value = promotions.reduction
                    else :
                        model_four = None
                    if promotions.model_five == vehicule.modele:
                        model_five = promotions.model_five
                        promo_value = promotions.reduction
                    else :
                        model_five = None
                elif lieu_depart_obj.zone == promotions.zone_two :
                    if promotions.model_one == vehicule.modele:
                        model_one = promotions.model_one
                        promo_value = promotions.reduction
                    else :
                        model_one = None
                    if promotions.model_two == vehicule.modele:
                        model_two = promotions.model_two
                        promo_value = promotions.reduction
                    else :
                        model_two = None
                    if promotions.model_three == vehicule.modele:
                        model_three = promotions.model_three
                        promo_value = promotions.reduction
                    else :
                        model_three = None
                    if promotions.model_four == vehicule.modele:
                        model_four = promotions.model_four
                        promo_value = promotions.reduction
                    else :
                        model_four = None
                    if promotions.model_five == vehicule.modele:
                        model_five = promotions.model_five
                        promo_value = promotions.reduction
                    else :
                        model_five = None
                elif lieu_depart_obj.zone == promotions.zone_three :
                    if promotions.model_one == vehicule.modele:
                        model_one = promotions.model_one
                        promo_value = promotions.reduction
                    else :
                        model_one = None
                    if promotions.model_two == vehicule.modele:
                        model_two = promotions.model_two
                        promo_value = promotions.reduction
                    else :
                        model_two = None
                    if promotions.model_three == vehicule.modele:
                        model_three = promotions.model_three
                        promo_value = promotions.reduction
                    else :
                        model_three = None
                    if promotions.model_four == vehicule.modele:
                        model_four = promotions.model_four
                        promo_value = promotions.reduction
                    else :
                        model_four = None
                    if promotions.model_five == vehicule.modele:
                        model_five = promotions.model_five
                        promo_value = promotions.reduction
                    else :
                        model_five = None
                else :
                    promo_value = 0
            else:
                promo_value = 0
                
            tarif = Tarifs.objects.filter(
               ( Q(date_depart_one__lte=date_depart, date_fin_one__gte=date_retour) |
                Q(date_depart_two__lte=date_depart, date_fin_two__gte=date_retour) |
                Q(date_depart_three__lte=date_depart, date_fin_three__gte=date_retour) |
                Q(date_depart_four__lte=date_depart, date_fin_four__gte=date_retour)),
                Q(nbr_de__lte=total_days, nbr_au__gte=total_days),
                modele=vehicule.modele,
                zone=depart.zone 
            ).first()

            if tarif :
                prix_jour = tarif.prix
                total += prix_jour * total_days
                if client_red_pr and client_red_pr > 0 and client_red_pr > promo_value:
                    last_total = (100-client_red_pr) * total / 100
                elif promo_value > client_red_pr:
                    last_total = Decimal((100-promo_value) * total / 100)
                else : 
                    last_total = total
                if client_solde > 0:
                    last_total = total - client_solde
                    client.solde_consomer = client.solde_consomer or 0
                    client.solde_total = client.solde_total or 0
                    client.solde = 0.00
                    client.solde_consomer += client_solde if client_solde else 0
                    client.solde_total += client_solde if client_solde else 0
                    client.save()
            else:
                return JsonResponse({"error": "tarifs invalides."}, status=400)
        else:
            return JsonResponse({"error": "vehucule invalides."}, status=400)
        last_total = Decimal(last_total)
        frais_dossier = Options.objects.filter(option_code="FRAIS_DOSSIER", zone= lieu_depart_obj.zone).first()
        if frais_dossier:
            total += Decimal(frais_dossier.prix) * total_days if frais_dossier.type_option == "jour" else Decimal(frais_dossier.prix)
            last_total += Decimal(frais_dossier.prix) * total_days if frais_dossier.type_option == "jour" else Decimal(frais_dossier.prix)
        frais_liv = 0
        frais_livraison = FraisLivraison.objects.filter(depart_id=lieu_depart, retour_id=lieu_retour)
        if frais_livraison :
            for frais in frais_livraison:
                total += Decimal(frais.montant) if frais else 0
                last_total += Decimal(frais.montant) if frais else 0
                frais_liv += Decimal(frais.montant) if frais else 0
        else :
            lieu_depart = int(lieu_depart)
            lieu_retour = int(lieu_retour)
            trajets = list(FraisLivraison.objects.all().values('depart_id', 'retour_id', 'montant'))
            chemins_possibles = [(lieu_depart, 0, set())]  # (position, total, lieux_visités)

            meilleur_cout = None

            while chemins_possibles:
                pos, cout, visites = chemins_possibles.pop()
                visites = visites | {pos}

                for t in trajets:
                    if t['depart_id'] == pos and t['retour_id'] not in visites:
                        nouveau_cout = cout + (t['montant'] or 0)
                        if t['retour_id'] == lieu_retour:
                            if meilleur_cout is None or nouveau_cout < meilleur_cout:
                                meilleur_cout = nouveau_cout
                        else:
                            chemins_possibles.append((t['retour_id'], nouveau_cout, visites))
           
            total += Decimal((meilleur_cout or 0)) 
            last_total += Decimal((meilleur_cout or 0)) 
            frais_liv += Decimal((meilleur_cout or 0))  
        
        supplements = Supplement.objects.filter(
            Q(heure_debut__lte=heure_depart, heure_fin__gte=heure_depart) |
            Q(heure_debut__lte=heure_retour, heure_fin__gte=heure_retour)
        )
        for supplement in supplements:
            supp_total += supplement.montant
            total += supplement.montant if supplement else 0
            last_total += supplement.montant if supplement else 0
        
        ecart = Supplement.objects.filter(valeur__gt=0).first()
        start_hour = float(heure_depart[:2]) + float(heure_depart[3:])/60
        end_hour = float(heure_retour[:2]) + float(heure_retour[3:])/60
        duration = end_hour - start_hour
        
        if duration > ecart.reatrd:
            ecart_montant = (prix_jour * ecart.valeur) / 100
            total+= Decimal(ecart_montant)
            last_total+= Decimal(ecart_montant)
        prix_unitaire = total / total_days
        total_afficher = total
        total_afficher_red = last_total
        last_prix_unitaire = last_total / total_days
        free_options = free_options_f(client_id=client_id)
       
        if opt_paiement == "yes" :
            if free_options and free_options[0].get("option_six") == True:
                paiement_anticipe = Options.objects.filter(option_code="P_ANTICIPE", zone= lieu_depart_obj.zone).first()
                opt_payment_name = paiement_anticipe.name
                opt_payment_unit = 0
                opt_payment_total = 0
                to_pay = prix_jour
                total_option += opt_payment_total
                total += opt_payment_total
                last_total += opt_payment_total
            else:
                paiement_anticipe = Options.objects.filter(option_code="P_ANTICIPE", zone= lieu_depart_obj.zone).first()
                opt_payment_name = paiement_anticipe.name
                opt_payment_unit = float(paiement_anticipe.prix) if paiement_anticipe.prix else 0.0
                opt_payment_total = Decimal(paiement_anticipe.prix) * total_days if paiement_anticipe.type_option =="jour" else Decimal(paiement_anticipe.prix)
                to_pay = prix_jour
                total_option += opt_payment_total
                total += opt_payment_total
                last_total += opt_payment_total
        else :
            to_pay = 0
            paiement_anticipe = None
            opt_payment_name = None
            opt_payment_unit = 0
            opt_payment_total = 0
        

        klm_illimite_b = None
        klm_a_illimite = None
        klm_illimite_c = None
        
        if opt_klm == "yes" :
            
            if free_options and free_options[0].get("option_seven") == True:
                klm_a_illimite = Options.objects.filter(option_code="KLM_ILLIMITED", zone= lieu_depart_obj.zone).first()
                opt_klm_a_name = klm_a_illimite.name
                opt_klm_a_unit = 0
                opt_klm_a_total = 0
                opt_klm_a_categorie = klm_a_illimite.categorie.id
            else :
                klm_a_illimite = Options.objects.filter(option_code="KLM_ILLIMITED", zone= lieu_depart_obj.zone).first()
                opt_klm_a_name = klm_a_illimite.name
                opt_klm_a_unit = float(klm_a_illimite.prix) if klm_a_illimite.prix else 0.0
                opt_klm_a_total = klm_a_illimite.prix * total_days if klm_a_illimite.type_tarif == "jour" else klm_a_illimite.prix
                opt_klm_a_categorie = klm_a_illimite.categorie.id

            if free_options and free_options[0].get("option_seven") == True:
                klm_illimite_b = Options.objects.filter(option_code="KLM_ILLIMITED_B", zone= lieu_depart_obj.zone).first()
                opt_klm_b_name = klm_illimite_b.name
                opt_klm_b_unit = 0
                opt_klm_b_total = 0
                opt_klm_b_categorie = klm_illimite_b.categorie.id
            else :
                klm_illimite_b = Options.objects.filter(option_code="KLM_ILLIMITED_B", zone= lieu_depart_obj.zone).first()
                opt_klm_b_name = klm_illimite_b.name
                opt_klm_b_unit = float(klm_illimite_b.prix) if klm_illimite_b.prix else 0.0
                opt_klm_b_total = klm_illimite_b.prix * total_days if klm_illimite_b.type_tarif == "jour" else klm_illimite_b.prix
                opt_klm_b_categorie = klm_illimite_b.categorie.id
            
            if free_options and free_options[0].get("option_seven") == True:
                klm_illimite_c = Options.objects.filter(option_code="KLM_ILLIMITED_C", zone= lieu_depart_obj.zone).first()
                opt_klm_c_name = klm_illimite_c.name
                opt_klm_c_unit = 0
                opt_klm_c_total = 0
                opt_klm_c_categorie = klm_illimite_c.categorie.id
            else :
                klm_illimite_c = Options.objects.filter(option_code="KLM_ILLIMITED_C", zone= lieu_depart_obj.zone).first()
                opt_klm_c_name = klm_illimite_c.name
                opt_klm_c_unit = float(klm_illimite_c.prix) if klm_illimite_c.prix else 0.0
                opt_klm_c_total = klm_illimite_c.prix * total_days if klm_illimite_c.type_tarif == "jour" else klm_illimite_c.prix
                opt_klm_c_categorie = klm_illimite_c.categorie.id

            if vehicule.categorie.id == opt_klm_a_categorie :
                opt_klm = klm_a_illimite
                opt_klm_name = opt_klm_a_name
                opt_klm_unit = opt_klm_a_unit
                opt_klm_total = opt_klm_a_total
            elif vehicule.categorie.id == opt_klm_b_categorie :
                opt_klm = klm_illimite_b
                opt_klm_name = opt_klm_b_name
                opt_klm_unit = opt_klm_b_unit
                opt_klm_total = opt_klm_b_total
            elif vehicule.categorie.id == opt_klm_c_categorie :
                opt_klm = klm_illimite_c
                opt_klm_name = opt_klm_c_name
                opt_klm_unit = opt_klm_c_unit
                opt_klm_total = opt_klm_c_total
            else :
                opt_klm = None
                opt_klm_name = None
                opt_klm_unit = 0
                opt_klm_total = 0
            
            total += opt_klm_total
            last_total += opt_klm_total
            total_option += opt_klm_total

        else :
            opt_klm = None
            opt_klm_name = None
            opt_klm_unit = 0
            opt_klm_total = 0
        
        if opt_protection == "BASE" :
            base_a = Options.objects.filter(option_code="BASE_P_1", zone= lieu_depart_obj.zone).first()
            base_a_name = base_a.name
            base_a_unit = float(base_a.prix) if base_a.prix else 0.0
            base_a_total = Decimal(base_a.prix) * total_days if base_a.type_tarif == "jour" else Decimal(base_a.prix)
            base_a_category = base_a.categorie.id
            base_a_caution = base_a.caution
            base_b = Options.objects.filter(option_code="BASE_P_2", zone= lieu_depart_obj.zone).first()
            base_b_name = base_b.name
            base_b_unit = float(base_b.prix) if base_b.prix else 0.0
            base_b_total = Decimal(base_b.prix) * total_days if base_b.type_tarif == "jour" else Decimal(base_b.prix)
            base_b_category = base_b.categorie.id
            base_b_caution = base_b.caution
            base_c = Options.objects.filter(option_code="BASE_P_3", zone= lieu_depart_obj.zone).first()
            base_c_name = base_c.name
            base_c_unit = float(base_c.prix) if base_c.prix else 0.0
            base_c_total = Decimal(base_c.prix) * total_days if base_c.type_tarif == "jour" else Decimal(base_c.prix)
            base_c_category = base_c.categorie.id
            base_c_caution = base_c.caution

            if vehicule.categorie.id == base_a_category :
                protection = base_a
                protection_name = base_a_name
                protection_unit = base_a_unit
                protection_total = base_a_total
                protection_caution = base_a_caution
            elif vehicule.categorie.id == base_b_category :
                protection = base_b
                protection_name = base_b_name
                protection_unit = base_b_unit
                protection_total = base_b_total
                protection_caution = base_b_caution
            elif vehicule.categorie.id == base_c_category :
                protection = base_c
                protection_name = base_c_name
                protection_unit = base_c_unit
                protection_total = base_c_total
                protection_caution = base_c_caution
            else :
                protection = None
                protection_name = None
                protection_unit = 0
                protection_total = 0
                protection_caution = 0

            total += protection_total
            last_total += protection_total
            total_option += protection_total
        
        elif opt_protection == "STANDART" :
            standart_a = Options.objects.filter(option_code="STANDART_P_1", zone= lieu_depart_obj.zone).first()
            standart_a_name = standart_a.name
            standart_a_unit = float(standart_a.prix) if standart_a.prix else 0.0
            standart_a_total = Decimal(standart_a.prix) * total_days if standart_a.type_tarif == "jour" else Decimal(standart_a.prix)
            standart_a_caution = standart_a.caution

            standart_b = Options.objects.filter(option_code="STANDART_P_2", zone= lieu_depart_obj.zone).first()
            standart_b_name = standart_b.name
            standart_b_unit = float(standart_b.prix) if standart_b.prix else 0.0
            standart_b_total = Decimal(standart_b.prix) * total_days if standart_b.type_tarif == "jour" else Decimal(standart_b.prix)
            standart_b_caution = standart_b.caution
            
            standart_c = Options.objects.filter(option_code="STANDART_P_3", zone= lieu_depart_obj.zone).first()
            standart_c_name = standart_c.name
            standart_c_unit = float(standart_c.prix) if standart_c.prix else 0.0
            standart_c_total = Decimal(standart_c.prix) * total_days if standart_c.type_tarif == "jour" else Decimal(standart_c.prix)
            standart_c_caution = standart_c.caution
            if vehicule.categorie == standart_a.categorie :
                protection = standart_a
                protection_name = standart_a_name
                protection_unit = standart_a_unit
                protection_total = standart_a_total
                protection_caution = standart_a_caution
            elif vehicule.categorie == standart_b.categorie :
                protection = standart_b
                protection_name = standart_b_name
                protection_unit = standart_b_unit
                protection_total = standart_b_total
                protection_caution = standart_b_caution
            elif vehicule.categorie == standart_c.categorie :
                protection = standart_c
                protection_name = standart_c_name
                protection_unit = standart_c_unit
                protection_total = standart_c_total
                protection_caution = standart_c_caution
            else :
                protection = None
                protection_name = None
                protection_unit = 0
                protection_total = 0
                protection_caution = 0
            total += protection_total
            last_total += protection_total
            total_option += protection_total

        elif opt_protection == "MAX" :
            if free_options and free_options[0].get("option_eight") == True:
                max_a = Options.objects.filter(option_code="MAX_P_1", zone= lieu_depart_obj.zone).first()
                max_a_name = max_a.name
                max_a_unit = 0
                max_a_total = 0
                max_a_caution = max_a.caution
            else : 
                max_a = Options.objects.filter(option_code="MAX_P_1", zone= lieu_depart_obj.zone).first()
                max_a_name = max_a.name
                if max_a.type_tarif == "jour" :
                    max_a_total = Decimal(max_a.prix * total_days) if max_a.min_prix < max_a.prix * total_days else Decimal(max_a.min_prix)
                else :
                    max_a_total = Decimal(max_a.prix)  if max_a.min_prix < max_a.prix * total_days else Decimal(max_a.min_prix)
                max_a_unit = float(max_a_total / total_days)
                max_a_caution = max_a.caution
            
            if free_options and free_options[0].get("option_eight") == True:
                max_b = Options.objects.filter(option_code="MAX_P_2", zone= lieu_depart_obj.zone).first()
                max_b_name = max_b.name
                max_b_unit = 0
                max_b_total = 0
                max_b_caution = max_b.caution
            else :
                max_b = Options.objects.filter(option_code="MAX_P_2", zone= lieu_depart_obj.zone).first()
                max_b_name = max_b.name
                
                max_b_unit = float(max_b.prix)
                max_b_total = Decimal(max_b.prix) * total_days if max_b.type_tarif == "jour" else Decimal(max_b.prix)
                max_b_caution = max_b.caution

            if free_options and free_options[0].get("option_eight") == True:
                max_c = Options.objects.filter(option_code="MAX_P_3", zone= lieu_depart_obj.zone).first()
                max_c_name = max_c.name
                max_c_unit = 0
                max_c_total = 0
                max_c_caution = max_c.caution
            else :
                max_c = Options.objects.filter(option_code="MAX_P_3", zone= lieu_depart_obj.zone).first()
                max_c_name = max_c.name
                max_c_unit = float(max_c.prix)
                max_c_total = Decimal(max_c.prix) * total_days if max_c.type_tarif == "jour" else Decimal(max_c.prix)
                max_c_caution = max_c.caution
            
            if vehicule.categorie == max_a.categorie :
                protection = max_a
                protection_name = max_a_name
                protection_unit = max_a_unit
                protection_total = max_a_total
                protection_caution = max_a_caution
            elif vehicule.categorie == max_b.categorie :
                protection = max_b
                protection_name = max_b_name
                protection_unit = max_b_unit
                protection_total = max_b_total
                protection_caution = max_b_caution
            elif vehicule.categorie == max_c.categorie :
                protection = max_c
                protection_name = max_c_name
                protection_unit = max_c_unit
                protection_total = max_c_total
                protection_caution = max_c_caution
            else :
                protection = None
                protection_name = None
                protection_unit = 0
                protection_total = 0
                protection_caution = 0
            total += protection_total
            last_total += protection_total
            total_option += protection_total

        else :
            protection = None
            protection_name = None
            protection_unit = 0
            protection_total = 0
            protection_caution = 0
        
        if opt_carburant == "yes":
            if free_options and free_options[0].get("option_two") == True:
                carburant = Options.objects.filter(option_code="P_CARBURANT", zone= lieu_depart_obj.zone).first()
                carburant_name = carburant.name
                carburant_unit = 0
                carburant_total = 0
                total += carburant_total
                last_total += carburant_total
                total_option += carburant_total
            else:
                carburant = Options.objects.filter(option_code="P_CARBURANT", zone= lieu_depart_obj.zone).first()
                carburant_name = carburant.name
                carburant_unit = float(carburant.prix) if carburant.prix else 0.0
                carburant_total = Decimal(carburant.prix) * total_days if carburant.type_tarif == "jour" else Decimal(carburant.prix)
                total += carburant_total
                last_total += carburant_total
                total_option += carburant_total
        else :
            carburant = None
            carburant_name = None
            carburant_unit = 0
            carburant_total = 0
        
        if opt_sb_a == "yes":
            if free_options and free_options[0].get("option_three") == True:
                sb_a = Options.objects.filter(option_code="S_BEBE_5", zone= lieu_depart_obj.zone).first()
                sb_a_name = sb_a.name
                sb_a_unit = 0
                sb_a_total = 0
                total += sb_a_total
                last_total += sb_a_total
                total_option += sb_a_total
            else :
                sb_a = Options.objects.filter(option_code="S_BEBE_5", zone= lieu_depart_obj.zone).first()
                sb_a_name = sb_a.name
                sb_a_unit = float(sb_a.prix) if sb_a.prix else 0.0
                sb_a_total = Decimal(sb_a.prix) * total_days if sb_a.type_tarif == "jour" else Decimal(sb_a.prix)
                total += sb_a_total
                last_total += sb_a_total
                total_option += sb_a_total 
        else :
            sb_a = None
            sb_a_name = None
            sb_a_unit = 0
            sb_a_total = 0
        
        if opt_sb_b == "yes":
            if free_options and free_options[0].get("option_four") == True:
                sb_b = Options.objects.filter(option_code="S_BEBE_13", zone= lieu_depart_obj.zone).first()
                sb_b_name = sb_b.name
                sb_b_unit = 0
                sb_b_total = 0
                total += sb_b_total 
                last_total += sb_b_total
                total_option += sb_b_total
            else:
                sb_b = Options.objects.filter(option_code="S_BEBE_13", zone= lieu_depart_obj.zone).first()
                sb_b_name = sb_b.name
                sb_b_unit = float(sb_b.prix) if sb_b.prix else 0.0
                sb_b_total = Decimal(sb_b.prix) * total_days if sb_b.type_tarif == "jour" else Decimal(sb_b.prix)
                total += sb_b_total 
                last_total += sb_b_total
                total_option += sb_b_total

        else :
            sb_b = None
            sb_b_name = None
            sb_b_unit = 0
            sb_b_total = 0
        
        if opt_sb_c == "yes":
            if free_options and free_options[0].get("option_five") == True:
                sb_c = Options.objects.filter(option_code="S_BEBE_18", zone= lieu_depart_obj.zone).first()
                sb_c_name = sb_c.name
                sb_c_unit = 0
                sb_c_total = 0
                total += sb_c_total
                last_total += sb_c_total
                total_option += sb_c_total
            else:
                sb_c = Options.objects.filter(option_code="S_BEBE_18", zone= lieu_depart_obj.zone).first()
                sb_c_name = sb_c.name
                sb_c_unit = float(sb_c.prix) if sb_c.prix else 0.0
                sb_c_total = Decimal(sb_c.prix) * total_days if sb_c.type_tarif == "jour" else Decimal(sb_c.prix)
                total += sb_c_total
                last_total += sb_c_total
                total_option += sb_c_total
        else :
            sb_c = None
            sb_c_name = None
            sb_c_unit = 0
            sb_c_total = 0
        
        if opt_nd_driver == "yes":
            if nd_driver_id :
                
                nd_driver = ListeClient.objects.filter(id=nd_driver_id).first()
                nd_driver_name = nd_driver.name
                nd_driver_date_permis = nd_driver.date_de_permis
                nd_driver_birthday = nd_driver.date_de_naissance
                nd_driver_phone = nd_driver.telephone
                nd_driver_email = nd_driver.email
                nd_driver_risque = nd_driver.risque
                nd_driver_prime = nd_driver.code_prime
                nd_driver_category = nd_driver.categorie_client
                nd_driver_solde = nd_driver.solde

                if free_options and free_options[0].get("option_one") == True:
                    nd_driver_opt = Options.objects.filter(option_code="ND_DRIVER", zone= lieu_depart_obj.zone).first()
                    nd_driver_opt_name = nd_driver_opt.name
                    nd_driver_opt_unit = 0
                    nd_driver_opt_total = 0
                    total += nd_driver_opt_total
                    last_total += nd_driver_opt_total
                    total_option += nd_driver_opt_total
                else:
                    nd_driver_opt = Options.objects.filter(option_code="ND_DRIVER", zone= lieu_depart_obj.zone).first()
                    nd_driver_opt_name = nd_driver_opt.name
                    nd_driver_opt_unit = float(nd_driver_opt.prix) if nd_driver_opt.prix else 0.0
                    nd_driver_opt_total = Decimal(nd_driver_opt.prix) * total_days if nd_driver_opt.type_tarif == "jour" else nd_driver_opt.prix
                    total += nd_driver_opt_total
                    last_total += nd_driver_opt_total
                    total_option += nd_driver_opt_total
            else :
                return JsonResponse({"error": "nd client invalides."}, status=400)
        else :
            nd_driver = None
            nd_driver_name = None
            nd_driver_date_permis = None
            nd_driver_birthday = None
            nd_driver_phone = None
            nd_driver_email = None
            nd_driver_risque = None
            nd_driver_prime = None
            nd_driver_category = None
            nd_driver_solde = 0
            nd_driver_opt = None
            nd_driver_opt_name = None
            nd_driver_opt_unit = 0
            nd_driver_opt_total = 0

        taux_change = TauxChange.objects.get(id=2)
        change = taux_change.montant
        
        reservation = Reservation.objects.create(
            create_date=timezone.now(),
            status="en_attend",
            etat_reservation="reserve",
            date_heure_debut = date_heure_debut ,
            date_heure_fin = date_heure_fin,
            date_depart_char = date_debut_char,
            date_retour_char = date_fin_char,
            heure_depart_char = heure_debut_char,
            heure_retour_char = heure_fi_char,
            du_au = du_au_string,
            nbr_jour_reservation = total_days,
            duree_dereservation = duree,
            lieu_depart = depart,
            zone = depart.zone,
            address_fr = depart.address,
            address_en = depart.address_en,
            address_ar = depart.address_ar,
            lieu_retour = retour,
            depart_retour = depart_retour_string,
            vehicule = vehicule,
            modele = vehicule.modele,
            categorie = vehicule.categorie,
            carburant = vehicule.carburant,
            matricule = vehicule.matricule,
            numero = vehicule.numero,
            model_name = vehicule.model_name,
            marketing_text_fr = vehicule.marketing_text_fr,
            photo_link_nd = vehicule.photo_link_nd,
            photo_link = vehicule.photo_link,
            nombre_deplace = vehicule.nombre_deplace,
            nombre_de_porte = vehicule.nombre_de_porte,
            nombre_de_bagage = vehicule.nombre_de_bagage,
            boite_vitesse = vehicule.boite_vitesse,
            age_min = vehicule.age_min,
            client = client,
            client_create_date = client.create_date if client.create_date is not None else None,
            nom = client.nom,
            prenom = client.prenom,
            email = client.email,
            date_de_naissance = client.date_de_naissance,
            mobile = client.mobile,
            telephone = client.telephone,
            risque = client.risque,
            note = client.note,
            categorie_client = client.categorie_client,
            code_prime = client.code_prime,
            solde = client.solde,
            nom_nd_condicteur = nd_driver.nom if nd_driver else None,
            prenom_nd_condicteur = nd_driver.prenom if nd_driver else None,
            date_de_permis=nd_driver_date_permis if nd_driver else None,
            date_nd_condicteur=nd_driver_birthday if nd_driver else None, 
            email_nd_condicteur=nd_driver_email if nd_driver else None, 
            opt_klm = opt_klm ,
            opt_klm_name = opt_klm_name,
            opt_klm_price = float(opt_klm_unit) if opt_klm_unit else 0.00,
            opt_klm_total = Decimal(opt_klm_total) if opt_klm_total else 0,
            opt_payment = paiement_anticipe,
            opt_payment_name = opt_payment_name,
            opt_payment_price = float(opt_payment_unit) if opt_payment_unit else 0.00,
            opt_payment_total = Decimal(opt_payment_total) if opt_payment_total else 0,
            opt_protection = protection,
            opt_protection_name = protection_name,
            opt_protection_caution= Decimal(protection_caution) if protection_caution else 0,
            opt_protection_price=float(protection_unit) if protection_unit else 0.00,
            opt_protection_total=Decimal(protection_total) if protection_total else 0,
            opt_nd_driver=nd_driver_opt,
            opt_nd_driver_name=nd_driver_opt_name,
            opt_nd_driver_price=float(nd_driver_opt_unit) if nd_driver_opt_unit else 0.00,
            opt_nd_driver_total=Decimal(nd_driver_opt_total) if nd_driver_opt_total else 0,
            opt_plein_carburant=carburant,
            opt_plein_carburant_name=carburant_name,
            opt_plein_carburant_prix= float(carburant_unit) if carburant_unit else 0.00,
            opt_plein_carburant_total=Decimal(carburant_total) if carburant_total else 0,
            opt_siege_a = sb_a,
            opt_siege_a_name=sb_a_name,
            opt_siege_a_prix=float(sb_a_unit) if sb_a_unit else 0.00,
            opt_siege_a_total=Decimal(sb_a_total) if sb_a_total else 0,
            opt_siege_b = sb_b,
            opt_siege_b_name= sb_b_name,
            opt_siege_b_prix=float(sb_b_unit) if sb_b_unit else 0.00,
            opt_siege_b_total=Decimal(sb_b_total) if sb_b_total else 0,
            opt_siege_c=sb_c,
            opt_siege_c_prix=float(sb_c_unit) if sb_c_unit else 0.00,
            opt_siege_c_name=sb_c_name,
            opt_siege_c_total=Decimal(sb_c_total) if sb_c_unit else 0,
            num_vol=num_vol,
            frais_de_dossier = Decimal(frais_dossier.prix),
            prix_jour = Decimal(prix_jour),
            nbr_jour_one = Decimal(total_days),
            frais_de_livraison = Decimal(frais_liv),
            supplements = Decimal(supp_total) ,
            retour_tard = Decimal(ecart_montant),
            total_afficher = Decimal(total_afficher),
            prix_jour_afficher = float(prix_unitaire),
            options_total = Decimal(total_option),
            total = Decimal(total) ,
            reduction = client_red_pr if  client_red_pr > promo_value else promo_value,
            total_afficher_reduit = Decimal(total_afficher_red),
            prix_jour_afficher_reduit = float(last_prix_unitaire),
            total_reduit = Decimal(last_total),
            total_reduit_euro = float(last_total),
            reste_payer = float(last_total),
            exchange_amount = float(change),
            country_code = pays_drapeau,
        )  
        montant_a_paye = to_pay if to_pay>0 else last_total

        if ccountry_code == "DZ" :
            return JsonResponse({"payment":False,"message": "Réservation créée avec succès.", "reservation_id": reservation.id}, status=201)
        
        else :
            request_factory = RequestFactory()
            fake_request = request_factory.post(
                path="/create-payment-session-reservation/",
                data=json.dumps({
                    "product_name": f"Réservation N° : {reservation.name}",
                    "description": f"Réservation du {reservation.model_name} du {date_depart} à {heure_depart} au {date_retour} à {heure_retour}",
                    "images": [vehicule.modele.photo_link_pay] if vehicule.modele.photo_link_pay else [],
                    "unit_amount": int(float(montant_a_paye) * 100),
                    "quantity": 1,
                    "currency": "eur",
                    "reservation_id": reservation.id,
                    "montant_total":float(last_total),
                    "montant_paye":float(montant_a_paye),
                    "email": reservation.email,
                    "token":token

                }),
                content_type="application/json"
            )
            payment_session_response = create_payment_session_reservation(fake_request)
            if payment_session_response.status_code == 200:
                payment_session_data = json.loads(payment_session_response.content)
                session_id = payment_session_data.get("session_id", "")
                payment_url = payment_session_data.get("url", "")
                return JsonResponse({"payment":True,"message": "Réservation créée avec succès.", "reservation_id": reservation.id, "session_id": session_id, "payment_url": payment_url}, status=201)
            else:
                return JsonResponse({"payment":False,"error": "Échec de la création de la session de paiement.", "response": payment_session_response.content.decode('utf-8')}, status=500)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Données JSON invalides."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def create_payment_session_reservation(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

        data = json.loads(request.body)
        product_name = data.get("product_name")
        description = data.get("description")
        images = data.get("images", [])
        unit_amount = data.get("unit_amount")
        quantity = data.get("quantity")
        currency = data.get("currency", "eur")
        reservation_id = data.get("reservation_id")
        customer_email = data.get("email")
        token = data.get("token")


        if not all([product_name, description, unit_amount, quantity]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        unit_amount = int(unit_amount)
        quantity = int(quantity)

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": product_name,
                            "description": description,
                            "images": images,
                        },
                        "unit_amount": unit_amount,
                    },
                    "quantity": quantity,
                },
            ],
            mode="payment",
            success_url=f"https://safarelamir.com/confirmation/{reservation_id}?token={token}",
            cancel_url="https://safarelamir.com/cancel",
            customer_email=customer_email,
            metadata={
                "reservation_id": str(reservation_id),
                "montant_total": str(data.get("montant_total", 0)), 
                "montant_paye": str(data.get("montant_paye", 0)),
                "type":"reservation"
            }
        )

        return JsonResponse({"session_id": checkout_session.id, "url": checkout_session.url}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def stripe_webhook_reservation_(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET 
 

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return JsonResponse({"error": "Invalid payload"}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({"error": "Invalid signature"}, status=400)

    

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        type_id = session.get("metadata", {}).get("type")
        if type_id == "reservation":
            reservation_id = session.get("metadata", {}).get("reservation_id")
            montant_total = session.get("metadata", {}).get("montant_total")
            montant_paye = session.get("metadata", {}).get("montant_paye")

            montant_total = float(montant_total) if montant_total else 0
            montant_paye = float(montant_paye) if montant_paye else 0

            montant_paye_dec = Decimal(montant_paye) if montant_paye else Decimal("0.00")

            reservation = Reservation.objects.filter(id=reservation_id).first()
            if reservation.status != "confirmee" :
                reservation.status ="confirmee"
                reservation.montant_paye = montant_paye_dec
                reservation.reste_payer = float(reservation.total_reduit_euro) - float(montant_paye_dec)
                reservation.save()
                

                date_heure_depart = reservation.date_heure_debut
                date_heure_retour = reservation.date_heure_fin

                date_debut = date_heure_depart.strftime("%d %B %Y") 
                heure_debut = date_heure_depart.strftime("%H:%M")  

                date_fin = date_heure_retour.strftime("%d %B %Y")
                heure_fin = date_heure_retour.strftime("%H:%M")

                taux = TauxChange.objects.filter(id=2).first()
                taux_change = taux.montant

                sujet = f"Confirmation de votre reservation N°= {reservation.name}"
                expediteur = settings.EMAIL_HOST_USER

                html_message = render_to_string('email/confirmation_email.html', {
                    "referance":reservation.name,
                    "mobile_one":reservation.lieu_depart.mobile,
                    "adresse_one":reservation.lieu_depart.address,
                    "mobile_two":reservation.lieu_retour.mobile,
                    "adresse_two":reservation.lieu_retour.address,
                    'client': reservation.client.nom,
                    'client_prenom':reservation.client.prenom,
                    'durrée':reservation.duree_dereservation,
                    'model_name':reservation.model_name,
                    'reste_paye':montant_total - montant_paye,
                    'caution':reservation.opt_protection_caution,
                    "date_depart_char" : reservation.date_depart_char,
                    "date_retour_char" : reservation.date_retour_char,
                    "heure_depart_char" : reservation.heure_depart_char,
                    "heure_retour_char" : reservation.heure_retour_char,
                    'date_depart':date_debut,
                    'heure_depart':heure_debut,
                    'date_retoure':date_fin,
                    'haure_retour':heure_fin,
                    'lieu_depart':reservation.lieu_depart.name,
                    'lieu_depart_id':f"https://api.safarelamir.com/location-description/?lieu_id={reservation.lieu_depart.id}",
                    'lieu_retour':reservation.lieu_retour.name,
                    'lieu_retour_id':f"https://api.safarelamir.com/location-description/?lieu_id={reservation.lieu_retour.id}",

                })

                send_mail(
                    sujet,
                    strip_tags(html_message),  
                    expediteur,
                    [reservation.email],
                    html_message=html_message,
                    fail_silently=False,
                )

                montant_total = Decimal(montant_total) if montant_total else Decimal("0.00")
                montant_paye = Decimal(montant_paye) if montant_paye else Decimal("0.00")
                taux_change = Decimal(taux.montant) if taux else Decimal("1.00") 

                payment = Payment.objects.create(
                    reservation=reservation,
                    vehicule=reservation.vehicule,  
                    modele=reservation.modele,  
                    zone=reservation.lieu_depart.zone,  
                    total_reduit_euro=montant_total,
                    montant=montant_paye,
                    montant_dzd=0,
                    montant_eur_dzd=montant_paye * taux_change,
                    montant_dzd_eur=0,  
                    note="Paiement effectué via Stripe",  
                    total_reduit_dinar=montant_total * taux_change,
                    ecart_eur=montant_total - montant_paye,
                    ecart_da=(montant_total - montant_paye) * taux_change,
                    mode_paiement="carte", 
                    total_encaisse=montant_paye,  
                )
                payment.save()

                livraison = Livraison.objects.create(
                    reservation = reservation,
                    name = reservation.name,
                    opt_protection_caution = reservation.opt_protection.caution,
                    opt_protection = reservation.opt_protection.name,
                    opt_carburant = reservation.opt_plein_carburant,
                    opt_carburant_check = True if reservation.opt_plein_carburant else False,
                    opt_klm = reservation.opt_klm,
                    opt_klm_check = True if reservation.opt_klm else False,
                    opt_nd_driver = reservation.opt_nd_driver ,
                    opt_nd_driver_check = True if reservation.opt_nd_driver else False,
                    opt_sb_a = reservation.opt_siege_a,
                    opt_sb_a_check = True if reservation.opt_siege_a else False,
                    opt_sb_b = reservation.opt_siege_b,
                    opt_sb_b_check = True if reservation.opt_siege_b else False,
                    opt_sb_c = reservation.opt_siege_c,
                    opt_sb_c_check = True if reservation.opt_siege_c else False,
                    status = reservation.status,
                    date_heure_debut = reservation.date_heure_debut,
                    date_heure_fin = reservation.date_heure_fin,
                    date_de_reservation = reservation.create_date,
                    nbr_jour_reservation = reservation.nbr_jour_reservation,
                    duree_dereservation = reservation.duree_dereservation,
                    lieu_depart = reservation.lieu_depart,
                    zone = reservation.zone,
                    lieu_retour = reservation.lieu_retour,
                    vehicule = reservation.vehicule,
                    modele = reservation.modele,
                    carburant = reservation.carburant,
                    client = reservation.client,
                    nom = reservation.nom,
                    prenom = reservation.prenom,
                    email = reservation.email,
                    mobile = reservation.mobile,
                    total_reduit_euro = reservation.reste_payer,
                    total_payer = reservation.reste_payer,
                    stage = 'reserve',
                    lv_type = "livraison",
                    action_lieu=reservation.lieu_depart.name,
                    action_date=reservation.date_heure_debut,
                    date_depart_char_ = reservation.date_depart_char if reservation.date_depart_char else None,
                    date_retour_char_ = reservation.date_retour_char if reservation.date_retour_char else None,
                    heure_depart_char_ = reservation.heure_depart_char if reservation.heure_depart_char else None,
                    heure_retour_char_ = reservation.heure_retour_char if reservation.heure_retour_char else None,
                    num_vol = reservation.num_vol if reservation.num_vol else None,

                ) 
                livraison.save()

                restitution = Livraison.objects.create(
                    reservation = reservation,
                    name = reservation.name,
                    opt_protection_caution = reservation.opt_protection.caution,
                    opt_protection = reservation.opt_protection.name,
                    opt_carburant = reservation.opt_plein_carburant,
                    opt_carburant_check = True if reservation.opt_plein_carburant else False,
                    opt_klm = reservation.opt_klm,
                    opt_klm_check = True if reservation.opt_klm else False,
                    opt_nd_driver = reservation.opt_nd_driver ,
                    opt_nd_driver_check = True if reservation.opt_nd_driver else False,
                    opt_sb_a = reservation.opt_siege_a,
                    opt_sb_a_check = True if reservation.opt_siege_a else False,
                    opt_sb_b = reservation.opt_siege_b,
                    opt_sb_b_check = True if reservation.opt_siege_b else False,
                    opt_sb_c = reservation.opt_siege_c,
                    opt_sb_c_check = True if reservation.opt_siege_c else False,
                    status = reservation.status,
                    date_heure_debut = reservation.date_heure_debut,
                    date_heure_fin = reservation.date_heure_fin,
                    date_de_reservation = reservation.create_date,
                    nbr_jour_reservation = reservation.nbr_jour_reservation,
                    duree_dereservation = reservation.duree_dereservation,
                    lieu_depart = reservation.lieu_depart,
                    zone = reservation.zone,
                    lieu_retour = reservation.lieu_retour,
                    vehicule = reservation.vehicule,
                    modele = reservation.modele,
                    carburant = reservation.carburant,
                    client = reservation.client,
                    nom = reservation.nom,
                    prenom = reservation.prenom,
                    email = reservation.email,
                    mobile = reservation.mobile,
                    total_reduit_euro = reservation.reste_payer,
                    total_payer = reservation.reste_payer,
                    stage = 'reserve',
                    lv_type = "restitution",
                    action_lieu=reservation.lieu_retour.name,
                    action_date=reservation.date_heure_fin,
                    date_depart_char_ = reservation.date_depart_char if reservation.date_depart_char else None,
                    date_retour_char_ = reservation.date_retour_char if reservation.date_retour_char else None,
                    heure_depart_char_ = reservation.heure_depart_char if reservation.heure_depart_char else None,
                    heure_retour_char_ = reservation.heure_retour_char if reservation.heure_retour_char else None,
                    num_vol = reservation.num_vol if reservation.num_vol else None,
                ) 
                restitution.save()

                print(f"Paiement réussi pour la réservation ID: {reservation_id}")
        elif type_id == "verify_calculate":
            session = event["data"]["object"]
            reservation_id = session.get("metadata", {}).get("reservation_id")
            lieu_depart_id = session.get("metadata", {}).get("lieu_depart_id")
            lieu_retour_id = session.get("metadata", {}).get("lieu_retour_id")
            date_depart = session.get("metadata", {}).get("date_depart")
            heure_depart = session.get("metadata", {}).get("heure_depart")
            date_retour = session.get("metadata", {}).get("date_retour")
            heure_retour = session.get("metadata", {}).get("heure_retour")
            montant_paye = session.get("metadata", {}).get("montant_paye")

            reservation_obj = Reservation.objects.get(id=reservation_id)
            lieu_depart_obj = Lieux.objects.get(id=lieu_depart_id)
            lieu_retour_obj = Lieux.objects.get(id=lieu_retour_id)
            date_depart_obj = datetime.strptime(date_depart, "%Y-%m-%d").date()
            heure_depart_obj = datetime.strptime(heure_depart, "%H:%M").time()
            date_retour_obj = datetime.strptime(date_retour, "%Y-%m-%d").date()
            heure_retour_obj = datetime.strptime(heure_retour, "%H:%M").time()

            print("reservation_date_one : ",reservation_obj.date_heure_debut , " date_two : ",reservation_obj.date_heure_fin)
            print("new_date_one : ",datetime.combine(date_depart_obj, heure_depart_obj) , " date_two : ",datetime.combine(date_retour_obj, heure_retour_obj))
            if (reservation_obj.date_heure_debut != datetime.combine(date_depart_obj, heure_depart_obj)) or (reservation_obj.date_heure_fin != datetime.combine(date_retour_obj, heure_retour_obj)):
                reservation_obj.du_au_modifier = (f"{reservation_obj.date_heure_debut.strftime('%d/%m/%Y %H:%M')} → "
                                                    f"{reservation_obj.date_heure_fin.strftime('%d/%m/%Y %H:%M')}")
                reservation_obj.date_heure_debut = datetime.combine(date_depart_obj, heure_depart_obj)
                reservation_obj.date_heure_fin = datetime.combine(date_retour_obj, heure_retour_obj)
            if reservation_obj.lieu_depart.id != lieu_depart_obj.id or reservation_obj.lieu_retour.id != lieu_retour_obj.id :
                reservation_obj.ancien_lieu = f"{reservation_obj.lieu_depart.name} → {reservation_obj.lieu_retour.name}"
                reservation_obj.lieu_depart = lieu_depart_obj
                reservation_obj.lieu_retour = lieu_retour_obj
            reservation_obj.save()
            
            print(f"Paiement réussi pour la modification du réservation ID: {reservation_id}")

    return JsonResponse({"status": "success"}, status=200)

@csrf_exempt
def create_payment_link(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Only POST requests are allowed"}, status=405)
        data = json.loads(request.body)
        product_name = data.get("product_name")
        description = data.get("description")
        images = data.get("images", [])
        unit_amount = data.get("unit_amount")
        quantity = data.get("quantity")
        currency = data.get("currency", "eur")
        if not all([product_name, description, unit_amount, quantity]):
            return JsonResponse({"error": "Missing required fields"}, status=400)
        unit_amount = int(unit_amount)
        quantity = int(quantity)

        product = stripe.Product.create(
            name=product_name,
            description=description,
            images=images
        )

        price = stripe.Price.create(
            product=product.id,
            unit_amount=unit_amount,
            currency=currency
        )

        payment_link = stripe.PaymentLink.create(
            line_items=[
                {
                    "price": price.id,
                    "quantity": quantity,
                },
            ],
        )

        return JsonResponse({"url": payment_link.url}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def create_payment_session(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

        data = json.loads(request.body)
        product_name = data.get("product_name")
        description = data.get("description")
        images = data.get("images", [])
        unit_amount = data.get("unit_amount")
        quantity = data.get("quantity")
        currency = data.get("currency", "eur")
        reservation_id = data.get("reservation_id")

        if not all([product_name, description, unit_amount, quantity]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        unit_amount = int(unit_amount)
        quantity = int(quantity)

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": product_name,
                            "description": description,
                            "images": images,
                        },
                        "unit_amount": unit_amount,
                    },
                    "quantity": quantity,
                },
            ],
            mode="payment",
            success_url= f"https://safarelamir.com/confirmation?id={reservation_id}",
            cancel_url="https://safarelamir.com/cancel",
        )

        return JsonResponse({"session_id": checkout_session.id, "url": checkout_session.url}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return JsonResponse({"error": "Invalid payload"}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({"error": "Invalid signature"}, status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        handle_payment_success(session)
    elif event["type"] == "checkout.session.expired":
        session = event["data"]["object"]
        handle_payment_expired(session)

    return JsonResponse({"status": "success"}, status=200)

def handle_payment_success(session):
    print(f"Paiement réussi pour la session {session['id']}")

def handle_payment_expired(session):
    print(f"Paiement expiré pour la session {session['id']}")

def new_modeles_view(request):

    try:
        resultats = new_models()
        return JsonResponse({"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})


@csrf_exempt
@require_http_methods(["PUT"])
def add_options_put_view(request):
    try:
        data = json.loads(request.body)
        ref = data.get("ref")
        klm = data.get("klm")
        nd_driver = data.get("nd_driver")
        carburant = data.get("carburant")
        sb_a = data.get("sb_a")
        sb_b = data.get("sb_b")
        sb_c = data.get("sb_c")
        nom = data.get("nom")
        prenom = data.get("prenom")
        birthday = data.get("birthday")
        permis_date = data.get("permis_date")
        country_code = request.META.get("HTTP_X_COUNTRY_CODE")

        if not ref:
            return JsonResponse({"error": "Le champ 'ref' est requis."}, status=400)

        if country_code == "DZ":
            return JsonResponse({"message": "vous ne pouvez pas effectuer le paiement"}, status=400)
        else : 
            reservation = Reservation.objects.filter(name=ref).first()
            lieu_depart_obj = reservation.lieu_depart

            request_result = add_options_request(
                                                ref=ref,
                                                klm=klm,
                                                nd_driver=nd_driver,
                                                carburant=carburant,
                                                sb_a=sb_a,
                                                sb_b=sb_b,
                                                sb_c=sb_c,
                                                country_code=country_code
                                                )
            print(request_result)
            
            if nd_driver == "yes":
                if not nom or not prenom or not birthday or not permis_date :
                    return JsonResponse({"error": "Les champ 'info client' sont requis."}, status=400)
                else :
                    risque_client = verify_client(reservation.email, nom, prenom, birthday, permis_date, reservation.telephone)
                    print("risque_client : ",risque_client)
                    if risque_client.get("message") == "negatif":
                        return JsonResponse({"message": "2eme conducteur est bloqué"}, status=400)
                    else : 
                        nd_client_id = risque_client.get("client_id",None) 
                        if nd_client_id is not None:
                            nd_client = ListeClient.objects.filter(id=nd_client_id).first()
                            nd_client_name = nd_client.name
                            nd_client_permis = nd_client.date_de_permis
                            nd_client_birthday = nd_client.date_de_naissance
                            nd_client_phone = nd_client.telephone
                            nd_client_email = nd_client.email
                            nd_client_risque = nd_client.risque
                            nd_client_code_prime = nd_client.code_prime
                            nd_client_category = nd_client.categorie_client
                            nd_client_solde = nd_client.solde

            if isinstance(request_result, str):
                request_result = json.loads(request_result)

            to_pay = request_result.get("total_price", 0)
            if to_pay > 0 and reservation.opt_payment_name :
                request_factory = RequestFactory()
                fake_request = request_factory.post(
                    path="/create-payment-session-option/",
                    data=json.dumps({
                        "product_name": reservation.name,
                        "description": "test",
                        "images": [reservation.vehicule.photo_link] if reservation.vehicule.photo_link else [],
                        "unit_amount": int(to_pay * 100),
                        "quantity": 1,
                        "currency": "eur",
                        "reservation_id": reservation.id
                    }),
                    content_type="application/json"
                )

                payment_session_response = create_payment_session_option(fake_request)

                if payment_session_response.status_code == 200:
                    payment_session_data = json.loads(payment_session_response.content)
                    session_id = payment_session_data.get("session_id", "")
                    payment_url = payment_session_data.get("url", "")
                    return JsonResponse({"message": "Réservation créée avec succès.", "reservation_id": reservation.id, "session_id": session_id, "payment_url": payment_url}, status=201)
                else:
                    return JsonResponse({"error": "Échec de la création de la session de paiement.", "response": payment_session_response.content.decode('utf-8')}, status=500)
            elif to_pay >= 0 and not reservation.opt_payment_name :

                klm_put = request_result.get("klm", None)
                print("klm_put : ",klm_put)
                if klm_put is not None :
                    print("klm_put : ",klm_put)
                    klm_discount = klm_put.get("klM_last_price",None)
                    category = reservation.categorie
                    klm_name = klm_put.get("klm_name",None)
                    klm_option = Options.objects.filter(name=klm_name,categorie=category, zone= lieu_depart_obj.zone).first()
                    if klm_discount is None:
                        reservation.opt_klm = klm_option
                        reservation.opt_klm_name = klm_option.name
                        reservation.opt_klm_price = klm_option.prix
                        reservation.opt_klm_total = klm_option.prix * reservation.nbr_jour_reservation
                        reservation.save()
                    else:
                        reservation.opt_klm = klm_option
                        reservation.opt_klm_name = klm_option.name
                        reservation.opt_klm_price = 0
                        reservation.opt_klm_total = 0
                        reservation.save()

                nd_driver_put = request_result.get("nd_driver", None)
                if nd_driver_put is not None :
                    nd_driver_discount = nd_driver_put.get("nd_driver_last_price",None)
                    nd_driver_name = nd_driver_put.get("nd_driver_name",None)
                    nd_driver_option = Options.objects.filter(name=nd_driver_name, zone= lieu_depart_obj.zone).first()
                    if nd_driver_discount is None:
                        reservation.opt_nd_driver = nd_driver_option
                        reservation.opt_nd_driver_name = nd_driver_option.name
                        reservation.opt_nd_driver_price = nd_driver_option.prix
                        reservation.opt_nd_driver_total = nd_driver_option.prix * reservation.nbr_jour_reservation
                        #nd_client_name = nd_client.name
                        #nd_client_permis = nd_client.date_de_permis
                        #nd_client_birthday = nd_client.date_de_naissance
                        #nd_client_phone = nd_client.telephone
                        #nd_client_email = nd_client.email
                        #nd_client_risque = nd_client.risque
                        #nd_client_code_prime = nd_client.code_prime
                        #nd_client_category = nd_client.categorie_client
                        #nd_client_solde = nd_client.solde
                        reservation.save()
                    else:
                        reservation.opt_nd_driver = nd_driver_option
                        reservation.opt_nd_driver_name = nd_driver_option.name
                        reservation.opt_nd_driver_price = 0
                        reservation.opt_nd_driver_total = 0
                        reservation.save()

                carburant_put = request_result.get("carburant", None)
                if carburant_put is not None :
                    carburant_discount = carburant_put.get("carburant_last_price",None)
                    carburant_name = carburant_put.get("carburant_name",None)
                    carburant_option = Options.objects.filter(name=carburant_name, zone= lieu_depart_obj.zone).first()
                    if carburant_discount is None:
                        reservation.opt_plein_carburant = carburant_option
                        reservation.opt_plein_carburant_name = carburant_option.name
                        reservation.opt_plein_carburant_prix = carburant_option.prix
                        reservation.opt_plein_carburant_total = carburant_option.prix * reservation.nbr_jour_reservation
                        reservation.save()
                    else:
                        reservation.opt_plein_carburant = carburant_option
                        reservation.opt_plein_carburant_name = carburant_option.name
                        reservation.opt_plein_carburant_prix = 0
                        reservation.opt_plein_carburant_total = 0
                        reservation.save()
                
                sb_a_put = request_result.get("sb_a", None)
                if sb_a_put is not None :
                    sb_a_discount = sb_a_put.get("sb_a_last_price",None)
                    sb_a_name = sb_a_put.get("sb_a_name",None)
                    sb_a_option = Options.objects.filter(name=sb_a_name, zone= lieu_depart_obj.zone).first()
                    if sb_a_discount is None:
                        reservation.opt_siege_a = sb_a_option
                        reservation.opt_siege_a_name = sb_a_option.name
                        reservation.opt_siege_a_prix = sb_a_option.prix
                        reservation.opt_siege_a_total = sb_a_option.prix * reservation.nbr_jour_reservation
                        reservation.save()
                    else:
                        reservation.opt_siege_a = sb_a_option
                        reservation.opt_siege_a_name = sb_a_option.name
                        reservation.opt_siege_a_prix = 0
                        reservation.opt_siege_a_total = 0
                        reservation.save()

                sb_b_put = request_result.get("sb_b", None)
                if sb_b_put is not None :
                    sb_b_discount = sb_b_put.get("sb_b_last_price",None)
                    sb_b_name = sb_b_put.get("sb_b_name",None)
                    sb_b_option = Options.objects.filter(name=sb_b_name, zone= lieu_depart_obj.zone).first()
                    if sb_b_discount is None:
                        reservation.opt_siege_b = sb_b_option
                        reservation.opt_siege_b_name = sb_b_option.name
                        reservation.opt_siege_b_prix = sb_b_option.prix
                        reservation.opt_siege_b_total = sb_b_option.prix * reservation.nbr_jour_reservation
                        reservation.save()
                    else:
                        reservation.opt_siege_b = sb_b_option
                        reservation.opt_siege_b_name = sb_b_option.name
                        reservation.opt_siege_b_prix = 0
                        reservation.opt_siege_b_total = 0
                        reservation.save()

                sb_c_put = request_result.get("sb_c", None)
                if sb_c_put is not None :
                    sb_c_discount = sb_c_put.get("sb_c_last_price",None)
                    sb_c_name = sb_c_put.get("sb_c_name",None)
                    sb_c_option = Options.objects.filter(name=sb_c_name, zone= lieu_depart_obj.zone).first()
                    if sb_c_discount is None:
                        reservation.opt_siege_c = sb_c_option
                        reservation.opt_siege_c_name = sb_c_option.name
                        reservation.opt_siege_c_prix = sb_c_option.prix
                        reservation.opt_siege_c_total = sb_c_option.prix * reservation.nbr_jour_reservation
                        reservation.save()
                    else:
                        reservation.opt_siege_c = sb_c_option
                        reservation.opt_siege_c_name = sb_c_option.name
                        reservation.opt_siege_c_prix = 0
                        reservation.opt_siege_c_total = 0
                        reservation.save()
 
                return JsonResponse({"modified":True ,"message": "medification effectuer avec succee"}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Données JSON invalides."}, status=400)
    except Exception as e:
        print(f"Erreur: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def create_payment_session_option(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

        data = json.loads(request.body)
        product_name = data.get("product_name")
        description = data.get("description")
        images = data.get("images", [])
        unit_amount = data.get("unit_amount")
        quantity = data.get("quantity")
        currency = data.get("currency", "eur")
        reservation_id = data.get("reservation_id")

        if not all([product_name, description, unit_amount, quantity]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        unit_amount = int(unit_amount)
        quantity = int(quantity)

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": product_name,
                            "description": description,
                            "images": images,
                        },
                        "unit_amount": unit_amount,
                    },
                    "quantity": quantity,
                },
            ],
            mode="payment",
            success_url= f"https://safarelamir.com/confirmation?id={reservation_id}",
            cancel_url="https://safarelamir.com/cancel",
        )

        return JsonResponse({"session_id": checkout_session.id, "url": checkout_session.url}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

def add_options_request_view(request):
    ref = request.GET.get("ref")
    nd_driver = request.GET.get("nd_driver")
    carburant = request.GET.get("carburant")
    sb_a = request.GET.get("sb_a")
    sb_b = request.GET.get("sb_b")
    sb_c = request.GET.get("sb_c")
    klm = request.GET.get("klm")
    country_code = request.headers.get("X-Country-Code")

    if not ref or not nd_driver or not carburant or not sb_a or not sb_b or not sb_c:
        return JsonResponse({"error": "Tout les parametres sont requis."}, status=400)
    
    try:
        resultats = add_options_request(
            ref=ref,
            klm=klm,
            nd_driver=nd_driver,
            carburant=carburant,
            sb_a=sb_a,
            sb_b=sb_b,
            sb_c=sb_c,
            country_code = country_code
        )
        return JsonResponse({"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})



def mes_reservations_view(request):
    client_id = request.GET.get("client_id")
    country_code = request.headers.get("X-Country-Code") 

    if not client_id :
        return JsonResponse({"error": "Le paramètres 'client_id' est requis."}, status=400)

    try:
        resultats = mes_reservations(
            client_id=client_id,
            country_code=country_code
        )
        return JsonResponse({"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})

@csrf_exempt
@require_http_methods(["PUT"])
def cancel_do_view(request):
    try:
        data = json.loads(request.body)
        ref = data.get("ref")
        reason = data.get("reason")
        country_code = request.headers.get("X-Country-Code")

        if not ref:
            return JsonResponse({"error": "Le champ 'ref' est requis."}, status=400)

        if not reason:
            return JsonResponse({"error": "Le champ 'reason' est requis."}, status=400)

        annuler_raison = AnnulerRaison.objects.filter(id=reason).first()
        reservation = Reservation.objects.filter(name=ref).first()
        if not reservation or not annuler_raison:
            return JsonResponse({"error": "Réservation non trouvée avec la référence spécifiée."}, status=404)
        livraisons = Livraison.objects.filter(reservation=reservation)
        if livraisons.exists():
            livraisons.delete()
        today = date.today()
        date_reservation = reservation.date_heure_debut.date()
        periode_existe = Periode.objects.filter(
                date_debut__lte=date_reservation,
                date_fin__gte=date_reservation
            ).first()
        un_jour = 0
        if periode_existe :
            annulation = ConditionAnnulation.objects.filter(id=1).first()
            jours_restants = (date_reservation - today).days
            if (periode_existe.saison == annulation.haute_saison and jours_restants < annulation.haute_montant) or (periode_existe.saison == annulation.basse_saison and jours_restants < annulation.basse_montant):
                un_jour = reservation.prix_jour
            elif (periode_existe.saison == annulation.haute_saison and jours_restants >= annulation.haute_montant) or (periode_existe.saison == annulation.basse_saison and jours_restants >= annulation.basse_montant):
                un_jour = 15
        else : 
            un_jour = reservation.prix_jour
        
        if reservation.opt_payment_name and un_jour == 15:
            rembourssement = True
            montant_rembourse = reservation.total_reduit_euro - 15 
        elif not reservation.opt_payment_name and un_jour == 15:
            rembourssement = True
            montant_rembourse = reservation.prix_jour - 15
        else: 
            rembourssement = False
            montant_rembourse = 0
        if rembourssement and montant_rembourse > 0:
            refund = RefundTable(
                reservation=reservation,
                amount=montant_rembourse,  
                status='en_attent',
                date=timezone.now()
            )
            refund.save()

        reservation.status = "annule"
        reservation.etat_reservation = "annule"
        reservation.annuler_raison = annuler_raison
        reservation.save()

        sujet = f"Annulation de votre reservation N°= {reservation.name}"
        sujet_ceo = f"Annulation de  reservation N°= {reservation.name}"
        expediteur = settings.EMAIL_HOST_USER
        
        html_message = render_to_string('email/annulation_email.html', {
            "referance":reservation.name,
            "annuler_raison":reservation.annuler_raison.name,
            "client":reservation.client.name,
        })
        html_message_ceo = """
            <p>Bonjour,</p>

            <p>Une réservation vient d’être <strong>annulée</strong>.<br>
            Voici les détails :</p>

            <ul>
                <li><strong>Client :</strong> {reservation.client.name}</li>
                <li><strong>Référence :</strong> {reservation.name}</li>
                <li><strong>Cause d’annulation :</strong> {reservation.annuler_raison.name}</li>
                <li><strong>Montant a rembourser :</strong> {montant_ref}</li>
            </ul>

            <p>Ceci est une notification automatique pour information.</p>

            <p>Cordialement,<br>
            Le système Backoffice</p>
            """

        send_mail(
            sujet,
            strip_tags(html_message),  
            expediteur,
            [reservation.email],
            html_message=html_message,
            fail_silently=False,
        )
        send_mail(
            sujet_ceo,
            strip_tags(html_message_ceo),  
            expediteur,
            ["contact@safarelamir.com"],
            html_message=html_message_ceo,
            fail_silently=False,
        )
        taux = TauxChange.objects.filter(id=2).first()
        taux_change = taux.montant

        return JsonResponse({"rembourssement":rembourssement ,
                             "frais_annulation":un_jour * taux_change if country_code == "DZ" else un_jour,
                             "refund_amount":montant_rembourse * taux_change if country_code == "DZ" else montant_rembourse,
                             "message": "Modification effectuée avec succès."}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Données JSON invalides."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def cancel_request_view(request):
    ref = request.GET.get("ref")
    country_code = request.headers.get("X-Country-Code")

    if not ref :
        return JsonResponse({"error": "Le paramètres 'ref' est requis."}, status=400)

    try:
        resultats = cencel_request(
            ref=ref,
            country_code=country_code
        )
        if "success" in resultats:
            return JsonResponse({"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
        else:
            return JsonResponse({"results": resultats}, status=404, json_dumps_params={"ensure_ascii": False})
    except ValueError as ve:
        return JsonResponse({"error": str(ve)}, status=400, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})
        
@csrf_exempt
def verify_and_calculate_view(request):
    ref = request.GET.get("ref")
    lieu_depart = request.GET.get("lieu_depart")
    lieu_retour = request.GET.get("lieu_retour")
    date_depart = request.GET.get("date_depart")
    heure_depart = request.GET.get("heure_depart")
    date_retour = request.GET.get("date_retour")
    heure_retour = request.GET.get("heure_retour")
    country_code = request.headers.get("X-Country-Code")

    if not date_retour or not date_depart:
        return JsonResponse({"error": "Les paramètres 'date_retour' et 'date_depart' sont requis."}, status=400)

    try:
        resultats = verify_and_calculate(
            ref=ref,
            lieu_depart = lieu_depart,
            lieu_retour = lieu_retour,
            date_depart = date_depart,
            heure_depart = heure_depart,
            date_retour = date_retour,
            heure_retour = heure_retour,
            country_code = country_code
        )
        return JsonResponse({"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})

def ma_reservation_view(request):
    ref = request.GET.get("ref")
    email = request.GET.get("email")
    country_code = request.headers.get("X-Country-Code")

    if not ref or not email:
        return JsonResponse({"error": "Les paramètres 'ref' et 'email' sont requis."}, status=400)

    try:
        resultats = ma_reservation_detail(
            ref=ref,
            email=email,
            country_code=country_code
        )
        protection = protections(ref=ref, email=email, country_code=country_code)
        options = option_ma_reservation(ref=ref, email=email, country_code=country_code)
        if not options or not protection or not resultats:
            return JsonResponse({"protections":protection,"options": options ,"results": resultats}, status=404, json_dumps_params={"ensure_ascii": False})
        return JsonResponse({"protections":protection,"options": options ,"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})

def otp_send_client(request):
    if request.method == "GET":
        try:
            email = request.GET.get("email")

            if not email :
                return JsonResponse({"sent": False, "message": "Tous les champs (email, nom, prénom) sont requis."})

            result = otp_send(email)
            if result["client_id"] != None and result["account"] != None:
                return JsonResponse({"sent":True, "success": True, "client_id": result["client_id"]})
            else:
                return JsonResponse({"sent":False, "success": False, "account": result["account"]})

        except Exception as e:
            return JsonResponse({"sent": False, "message": f"Erreur: {str(e)}"})

    return JsonResponse({"sent": False, "message": "Méthode non autorisée. Utilisez GET."})

@csrf_exempt
def otp_verify_client(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            email = data.get("email")
            otp = data.get("otp")
            client_id = data.get("client_id")

            if not email or not otp:
                return JsonResponse({"success": False, "message": "Email et OTP sont requis."})

            result = otp_verify(email, otp, client_id)
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Erreur: {str(e)}"})

    return JsonResponse({"success": False, "message": "Méthode non autorisée. Utilisez POST."})

def search_result_view(request):
    lieu_depart_id = request.GET.get("lieu_depart_id")
    lieu_retour_id = request.GET.get("lieu_retour_id")
    date_depart = request.GET.get("date_depart")
    heure_depart = request.GET.get("heure_depart")
    date_retour = request.GET.get("date_retour")
    heure_retour = request.GET.get("heure_retour")
    client_id = request.GET.get("client_id")
    prime_code = request.GET.get("prime_code")
    country_code = request.GET.get("country_code")

    if not country_code :
        country_code = request.headers.get("X-Country-Code")

    if not date_depart or not date_retour:
        return JsonResponse({"error": "Les paramètres 'date_depart' et 'date_retour' sont requis."}, status=400)

    try:
        resultats = search_result_vehicule(
            lieu_depart_id=int(lieu_depart_id),
            lieu_retour_id=int(lieu_retour_id),
            date_depart=date_depart,
            heure_depart=heure_depart,
            date_retour=date_retour,
            heure_retour=heure_retour,
            client_id=client_id,
            prime_code=prime_code,
            country_code=country_code,
        )
        free_options = []
        if client_id :
            free_options = free_options_f(client_id)
        return JsonResponse({"free_options":free_options,"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})

def search_price_view(request):
    lieu_depart_id = request.GET.get("lieu_depart_id")
    lieu_retour_id = request.GET.get("lieu_retour_id")
    date_depart = request.GET.get("date_depart")
    heure_depart = request.GET.get("heure_depart")
    date_retour = request.GET.get("date_retour")
    heure_retour = request.GET.get("heure_retour")

    if not date_depart or not date_retour:
        return JsonResponse({"error": "Les paramètres 'date_depart' et 'date_retour' sont requis."}, status=400)

    try:
        # Appeler le service pour rechercher les tarifs
        resultats = rechercher_tarifs(
            lieu_depart_id=int(lieu_depart_id),
            lieu_retour_id=int(lieu_retour_id),
            date_depart=date_depart,
            heure_depart=heure_depart,
            date_retour=date_retour,
            heure_retour=heure_retour,
        )
        return JsonResponse({"results": resultats}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def search_vehicles(request):
    lieu_depart_id = request.GET.get("lieu_depart_id")
    lieu_retour_id = request.GET.get("lieu_retour_id")
    date_depart = request.GET.get("date_depart")
    heure_depart = request.GET.get("heure_depart")
    date_retour = request.GET.get("date_retour")
    heure_retour = request.GET.get("heure_retour")

    try:
        vehicles = rechercher_vehicules_disponibles(
            lieu_depart_id=int(lieu_depart_id),
            lieu_retour_id=int(lieu_retour_id),
            date_depart=date_depart,
            heure_depart=heure_depart,
            date_retour=date_retour,
            heure_retour=heure_retour,
        )
        vehicle_data = list(vehicles.values())
        return JsonResponse({"success": True, "vehicles": vehicle_data})
    except ValueError as e:
        return JsonResponse({"success": False, "error": str(e)})

def home(request):
    return HttpResponse("This is the homepage")

def zone_list(request):
    zones = Zone.objects.all()
    return render(request, 'zone_list.html', {'zones': zones})

def lieux_list(request):
    lieux = Lieux.objects.all()
    return render(request, 'lieux_list.html', {'lieux': lieux})

class LieuxViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Lieux.objects.all()
    serializer_class = LieuxSerializer

    def list(self, request):
        queryset = Lieux.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        lieu = self.queryset.get(pk=pk)
        serializer = self.serializer_class(lieu)
        return Response(serializer.data)

    def update(self, request, pk=None):
        lieu = self.queryset.get(pk=pk)
        serializer = self.serializer_class(lieu,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        lieu = self.queryset.get(pk=pk)
        lieu.delete()
        return Response(status=204)



class CategorieViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer

    def list(self, request):
        queryset = Categorie.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        categorie = self.queryset.get(pk=pk)
        serializer = self.serializer_class(categorie)
        return Response(serializer.data)

    def update(self, request, pk=None):
        categorie = self.queryset.get(pk=pk)
        serializer = self.serializer_class(categorie,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        categorie = self.queryset.get(pk=pk)
        categorie.delete()
        return Response(status=204)


class ModeleViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Modele.objects.all()
    serializer_class = ModeleSerializer

    def list(self, request):
        queryset = Modele.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        modele = self.queryset.get(pk=pk)
        serializer = self.serializer_class(modele)
        return Response(serializer.data)

    def update(self, request, pk=None):
        modele = self.queryset.get(pk=pk)
        serializer = self.serializer_class(modele,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        modele = self.queryset.get(pk=pk)
        modele.delete()
        return Response(status=204)


class VehiculeViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Vehicule.objects.all()
    serializer_class = VehiculeSerializer

    def list(self, request):
        queryset = Vehicule.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        vehicule = self.queryset.get(pk=pk)
        serializer = self.serializer_class(vehicule)
        return Response(serializer.data)

    def update(self, request, pk=None):
        vehicule = self.queryset.get(pk=pk)
        serializer = self.serializer_class(vehicule,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        vehicule = self.queryset.get(pk=pk)
        vehicule.delete()
        return Response(status=204)


class CategorieClientViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = CategorieClient.objects.all()
    serializer_class = CategorieClientSerializer

    def list(self, request):
        queryset = CategorieClient.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        categorie_client = self.queryset.get(pk=pk)
        serializer = self.serializer_class(categorie_client)
        return Response(serializer.data)

    def update(self, request, pk=None):
        categorie_client = self.queryset.get(pk=pk)
        serializer = self.serializer_class(categorie_client,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        categorie_client = self.queryset.get(pk=pk)
        categorie_client.delete()
        return Response(status=204)

class SoldeParrainageViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = SoldeParrainage.objects.all()
    serializer_class = SoldeParrainageSerializer

    def list(self, request):
        queryset = SoldeParrainage.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        solde_parrainage = self.queryset.get(pk=pk)
        serializer = self.serializer_class(solde_parrainage)
        return Response(serializer.data)

    def update(self, request, pk=None):
        solde_parrainage = self.queryset.get(pk=pk)
        serializer = self.serializer_class(solde_parrainage,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        solde_parrainage = self.queryset.get(pk=pk)
        solde_parrainage.delete()
        return Response(status=204)

class ListeClientViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = ListeClient.objects.all()
    serializer_class = ListeClientSerializer

    def list(self, request):
        queryset = ListeClient.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        liste_client = self.queryset.get(pk=pk)
        serializer = self.serializer_class(liste_client)
        return Response(serializer.data)

    def update(self, request, pk=None):
        liste_client = self.queryset.get(pk=pk)
        serializer = self.serializer_class(liste_client,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        liste_client = self.queryset.get(pk=pk)
        liste_client.delete()
        return Response(status=204)

class SaisonViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Saison.objects.all()
    serializer_class = SaisonSerializer

    def list(self, request):
        queryset = Saison.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        saison = self.queryset.get(pk=pk)
        serializer = self.serializer_class(saison)
        return Response(serializer.data)

    def update(self, request, pk=None):
        saison = self.queryset.get(pk=pk)
        serializer = self.serializer_class(saison,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        saison = self.queryset.get(pk=pk)
        saison.delete()
        return Response(status=204)

class PeriodeViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Periode.objects.all()
    serializer_class = PeriodeSerializer

    def list(self, request):
        queryset = Periode.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        periode = self.queryset.get(pk=pk)
        serializer = self.serializer_class(periode)
        return Response(serializer.data)

    def update(self, request, pk=None):
        periode = self.queryset.get(pk=pk)
        serializer = self.serializer_class(periode,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        periode = self.queryset.get(pk=pk)
        periode.delete()
        return Response(status=204)

class NombreDeJourViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = NombreDeJour.objects.all()
    serializer_class = NombreDeJourSerializer

    def list(self, request):
        queryset = NombreDeJour.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        nb_jour = self.queryset.get(pk=pk)
        serializer = self.serializer_class(nb_jour)
        return Response(serializer.data)

    def update(self, request, pk=None):
        nb_jour = self.queryset.get(pk=pk)
        serializer = self.serializer_class(nb_jour,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        nb_jour = self.queryset.get(pk=pk)
        nb_jour.delete()
        return Response(status=204)


class TarifsViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Tarifs.objects.all()
    serializer_class = TarifsSerializer

    def list(self, request):
        queryset = Tarifs.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        tarif = self.queryset.get(pk=pk)
        serializer = self.serializer_class(tarif)
        return Response(serializer.data)

    def update(self, request, pk=None):
        tarif = self.queryset.get(pk=pk)
        serializer = self.serializer_class(tarif,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        tarif = self.queryset.get(pk=pk)
        tarif.delete()
        return Response(status=204)

class OptionsViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Options.objects.all()
    serializer_class = OptionsSerializer

    def list(self, request):
        queryset = Options.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        option = self.queryset.get(pk=pk)
        serializer = self.serializer_class(option)
        return Response(serializer.data)

    def update(self, request, pk=None):
        option = self.queryset.get(pk=pk)
        serializer = self.serializer_class(option,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        option = self.queryset.get(pk=pk)
        option.delete()
        return Response(status=204)


class FraisLivraisonViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = FraisLivraison.objects.all()
    serializer_class = FraisLivraisonSerializer

    def list(self, request):
        queryset = FraisLivraison.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        frais_livraison = self.queryset.get(pk=pk)
        serializer = self.serializer_class(frais_livraison)
        return Response(serializer.data)

    def update(self, request, pk=None):
        frais_livraison = self.queryset.get(pk=pk)
        serializer = self.serializer_class(frais_livraison,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        frais_livraison = self.queryset.get(pk=pk)
        frais_livraison.delete()
        return Response(status=204)


class SupplementViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Supplement.objects.all()
    serializer_class = SupplementSerializer

    def list(self, request):
        queryset = Supplement.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        supplement = self.queryset.get(pk=pk)
        serializer = self.serializer_class(supplement)
        return Response(serializer.data)

    def update(self, request, pk=None):
        supplement = self.queryset.get(pk=pk)
        serializer = self.serializer_class(supplement,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        supplement = self.queryset.get(pk=pk)
        supplement.delete()
        return Response(status=204)

class PromotionViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer

    def list(self, request):
        queryset = Promotion.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        promotion = self.queryset.get(pk=pk)
        serializer = self.serializer_class(promotion)
        return Response(serializer.data)

    def update(self, request, pk=None):
        promotion = self.queryset.get(pk=pk)
        serializer = self.serializer_class(promotion,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        promotion = self.queryset.get(pk=pk)
        promotion.delete()
        return Response(status=204)


class ReservationViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    def list(self, request):
        queryset = Reservation.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        reservation = self.queryset.get(pk=pk)
        serializer = self.serializer_class(reservation)
        return Response(serializer.data)

    def update(self, request, pk=None):
        reservation = self.queryset.get(pk=pk)
        serializer = self.serializer_class(reservation,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        reservation = self.queryset.get(pk=pk)
        reservation.delete()
        return Response(status=204)


class LivraisonViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Livraison.objects.all()
    serializer_class = LivraisonSerializer

    def list(self, request):
        queryset = Livraison.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        livraison = self.queryset.get(pk=pk)
        serializer = self.serializer_class(livraison)
        return Response(serializer.data)

    def update(self, request, pk=None):
        livraison = self.queryset.get(pk=pk)
        serializer = self.serializer_class(livraison,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        livraison = self.queryset.get(pk=pk)
        livraison.delete()
        return Response(status=204)


class TauxChangeViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = TauxChange.objects.all()
    serializer_class = TauxChangeSerializer

    def list(self, request):
        queryset = TauxChange.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        taux_change = self.queryset.get(pk=pk)
        serializer = self.serializer_class(taux_change)
        return Response(serializer.data)

    def update(self, request, pk=None):
        taux_change = self.queryset.get(pk=pk)
        serializer = self.serializer_class(taux_change,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        taux_change = self.queryset.get(pk=pk)
        taux_change.delete()
        return Response(status=204)


class BookCarViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = BookCar.objects.all()
    serializer_class = BookCarSerializer

    def list(self, request):
        queryset = BookCar.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        taux_change = self.queryset.get(pk=pk)
        serializer = self.serializer_class(taux_change)
        return Response(serializer.data)

    def update(self, request, pk=None):
        taux_change = self.queryset.get(pk=pk)
        serializer = self.serializer_class(taux_change,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        taux_change = self.queryset.get(pk=pk)
        taux_change.delete()
        return Response(status=204)


class ConditionAnnulationViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = ConditionAnnulation.objects.all()
    serializer_class = ConditionAnnulationSerializer

    def list(self, request):
        queryset = ConditionAnnulation.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        taux_change = self.queryset.get(pk=pk)
        serializer = self.serializer_class(taux_change)
        return Response(serializer.data)

    def update(self, request, pk=None):
        taux_change = self.queryset.get(pk=pk)
        serializer = self.serializer_class(taux_change,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)



    def destroy(self, request, pk=None):
        taux_change = self.queryset.get(pk=pk)
        taux_change.delete()
        return Response(status=204)



class PaymentViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def list(self, request):
        queryset = Payment.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        taux_change = self.queryset.get(pk=pk)
        serializer = self.serializer_class(taux_change)
        return Response(serializer.data)

    def update(self, request, pk=None):
        taux_change = self.queryset.get(pk=pk)
        serializer = self.serializer_class(taux_change,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def destroy(self, request, pk=None):
        taux_change = self.queryset.get(pk=pk)
        taux_change.delete()
        return Response(status=204)

class HistoriqueSoldeViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = HistoriqueSolde.objects.all()
    serializer_class = HistoriqueSoldeSerializer

    def list(self, request):
        queryset = HistoriqueSolde.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        taux_change = self.queryset.get(pk=pk)
        serializer = self.serializer_class(taux_change)
        return Response(serializer.data)

    def update(self, request, pk=None):
        taux_change = self.queryset.get(pk=pk)
        serializer = self.serializer_class(taux_change,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def destroy(self, request, pk=None):
        taux_change = self.queryset.get(pk=pk)
        taux_change.delete()
        return Response(status=204)

@csrf_exempt
def create_payment_authorization_session____(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

        data = json.loads(request.body)
        
        deposit_amount = data.get("deposit_amount", 10000)  # 100€ en centimes par défaut
        currency = data.get("currency", "eur")
        reservation_id = data.get("reservation_id")
        
        if not reservation_id:
            return JsonResponse({"error": "reservation_id is required"}, status=400)
        
        deposit_amount = int(deposit_amount)
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": "Dépôt de garantie - Réservation",
                            "description": f"Autorisation de {deposit_amount/100}€ pour la réservation #{reservation_id}",
                            "images": [],  # Tu peux ajouter une image de ton logo
                        },
                        "unit_amount": deposit_amount,
                    },
                    "quantity": 1,
                },
            ],
            mode="payment",
            payment_intent_data={
                "capture_method": "manual",  # Ceci est la clé pour l'autorisation non capturée
                "description": f"Dépôt de garantie pour réservation #{reservation_id}",
                "metadata": {
                    "type": "deposit_authorization",
                    "reservation_id": str(reservation_id),
                }
            },
            success_url=f"https://safarelamir.com/deposit-success?reservation_id={reservation_id}&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"https://safarelamir.com/deposit-cancel?reservation_id={reservation_id}",
            metadata={
                "type": "deposit_authorization",
                "reservation_id": str(reservation_id),
                "deposit_amount": str(deposit_amount),
            }
        )

        return JsonResponse({
            "session_id": checkout_session.id, 
            "url": checkout_session.url,
            "amount": deposit_amount,
            "currency": currency,
            "type": "authorization"
        }, status=200)
        
    except stripe.error.StripeError as e:
        return JsonResponse({"error": f"Stripe error: {str(e)}"}, status=400)
    except ValueError as e:
        return JsonResponse({"error": f"Invalid data: {str(e)}"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def create_payment_authorization_session(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    try:
        data = json.loads(request.body)
        reservation_id = data.get("reservation_id")
        if not reservation_id:
            return JsonResponse({"error": "reservation_id is required"}, status=400)

        deposit_amount = int(data.get("deposit_amount", 10000))
        currency       = data.get("currency", "eur")
        authorize_now  = data.get("authorize_now", True)

        if authorize_now:
            # Autorisation immédiate
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": "Dépôt de garantie – Réservation",
                            "description": f"{deposit_amount/100:.2f}€ – Réservation #{reservation_id}",
                        },
                        "unit_amount": deposit_amount,
                    },
                    "quantity": 1,
                }],
                mode="payment",
                payment_intent_data={
                    "capture_method": "manual",
                    "description": f"Dépôt garantie #{reservation_id}",
                    "metadata": {
                        "type": "deposit_authorization",
                        "reservation_id": str(reservation_id),
                    }
                },
                success_url= f"https://safarelamir.com/confirmation?id={reservation_id}",
                cancel_url =f"https://safarelamir.com/",
                metadata={
                    "type": "deposit_authorization",
                    "reservation_id": str(reservation_id),
                    "deposit_amount": str(deposit_amount),
                }
            )
        else:
            # Simplement enregistrer la carte (setup) pour autoriser plus tard
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                mode="setup",
                setup_intent_data={
                    "metadata": {
                        "type": "deposit_payment_method",
                        "reservation_id": str(reservation_id),
                    }
                },
                success_url=f"https://safarelamir.com/setup-success?reservation_id={reservation_id}&session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url =f"https://safarelamir.com/setup-cancel?reservation_id={reservation_id}",
                metadata={
                    "type": "deposit_payment_method",
                    "reservation_id": str(reservation_id),
                }
            )

        return JsonResponse({
            "session_id": session.id,
            "url":        session.url,
            "authorize_now": authorize_now,
            "amount":     deposit_amount if authorize_now else None,
            "currency":   currency,
        }, status=200)

    except stripe.error.StripeError as e:
        return JsonResponse({"error": f"Stripe error: {str(e)}"}, status=400)
    except ValueError as e:
        return JsonResponse({"error": f"Invalid data: {str(e)}"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def capture_authorized_payment(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

        data = json.loads(request.body)
        payment_intent_id = data.get("payment_intent_id")
        amount_to_capture = data.get("amount_to_capture")  # Optionnel, capture le montant total si non spécifié
        
        if not payment_intent_id:
            return JsonResponse({"error": "payment_intent_id is required"}, status=400)
        
        capture_params = {}
        if amount_to_capture:
            capture_params["amount_to_capture"] = int(amount_to_capture)
        
        payment_intent = stripe.PaymentIntent.capture(
            payment_intent_id,
            **capture_params
        )
        
        return JsonResponse({
            "payment_intent_id": payment_intent.id,
            "status": payment_intent.status,
            "amount_captured": payment_intent.amount_received,
            "currency": payment_intent.currency
        }, status=200)
        
    except stripe.error.StripeError as e:
        return JsonResponse({"error": f"Stripe error: {str(e)}"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def cancel_authorized_payment(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

        data = json.loads(request.body)
        payment_intent_id = data.get("payment_intent_id")
        
        if not payment_intent_id:
            return JsonResponse({"error": "payment_intent_id is required"}, status=400)
        
        payment_intent = stripe.PaymentIntent.cancel(payment_intent_id)
        
        return JsonResponse({
            "payment_intent_id": payment_intent.id,
            "status": payment_intent.status,
            "canceled_at": payment_intent.canceled_at
        }, status=200)
        
    except stripe.error.StripeError as e:
        return JsonResponse({"error": f"Stripe error: {str(e)}"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
