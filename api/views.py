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
import json
from decimal import Decimal
from rest_framework.decorators import api_view
from rest_framework import status
stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
@require_http_methods(["PUT"])
def protection_put_view(request):
    try:
        print(request.body)
        data = json.loads(request.body)
        ref = data.get("ref")
        protection = data.get("protection")

        try:
            resultats = modify_protection_request(
                ref=ref,
                protection=protection,
            )
            reservation = Reservation.objects.filter(name=ref).first()

            to_pay_value = resultats.get("to_pay")

            if to_pay_value is not None:
                request_factory = RequestFactory()
                fake_request = request_factory.post(
                    path="/create-payment-session/",
                    data=json.dumps({
                        "product_name": reservation.name,
                        "description": "test",
                        "images": [reservation.photo_link] if reservation.photo_link else [],
                        "unit_amount": int(to_pay_value * 100),
                        "quantity": 1,
                        "currency": "eur",
                        "reservation_id": reservation.id
                    }),
                    content_type="application/json"
                )

                payment_session_response = create_payment_session(fake_request)

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
    
def protection_request_view(request):

    ref = request.GET.get("ref")
    protection = request.GET.get("protection")

    if not ref or not protection:
        return JsonResponse({"error": "Les paramètres 'ref' et 'protection' sont requis."}, status=400)

    try:
        resultats = modify_protection_request(
            ref=ref,
            protection=protection,
        )
        return JsonResponse({"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params={"ensure_ascii": False})

def disponibilite_view(request):
    lieu_depart_id = request.GET.get("lieu_depart_id")
    lieu_retour_id = request.GET.get("lieu_retour_id")
    date_depart = request.GET.get("date_depart")
    heure_depart = request.GET.get("heure_depart")
    date_retour = request.GET.get("date_retour")
    heure_retour = request.GET.get("heure_retour")
    client_id = request.GET.get("client_id")
    prime_code = request.GET.get("prime_code")
    country_code = request.GET.get("country_code")

    if not date_depart or not date_retour:
        return JsonResponse({"error": "Les paramètres 'date_depart' et 'date_retour' sont requis."}, status=400)

    try:
        resultats = disponibilite_resultat(
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
            "du_pts": cat.du_pts,
            "au_pts": cat.au_pts,
            "reduction": cat.reduction,
        }

        options = {
            "option_one": cat.option_one.name if cat.option_one else None,
            "option_two": cat.option_two.name if cat.option_two else None,
            "option_three": cat.option_three.name if cat.option_three else None,
            "option_four": cat.option_four.name if cat.option_four else None,
            "option_five": cat.option_five.name if cat.option_five else None,
            "option_six": cat.option_six.name if cat.option_six else None,
            "option_seven": cat.option_seven.name if cat.option_seven else None,
            "option_eight": cat.option_eight.name if cat.option_eight else None,
            "option_nine": cat.option_nine.name if cat.option_nine else None,
            "option_ten": cat.option_ten.name if cat.option_ten else None,
        }

        options = {key: value for key, value in options.items() if value is not None}

        category_data.update(options)

        categories_list.append(category_data)

    return JsonResponse({"categories": categories_list}, safe=False)

@csrf_exempt
def ajouter_liste_attente(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            client_id = data.get('client_id')
            try:
                client = ListeClient.objects.get(id=client_id)
            except ObjectDoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Client non trouvé'}, status=404)

            car_model_id = data.get('car_model_id')
            lieu_depart_id = data.get('lieu_depart_id')
            lieu_retour_id = data.get('lieu_retour_id')
            date_depart = data.get('date_depart')
            date_retour = data.get('date_retour')
            heure_debut = data.get('heure_debut')
            heure_fin = data.get('heure_fin')

            try:
                car_model = Modele.objects.get(id=car_model_id)
                lieu_depart = Lieux.objects.get(id=lieu_depart_id)
                lieu_retour = Lieux.objects.get(id=lieu_retour_id)
            except ObjectDoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Modèle ou lieu non trouvé'}, status=404)

            nouvelle_liste_attente = ListeAttente(
                name=data.get('name', 'Nouvelle liste d\'attente'),
                client=client,
                full_name=f"{client.nom} {client.prenom}",
                email=client.email,
                phone_number=client.telephone,
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

@api_view(['POST'])
def create_contact_message(request):
    if request.method == 'POST':
        try:
            nom_complet = request.data.get('nom_complet')
            email = request.data.get('email')
            message_text = request.data.get('message') 
            client_id = request.data.get('client')

            if not client_id :
                client_id = 0

            name = str(random.randint(1000, 9999))

            create_date = datetime.now()

            client = None
            if client_id:
                client = ListeClient.objects.filter(id=client_id).first()

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


def verify_and_edit(ref, lieu_depart, lieu_retour, date_depart, heure_depart, date_retour, heure_retour):
    try:
        ma_reservation = Reservation.objects.filter(name=ref).first()
        if not ma_reservation:
            return {"message": "Réservation non trouvée."}
        date_depart_heure = datetime.strptime(f"{date_depart} {heure_depart}", '%Y-%m-%d %H:%M')
        date_retour_heure = datetime.strptime(f"{date_retour} {heure_retour}", '%Y-%m-%d %H:%M')
        verify_value = verify_and_calculate(
            ref,
            lieu_depart,
            lieu_retour,
            date_depart,
            heure_depart,
            date_retour,
            heure_retour
        )
        if verify_value and verify_value[0].get('is_available') == "yes":
            old_total = verify_value[0].get('old_total')
            new_total = verify_value[0].get('new_total')
            to_pay = Decimal(new_total) - Decimal(old_total)
            if to_pay < 0 :
                
                lieu_depart_obj = get_object_or_404(Lieux, id=lieu_depart)
                lieu_retour_obj = get_object_or_404(Lieux, id=lieu_retour)
                
                ma_reservation.lieu_depart = lieu_depart_obj
                ma_reservation.lieu_retour = lieu_retour_obj
                ma_reservation.date_heure_debut = date_depart_heure
                ma_reservation.date_heure_fin = date_retour_heure
                ma_reservation.save()

                return {"modified":"yes","message": "Réservation mise à jour avec succès.", "refund_message": True}

            if to_pay == 0 :
                
                lieu_depart_obj = get_object_or_404(Lieux, id=lieu_depart)
                lieu_retour_obj = get_object_or_404(Lieux, id=lieu_retour)
                
                ma_reservation.lieu_depart = lieu_depart_obj
                ma_reservation.lieu_retour = lieu_retour_obj
                ma_reservation.date_heure_debut = date_depart_heure
                ma_reservation.date_heure_fin = date_retour_heure
                ma_reservation.save()

                return {"modified":"yes","message": "Réservation mise à jour avec succès."}
            
            if to_pay > 0 and not ma_reservation.opt_payment_name:
                
                lieu_depart_obj = get_object_or_404(Lieux, id=lieu_depart)
                lieu_retour_obj = get_object_or_404(Lieux, id=lieu_retour)


                return {"modified":"yes","message": "Réservation mise à jour avec succès."}


            if to_pay > 0 and ma_reservation.opt_payment_name: 
                request_factory = RequestFactory()
                fake_request = request_factory.post(
                    path="/create-payment-session/",
                    data=json.dumps({
                        "product_name": ma_reservation.name,
                        "description": "test",
                        "images": [ma_reservation.photo_link] if ma_reservation.photo_link else [],
                        "unit_amount": int(to_pay * 100),
                        "quantity": 1,
                        "currency": "eur",
                        "reservation_id": ma_reservation.id

                    }),
                    content_type="application/json"
                )

                payment_session_response = create_payment_session(fake_request)

                if payment_session_response.status_code != 200:
                    return {"message": "Erreur lors de la création de la session de paiement."}

                if payment_session_response.status_code == 200:
                    payment_session_data = json.loads(payment_session_response.content)
                    session_id = payment_session_data.get("session_id", "")
                    payment_url = payment_session_data.get("url", "")


                lieu_depart_obj = get_object_or_404(Lieux, id=lieu_depart)
                lieu_retour_obj = get_object_or_404(Lieux, id=lieu_retour)
                
                ma_reservation.lieu_depart = lieu_depart_obj
                ma_reservation.lieu_retour = lieu_retour_obj
                ma_reservation.date_heure_debut = date_depart_heure
                ma_reservation.date_heure_fin = date_retour_heure
                ma_reservation.save()

                return {"modified":"yes","message": "Réservation mise à jour avec succès.", "session_id": session_id, "payment_url": payment_url}
        else:
            return {"modified":"no","message": "Les modifications ne peuvent pas être effectuées : véhicule non disponible."}
    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}
    except Exception as e:
        return {"message": f"Erreur: {str(e)}"}


def verify_and_do_view(request):
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
        opt_protection = data.get("opt_protection")
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
        client_nom = client.nom
        client_prenom = client.prenom
        client_date_permis = client.date_de_permis
        client_date_naissance = client.date_de_naissance
        client_mobil = client.mobile
        client_phone = client.telephone
        client_email = client.email
        client_risque = client.risque
        client_prime = client.code_prime

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
            nom=client_nom,
            prenom=client_prenom,
            date_de_naissance=client_date_naissance,
            email=client_email,
            risque=client_risque,
            code_prime=client_prime,
            mobile=client_mobil,
            telephone=client_phone,
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
                reservation.opt_payment_name = option_paiement.name
                reservation.opt_payment_price = option_paiement.prix
                if option_paiement.type_tarif == "fixe":
                    opt_paiement_total = option_paiement.prix
                    reservation.opt_payment_total = opt_paiement_total
                elif option_paiement.type_tarif == "jour":
                    opt_paiement_total = option_paiement.prix * total_days
                    reservation.opt_payment_total = opt_paiement_total
                else :
                    opt_paiement_total = 0

        if opt_klm == "yes":
            option_klm = Options.objects.filter(option_code="KLM_ILLIMITED").first()
            if option_klm:
                reservation.opt_klm = option_klm
                reservation.opt_klm_name = option_klm.name
                reservation.opt_klm_price = option_klm.prix
                reservation.opt_kilometrage = option_klm.limit_Klm * total_days
                if option_klm.type_tarif == "fixe":
                    option_klm_total = option_klm.prix
                    reservation.opt_klm_total = option_klm_total
                elif option_klm.type_tarif == "jour":
                    option_klm_total = option_klm.prix * total_days
                    reservation.opt_klm_total = option_klm_total
                else :
                    option_klm_total = 0

        if opt_protection == "basic":
            option_basic = Options.objects.filter(option_code="ND_DRIVER").first()


        if opt_nd_driver == "yes":
            option_nd_driver = Options.objects.filter(option_code="ND_DRIVER").first()
            client_nd = ListeClient.objects.filter(id=nd_driver_id).first()
            client_nd_nom = client_nd.nom
            client_nd_prenom = client_nd.prenom
            client_nd_date_permis = client_nd.date_de_permis
            client_nd_date_naissance = client_nd.date_de_naissance
            client_nd_email = client_nd.email
            client_nd_risque = client_nd.risque
            reservation.nom_nd_condicteur = client_nd_nom
            reservation.prenom_nd_condicteur = client_nd_prenom
            reservation.email_nd_condicteur = client_nd_email
            reservation.date_nd_condicteur = client_nd_date_naissance
            reservation.date_de_permis = client_nd_date_permis

            if option_nd_driver:
                reservation.opt_nd_driver = option_nd_driver
                reservation.opt_nd_driver_name = option_nd_driver.name
                reservation.opt_nd_driver_price = option_nd_driver.prix
                if option_nd_driver.type_tarif == "fixe":
                    option_nd_driver_total = option_nd_driver.prix
                    reservation.opt_nd_driver_total = option_nd_driver_total
                elif option_nd_driver.type_tarif == "jour":
                    option_nd_driver_total = option_nd_driver.prix * total_days
                    reservation.opt_nd_driver_total = option_nd_driver_total
                else :
                    option_nd_driver_total = 0

        if opt_carburant == "yes":
            option_carburant = Options.objects.filter(option_code="P_CARBURANT").first()
            if option_carburant:
                reservation.opt_plein_carburant = option_carburant
                reservation.opt_plein_carburant_name = option_carburant.name
                reservation.opt_plein_carburant_prix = option_carburant.prix
                if option_carburant.type_tarif == "fixe":
                    option_carburant_total = option_carburant.prix
                    reservation.opt_plein_carburant_total = option_carburant_total
                elif option_carburant.type_tarif == "jour":
                    option_carburant_total = option_carburant.prix * total_days
                    reservation.opt_plein_carburant_total = option_carburant_total
                else :
                    option_carburant_total = 0

        if opt_sb_a == "yes":
            option_sb_a = Options.objects.filter(option_code="S_BEBE_5").first()
            if option_sb_a:
                reservation.opt_siege_a = option_sb_a
                reservation.opt_siege_a_name = option_sb_a.name
                reservation.opt_siege_a_prix = option_sb_a.prix
                if option_sb_a.type_tarif == "fixe":
                    option_sb_a_total = option_sb_a.prix
                    reservation.opt_siege_a_total = option_sb_a_total
                elif option_sb_a.type_tarif == "jour":
                    option_sb_a_total = option_sb_a.prix * total_days
                    reservation.opt_siege_a_total = option_sb_a_total
                else :
                    option_sb_a_total = 0

        if opt_sb_b == "yes":
            option_sb_b = Options.objects.filter(option_code="S_BEBE_13").first()
            if option_sb_b:
                reservation.opt_siege_b = option_sb_b
                reservation.opt_siege_b_name = option_sb_b.name
                reservation.opt_siege_b_prix = option_sb_b.prix
                if option_sb_b.type_tarif == "fixe":
                    option_sb_b_total = option_sb_b.prix
                    reservation.opt_siege_b_total = option_sb_b_total
                elif option_sb_b.type_tarif == "jour":
                    option_sb_b_total = option_sb_b.prix * total_days
                    reservation.opt_siege_b_total = option_sb_b_total
                else :
                    option_sb_b_total = 0

        if opt_sb_c == "yes":
            option_sb_c = Options.objects.filter(option_code="S_BEBE_18").first()
            if option_sb_c:
                reservation.opt_siege_c = option_sb_c
                reservation.opt_siege_c_name = option_sb_c.name
                reservation.opt_siege_c_prix = option_sb_c.prix
                if option_sb_c.type_tarif == "fixe":
                    option_sb_c_total = option_sb_c.prix
                    reservation.opt_siege_c_total = option_sb_c_total
                elif option_sb_c.type_tarif == "jour":
                    option_sb_c_total = option_sb_c.prix * total_days
                    reservation.opt_siege_c_total = option_sb_c_total
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
            path="/create-payment-session/",
            data=json.dumps({
                "product_name": reservation.name,
                "description": "test",
                "images": [vehicule.photo_link] if vehicule.photo_link else [],
                "unit_amount": int(total * 100),
                "quantity": 1,
                "currency": "eur",
                "reservation_id": reservation.id

            }),
            content_type="application/json"
        )

        payment_session_response = create_payment_session(fake_request)

        if payment_session_response.status_code == 200:
            payment_session_data = json.loads(payment_session_response.content)
            session_id = payment_session_data.get("session_id", "")
            payment_url = payment_session_data.get("url", "")
            return JsonResponse({"message": "Réservation créée avec succès.", "reservation_id": reservation.id, "session_id": session_id, "payment_url": payment_url}, status=201)
        else:
            return JsonResponse({"error": "Échec de la création de la session de paiement.", "response": payment_session_response.content.decode('utf-8')}, status=500)


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
            success_url= f"https://safar-el-amir.vercel.app/confirmation?id={reservation_id}",
            cancel_url="https://safar-el-amir.vercel.app/cancel",
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
        jr = reservation.nbr_jour_reservation
        opt_total = reservation.options_total
        new_total = 0
        if not reservation:
            return JsonResponse({"error": "Réservation non trouvée avec la référence spécifiée."}, status=404)

        if nd_driver == "yes" and not reservation.opt_nd_driver_name:
            tarif_nd = Options.objects.filter(option_code="ND_DRIVER").first()
            reservation.opt_nd_driver = tarif_nd
            reservation.opt_nd_driver_name = tarif_nd.name
            reservation.opt_nd_driver_price = tarif_nd.prix
            if tarif_nd.type_tarif == "jour":
                reservation.opt_nd_driver_total = tarif_nd.prix * jr
                new_total += tarif_nd.prix * jr
            else :
                reservation.opt_nd_driver_total = tarif_nd.prix
                new_total += tarif_nd.prix
        else :
            reservation.opt_nd_driver = None
            reservation.opt_nd_driver_name = None
            reservation.opt_nd_driver_price = None
            reservation.opt_nd_driver_total = None

        if carburant == "yes" and not reservation.opt_plein_carburant_name:
            tarif_carburant = Options.objects.filter(option_code="P_CARBURANT").first()
            reservation.opt_plein_carburant = tarif_carburant
            reservation.opt_plein_carburant_name = tarif_carburant.name
            reservation.opt_plein_carburant_prix = tarif_carburant.prix
            if tarif_carburant.type_tarif == "jour":
                reservation.opt_plein_carburant_total = tarif_carburant.prix * jr
                new_total += tarif_carburant.prix * jr
            else :
                reservation.opt_plein_carburant_total = tarif_carburant.prix
                new_total += tarif_carburant.prix
        else :
            reservation.opt_plein_carburant = None
            reservation.opt_plein_carburant_name = None
            reservation.opt_plein_carburant_prix = None
            reservation.opt_plein_carburant_total = None

        if sb_a == "yes" and not reservation.opt_siege_a_name:
            tarif_sb_a = Options.objects.filter(option_code="S_BEBE_5").first()
            reservation.opt_siege_a = tarif_sb_a
            reservation.opt_siege_a_name = tarif_sb_a.name
            reservation.opt_siege_a_prix = tarif_sb_a.prix
            if tarif_sb_a.type_tarif == "jour":
                reservation.opt_siege_a_total = tarif_sb_a.prix * jr
                new_total +=  tarif_sb_a.prix * jr
            else :
                reservation.opt_siege_a_total = tarif_sb_a.prix
                new_total += tarif_sb_a.prix
        else :
            reservation.opt_siege_a = None
            reservation.opt_siege_a_name = None
            reservation.opt_siege_a_prix = None
            reservation.opt_siege_a_total = None

        if sb_b == "yes" and not reservation.opt_siege_b_name:
            tarif_sb_b = Options.objects.filter(option_code="S_BEBE_13").first()
            reservation.opt_siege_b = tarif_sb_b
            reservation.opt_siege_b_name = tarif_sb_b.name
            reservation.opt_siege_b_prix = tarif_sb_b.prix
            if tarif_sb_b.type_tarif == "jour":
                reservation.opt_siege_b_total = tarif_sb_b.prix * jr
                new_total += tarif_sb_b.prix * jr
            else :
                reservation.opt_siege_b_total = tarif_sb_b.prix
                new_total += tarif_sb_b.prix
        else :
            reservation.opt_siege_b = None
            reservation.opt_siege_b_name = None
            reservation.opt_siege_b_prix = None
            reservation.opt_siege_b_total = None

        if sb_c == "yes" and not reservation.opt_siege_c_name:
            tarif_sb_c = Options.objects.filter(option_code="S_BEBE_18").first()
            reservation.opt_siege_c = tarif_sb_c
            reservation.opt_siege_c_name = tarif_sb_c.name
            reservation.opt_siege_c_prix = tarif_sb_c.prix
            if tarif_sb_c.type_tarif == "jour":
                reservation.opt_siege_c_total = tarif_sb_c.prix * jr
                new_total += tarif_sb_c.prix
            else :
                reservation.opt_siege_c_total = tarif_sb_c.prix
                new_total += tarif_sb_c.prix
        else :
            reservation.opt_siege_c = None
            reservation.opt_siege_c_name = None
            reservation.opt_siege_c_prix = None
            reservation.opt_siege_c_total = None

        if (int(new_total) < int(opt_total) and not reservation.opt_payment_name) or (new_total == opt_total):
            reservation.save()
            return JsonResponse({"refund_message":False , "message": "Modification effectuée avec succès."}, status=200)

        elif int(new_total) < int(opt_total) and reservation.opt_payment_name:
            reservation.save()
            return JsonResponse({"refund_message":True,"message": "Modification effectuée avec succès."}, status=200)
        elif (int(new_total) > int(opt_total) and not reservation.opt_payment_name) or (new_total == opt_total):
            reservation.save()
            return JsonResponse({"refund_message":False , "message": "Modification effectuée avec succès."}, status=200)
        elif int(new_total) > int(opt_total) and reservation.opt_payment_name:
            diff = new_total - opt_total 
            request_factory = RequestFactory()
            fake_request = request_factory.post(
                path="/create-payment-session/",
                data=json.dumps({
                    "product_name": reservation.name,
                    "description": "test",
                    "images": [reservation.photo_link] if reservation.photo_link else [],
                    "unit_amount": int(diff * 100),
                    "quantity": 1,
                    "currency": "eur",
                    "reservation_id": reservation.id
                }),
                content_type="application/json"
            )
            payment_session_response = create_payment_session(fake_request)

            if payment_session_response.status_code != 200:
                return {"message": "Erreur lors de la création de la session de paiement."}

            if payment_session_response.status_code == 200:
                payment_session_data = json.loads(payment_session_response.content)
                session_id = payment_session_data.get("session_id", "")
                payment_url = payment_session_data.get("url", "")

            return JsonResponse({"refund_message":False , "message": "Modification effectuée avec succès.","session_id":session_id,"payment_url":payment_url}, status=200)
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Données JSON invalides."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def add_options_request_view(request):
    ref = request.GET.get("ref")
    nd_driver = request.GET.get("nd_driver")
    carburant = request.GET.get("carburant")
    sb_a = request.GET.get("sb_a")
    sb_b = request.GET.get("sb_b")
    sb_c = request.GET.get("sb_c")
    nom = request.GET.get("nom")
    prenom = request.GET.get("prenom")
    birthday = request.GET.get("birthday")
    permis_date = request.GET.get("permis_date")

    if not ref or not nd_driver or not carburant or not sb_a or not sb_b or not sb_c:
        return JsonResponse({"error": "Tout les parametres sont requis."}, status=400)
    if nd_driver == "yes" and (not nom or not prenom or not birthday or not permis_date):
        return JsonResponse({"error": "information client requis."}, status=400)

    try:
        resultats = add_options_request(
            ref=ref,
            nd_driver=nd_driver,
            carburant=carburant,
            sb_a=sb_a,
            sb_b=sb_b,
            sb_c=sb_c,
            nom=nom,
            prenom=prenom,
            birthday=birthday,
            permis_date=permis_date,
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
    country_code = request.GET.get("country_code")

    if not ref or not email:
        return JsonResponse({"error": "Les paramètres 'ref' et 'email' sont requis."}, status=400)

    try:
        resultats = ma_reservation_detail(
            ref=ref,
            email=email,
            country_code=country_code
        )
        protection = protections(ref=ref, country_code=country_code)
        options = option_ma_reservation(ref=ref , country_code=country_code)
        return JsonResponse({"protections":protection,"options": options ,"results": resultats}, status=200, json_dumps_params={"ensure_ascii": False})
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
        country_code = request.headers.get("country_code")

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




