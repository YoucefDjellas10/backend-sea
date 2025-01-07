from django.shortcuts import render
from django.http import HttpResponse
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
stripe.api_key = settings.STRIPE_SECRET_KEY

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
        heure_retour = data.get("heure_depart")
        vehicule_id = data.get("vehicule_id")
        opt_paiement = data.get("opt_paiement")
        opt_klm = data.get("opt_klm")
        opt_nd_driver = data.get("opt_nd_driver")
        opt_carburant = data.get("opt_carburant")
        opt_sb_a = data.get("opt_sb_a")
        opt_sb_b = data.get("opt_sb_b")
        opt_sb_c = data.get("opt_sb_c")
        client_id = data.get("client_id")
        nd_driver_id = data.get("nd_driver_id")
        num_vol = data.get("num_vol")

        if not all([lieu_depart, lieu_retour, date_depart, heure_depart, date_retour, heure_retour, vehicule_id, client_id]):
                    return JsonResponse({"error": "Tous les champs requis doivent être remplis."}, status=400)
        
        date_heure_debut = parse_datetime(f"{date_depart}T{heure_depart}")
        date_heure_fin = parse_datetime(f"{date_retour}T{heure_retour}")

        date_heure_debut_formate = date_heure_debut.strftime("%d/%m/%Y %H:%M")
        date_heure_fin_formate = date_heure_fin.strftime("%d/%m/%Y %H:%M")

        du_au_string = f"{date_heure_debut_formate} → {date_heure_fin_formate}"
        if not date_heure_debut or not date_heure_fin:
            return JsonResponse({"error": "Les dates ou heures fournies sont invalides."}, status=400)
        
        lieu_depart_id = Lieux.objects.filter(id=lieu_depart).first()
        lieu_retour_id = Lieux.objects.filter(id=lieu_retour).first()
        zone_id = Zone.objects.filter(id=lieu_depart_id.zone.id).first()
        lieu_depart_name = lieu_depart_id.name
        lieu_retour_name = lieu_retour_id.name
        depart_retour_name = f"{lieu_depart_name} → {lieu_retour_name}"
        
        vehicule = Vehicule.objects.filter(id=vehicule_id).first()
        client = ListeClient.objects.filter(id=client_id).first()

        if not vehicule or not client:
            return JsonResponse({"error": "Véhicule ou client introuvable."}, status=404)
        
        reservation = Reservation(
            lieu_depart=lieu_depart_id,
            lieu_retour=lieu_retour_id,
            depart_retour = depart_retour_name,
            zone=zone_id,
            date_heure_debut=date_heure_debut,
            date_heure_fin=date_heure_fin,
            du_au=du_au_string,
            vehicule=vehicule,
            modele=vehicule.modele,
            client=client,
            status="en_attend"
        )

        date_depart = datetime.strptime(date_depart, "%Y-%m-%d").date()
        date_retour = datetime.strptime(date_retour, "%Y-%m-%d").date()
                                
        total_days = (date_retour - date_depart).days
        opt_paiement_total = 0
        option_klm_total = 0
        option_nd_driver_total = 0
        option_carburant_total = 0
        option_sb_a_total = 0
        option_sb_b_total = 0
        option_sb_c_total = 0

        if opt_paiement == "yes":
            option_paiement = Options.objects.filter(option_code="P_ANTICIPE").first()
            if option_paiement:
                reservation.opt_payment = option_paiement
                if option_paiement.type_tarif == "fixe":
                    opt_paiement_total = option_paiement.prix 
                elif option_paiement.type_tarif == "jour":
                    opt_paiement_total = option_paiement.prix * total_days
                else : 
                    opt_paiement_total = 0
        
        if opt_klm == "yes":
            option_klm = Options.objects.filter(option_code="KLM_ILLIMITED").first()
            if option_klm:
                reservation.opt_klm = option_klm
                if option_klm.type_tarif == "fixe":
                    option_klm_total = option_klm.prix 
                elif option_klm.type_tarif == "jour":
                    option_klm_total = option_klm.prix * total_days
                else : 
                    option_klm_total = 0
        
        if opt_nd_driver == "yes":
            option_nd_driver = Options.objects.filter(option_code="ND_DRIVER").first()
            if option_nd_driver:
                reservation.opt_nd_driver = option_nd_driver
                if option_nd_driver.type_tarif == "fixe":
                    option_nd_driver_total = option_nd_driver.prix 
                elif option_nd_driver.type_tarif == "jour":
                    option_nd_driver_total = option_nd_driver.prix * total_days
                else : 
                    option_nd_driver_total = 0
        
        if opt_carburant == "yes":
            option_carburant = Options.objects.filter(option_code="P_CARBURANT").first()
            if option_carburant:
                reservation.opt_plein_carburant = option_carburant 
                if option_carburant.type_tarif == "fixe":
                    option_carburant_total = option_carburant.prix 
                elif option_carburant.type_tarif == "jour":
                    option_carburant_total = option_carburant.prix * total_days
                else : 
                    option_carburant_total = 0
                
        if opt_sb_a == "yes":
            option_sb_a = Options.objects.filter(option_code="S_BEBE_5s").first()
            if option_sb_a:
                reservation.opt_siege_a = option_sb_a
                if option_sb_a.type_tarif == "fixe":
                    option_sb_a_total = option_sb_a.prix 
                elif option_sb_a.type_tarif == "jour":
                    option_sb_a_total = option_sb_a.prix * total_days
                else : 
                    option_sb_a_total = 0

        if opt_sb_b == "yes":
            option_sb_b = Options.objects.filter(option_code="S_BEBE_13").first()
            if option_sb_b:
                reservation.opt_siege_b = option_sb_b
                if option_sb_b.type_tarif == "fixe":
                    option_sb_b_total = option_sb_b.prix 
                elif option_sb_b.type_tarif == "jour":
                    option_sb_b_total = option_sb_b.prix * total_days
                else : 
                    option_sb_b_total = 0

        if opt_sb_c == "yes":
            option_sb_c = Options.objects.filter(option_code="S_BEBE_18").first()
            if option_sb_c:
                reservation.opt_siege_c = option_sb_c
                if option_sb_c.type_tarif == "fixe":
                    option_sb_c_total = option_sb_c.prix 
                elif option_sb_c.type_tarif == "jour":
                    option_sb_c_total = option_sb_c.prix * total_days
                else : 
                    option_sb_c_total = 0

        if num_vol :
            reservation.num_vol = num_vol

        tarifs = Tarifs.objects.filter(
                    Q(modele = vehicule.modele)&
                    Q(nbr_de__lte=total_days) & Q(nbr_au__gte=total_days) & (
                        Q(date_depart_one__lte=date_depart, date_fin_one__gte=date_retour) |
                        Q(date_depart_two__lte=date_depart, date_fin_two__gte=date_retour) |
                        Q(date_depart_three__lte=date_depart, date_fin_three__gte=date_retour) |
                        Q(date_depart_four__lte=date_depart, date_fin_four__gte=date_retour)
                    )
                ) 
        total = 0
        prix_unitaire = 0 
        
        for tarif in tarifs:
                     
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

        total += option_klm_total + option_sb_a_total + option_sb_b_total + option_sb_c_total + opt_paiement_total + option_carburant_total + option_nd_driver_total
                    
        reservation.total_reduit_euro = total
        reservation.save()

        request_factory = RequestFactory()
        fake_request = request_factory.post(
            path="/create-payment-link/",
            data=json.dumps({
                "product_name": reservation.name,
                "description": "test",
                "images": [vehicule.photo_link] if vehicule.photo_link else [],
                "unit_amount": int(total * 100), 
                "quantity": 1,
                "currency": "eur"
            }),
            content_type="application/json"
        )

        payment_link_response = create_payment_link(fake_request)

        if payment_link_response.status_code == 200:
            payment_link_data = json.loads(payment_link_response.content)
            payment_url = payment_link_data.get("url", "")
            return JsonResponse({"message": "Réservation créée avec succès.", "reservation_id": reservation.id, "payment_link": payment_url}, status=201)
        else:
            return JsonResponse({"error": "Échec de la création du lien de paiement.", "response": payment_link_response.content.decode('utf-8')}, status=500)
                
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Données JSON invalides."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

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
            success_url="http://localhost:5173/confirmation?id=8",
            cancel_url="http://localhost:5173/cancel",
        )

        return JsonResponse({"session_id": checkout_session.id, "url": checkout_session.url}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
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
        print(request.body)
        data = json.loads(request.body)
        ref = data.get("ref")
        nd_driver = data.get("nd_driver")
        carburant = data.get("carburant")
        sb_a = data.get("sb_a")
        sb_b = data.get("sb_b")
        sb_c = data.get("rsb_cef")

        if not ref:
            return JsonResponse({"error": "Le champ 'ref' est requis."}, status=400)
        reservation = Reservation.objects.filter(name=ref).first()
        if not reservation:
            return JsonResponse({"error": "Réservation non trouvée avec la référence spécifiée."}, status=404)
        
        if nd_driver == "yes" and not reservation.opt_nd_driver_name:
            tarif_nd = Options.objects.filter(option_code="ND_DRIVER").first()
            reservation.opt_nd_driver = tarif_nd
    
        if carburant == "yes" and not reservation.opt_plein_carburant_name:  
            tarif_carburant = Options.objects.filter(option_code="P_CARBURANT").first()
            reservation.opt_plein_carburant = tarif_carburant
              
        if sb_a == "yes" and not reservation.opt_siege_a_name:  
            tarif_sb_a = Options.objects.filter(option_code="S_BEBE_5").first()
            reservation.opt_siege_a = tarif_sb_a
 
        if sb_b == "yes" and not reservation.opt_siege_b_name:  
            tarif_sb_b = Options.objects.filter(option_code="S_BEBE_13").first()
            reservation.opt_siege_b = tarif_sb_b

        if sb_c == "yes" and not reservation.opt_siege_c_name:  
            tarif_sb_c = Options.objects.filter(option_code="S_BEBE_18").first()  
            reservation.opt_siege_c = tarif_sb_c  

        if nd_driver == "no" and reservation.opt_nd_driver_name:
            reservation.opt_nd_driver = None
    
        if carburant == "no" and reservation.opt_plein_carburant_name:  
            reservation.opt_plein_carburant = None
              
        if sb_a == "no" and reservation.opt_siege_a_name:  
            reservation.opt_siege_a = None
 
        if sb_b == "no" and reservation.opt_siege_b_name:  
            reservation.opt_siege_b = None

        if sb_c == "no" and reservation.opt_siege_c_name:  
            reservation.opt_siege_c = None      
    
        reservation.save()

        return JsonResponse({"message": "Modification effectuée avec succès."}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Données JSON invalides."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def add_options_request_view(request):  
    ref = request.GET.get("ref")
    nd_driver = request.GET.get("nd_driver")
    carburant = request.GET.get("ref")
    sb_a = request.GET.get("sb_a")
    sb_b = request.GET.get("sb_b")
    sb_c = request.GET.get("sb_c")
        
    if not ref or not nd_driver or not carburant or not sb_a or not sb_b or not sb_c:
        return JsonResponse({"error": "Tout les parametres sont requis."}, status=400)
    
    try:
        resultats = add_options_request(
            ref=ref,
            nd_driver=nd_driver,
            carburant=carburant,
            sb_a=sb_a,
            sb_b=sb_b,
            sb_c=sb_c,
        )
        return JsonResponse({"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})



def mes_reservations_view(request):  
    client_id = request.GET.get("client_id")
        
    if not client_id :
        return JsonResponse({"error": "Le paramètres 'client_id' est requis."}, status=400)
    
    try:
        resultats = mes_reservations(
            client_id=client_id,
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
        if not ref:
            return JsonResponse({"error": "Le champ 'ref' est requis."}, status=400)
        
        if not reason:
            return JsonResponse({"error": "Le champ 'reason' est requis."}, status=400)
        
        annuler_raison = AnnulerRaison.objects.filter(name=reason).first()  
        reservation = Reservation.objects.filter(name=ref).first()
        if not reservation:
            return JsonResponse({"error": "Réservation non trouvée avec la référence spécifiée."}, status=404)
        reservation.status = "annule"
        reservation.etat_reservation = "annule"
        reservation.annuler_raison = annuler_raison
        reservation.save()

        return JsonResponse({"message": "Modification effectuée avec succès."}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Données JSON invalides."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def cancel_request_view(request):  
    ref = request.GET.get("ref")
        
    if not ref :
        return JsonResponse({"error": "Le paramètres 'ref' est requis."}, status=400)
    
    try:
        resultats = cencel_request(
            ref=ref,
        )
        return JsonResponse({"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})

def verify_and_verify_view(request):  
    ref = request.GET.get("ref")
    lieu_depart = request.GET.get("lieu_depart")
    lieu_retour = request.GET.get("lieu_retour")
    date_depart = request.GET.get("date_depart")
    heure_depart = request.GET.get("heure_depart")
    date_retour = request.GET.get("date_retour")
    heure_retour = request.GET.get("heure_retour")
        
    if not date_retour or not date_depart:
        return JsonResponse({"error": "Les paramètres 'date_retour' et 'date_depart' sont requis."}, status=400)
    
    try:
        resultats = verify_and_edit(
            ref=ref,
            lieu_depart = lieu_depart,
            lieu_retour = lieu_retour,
            date_depart = date_depart,
            heure_depart = heure_depart,
            date_retour = date_retour,
            heure_retour = heure_retour,
        )
        return JsonResponse({"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})


def verify_and_calculate_view(request):  
    ref = request.GET.get("ref")
    lieu_depart = request.GET.get("lieu_depart")
    lieu_retour = request.GET.get("lieu_retour")
    date_depart = request.GET.get("date_depart")
    heure_depart = request.GET.get("heure_depart")
    date_retour = request.GET.get("date_retour")
    heure_retour = request.GET.get("heure_retour")
        
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
        )
        return JsonResponse({"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})



def ma_reservation_view(request):
    ref = request.GET.get("ref")
    email = request.GET.get("email")
        
    if not ref or not email:
        return JsonResponse({"error": "Les paramètres 'ref' et 'email' sont requis."}, status=400)
    
    try:
        resultats = ma_reservation_detail(
            ref=ref,
            email=email,
        )
        return JsonResponse({"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})



def otp_send_client(request):
    if request.method == "GET":  
        try:
            email = request.GET.get("email")

            if not email :
                return JsonResponse({"success": False, "message": "Tous les champs (email, nom, prénom) sont requis."})

            result = otp_send(email)
            return JsonResponse({"success": True, "message": result["message"], "client_id": result["client_id"]})

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Erreur: {str(e)}"})

    return JsonResponse({"success": False, "message": "Méthode non autorisée. Utilisez GET."})

def search_result_view(request):
    lieu_depart_id = request.GET.get("lieu_depart_id")
    lieu_retour_id = request.GET.get("lieu_retour_id")
    date_depart = request.GET.get("date_depart")
    heure_depart = request.GET.get("heure_depart")
    date_retour = request.GET.get("date_retour")
    heure_retour = request.GET.get("heure_retour")
    
    if not date_depart or not date_retour:
        return JsonResponse({"error": "Les paramètres 'date_depart' et 'date_retour' sont requis."}, status=400)
    
    try:
        resultats = search_result(
            lieu_depart_id=int(lieu_depart_id),
            lieu_retour_id=int(lieu_retour_id),
            date_depart=date_depart,
            heure_depart=heure_depart,
            date_retour=date_retour,
            heure_retour=heure_retour,
        )
        return JsonResponse({"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})



def search_price_view(request):
    # Récupérer les paramètres GET
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



