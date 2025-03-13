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
endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
from django.utils import timezone
import time

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

def get_all_categories(request):
    categories = CategorieClient.objects.all() 

    categories_list = []
    
    for cat in categories:
        category_data = {
            "id": cat.id,
            "name": cat.name,
            "du_pts": cat.du_pts,
            "au_pts": cat.au_pts if cat.au_pts < 10000 else "+∞",
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


            name = str(random.randint(1000, 9999))

            create_date = datetime.now()


            ContactMessage.objects.create(
                name=name,
                nom_complet=nom_complet,
                email=email,
                message=message_text, 

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
        ccountry_code = request.META.get("HTTP_X_COUNTRY_CODE") 

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

        if not all([date_depart, heure_depart, date_retour, heure_retour]):
            return JsonResponse({"error": "les dates et les heures doivent être remplis."}, status=400)
        
        date_heure_debut = parse_datetime(f"{date_depart}T{heure_depart}")
        date_heure_fin = parse_datetime(f"{date_retour}T{heure_retour}")
        total_days = (date_heure_fin - date_heure_debut).days
        duree = f"{total_days} jours"

        if date_heure_debut and date_heure_fin:
            date_heure_debut_formate = date_heure_debut.strftime("%d/%m/%Y %H:%M")
            date_heure_fin_formate = date_heure_fin.strftime("%d/%m/%Y %H:%M")
            du_au_string = f"{date_heure_debut_formate} → {date_heure_fin_formate}"
        else :
            return JsonResponse({"error": "Les dates ou heures fournies sont invalides."}, status=400)

        if client_id :
            client = ListeClient.objects.filter(id=client_id).first()
            if client :
                client_solde = client.solde if client.solde else 0
                client_red_pr = client.categorie_client.reduction if client.categorie_client.reduction and client.categorie_client is not None else 0
            else :
                return JsonResponse({"error": "client non trouver."}, status=400)
        else:
            return JsonResponse({"error": "client non fournis."}, status=400)
        
        if lieu_depart and lieu_retour:
            depart = Lieux.objects.filter(id=lieu_depart).first()
            retour = Lieux.objects.filter(id=lieu_retour).first()
            depart_retour_string = f"{depart.name} → {retour.name}"
            if depart.zone != retour.zone:
                return JsonResponse({"error": "zone invalides."}, status=400) 
        
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
            promotion = Promotion.objects.filter(
                date_debut__lte=date_depart,
                date_fin__gte=date_retour,
                active_passive=True
            ).first()
            if promotion:
                zone_match = depart.zone in [promotion.zone_one, promotion.zone_two, promotion.zone_three]
                model_match = vehicule.modele in [
                    promotion.model_one, promotion.model_two, promotion.model_three, 
                    promotion.model_four, promotion.model_five
                ]

                # Vérification des conditions
                if promotion.tout_zone == "oui" and promotion.tout_modele == "oui":
                    promo_value = promotion.reduction
                elif zone_match and promotion.tout_modele == "oui":
                    promo_value = promotion.reduction
                elif model_match and promotion.tout_zone == "oui":
                    promo_value = promotion.reduction
                elif zone_match and model_match:
                    promo_value = promotion.reduction
                else:
                    promo_value = promotion.reduction
            tarif = Tarifs.objects.filter(
               ( Q(date_depart_one__lte=date_depart, date_fin_one__gte=date_retour) |
                Q(date_depart_two__lte=date_depart, date_fin_two__gte=date_retour) |
                Q(date_depart_three__lte=date_depart, date_fin_three__gte=date_retour) |
                Q(date_depart_four__lte=date_depart, date_fin_four__gte=date_retour)),
                Q(nbr_de__lte=total_days, nbr_au__gte=total_days),
                modele=vehicule.modele
            ).first()

            if tarif :
                prix_jour = tarif.prix
                total += prix_jour * total_days
                if client_red_pr and client_red_pr > 0 and client_red_pr > promo_value:
                    last_total = (100-client_red_pr) * total / 100
                elif promo_value > client_red_pr:
                    last_total = (100-promo_value) * total / 100
                else : 
                    last_total = total
                if client_solde > 0:
                    last_total = total - client_solde
                    client.solde = 0
                    client.solde_consomer += client_solde
                    client.solde_total += client_solde
                    client.save()
            else:
                return JsonResponse({"error": "tarifs invalides."}, status=400)
        else:
            return JsonResponse({"error": "vehucule invalides."}, status=400)
        
        
        
        frais_dossier = Options.objects.filter(option_code="FRAIS_DOSSIER").first()
        if frais_dossier:
            total += frais_dossier.prix * total_days if frais_dossier.type_option == "jour" else frais_dossier.prix
            last_total += frais_dossier.prix * total_days if frais_dossier.type_option == "jour" else frais_dossier.prix
            
        frais_livraison = FraisLivraison.objects.filter(depart=depart,retour=retour).first()
        if frais_livraison:
            total += frais_livraison.montant
            last_total += frais_livraison.montant
        
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
            total+= ecart_montant
            last_total+= ecart_montant
        
        prix_unitaire = total / total_days
        total_afficher = total
        total_afficher_red = last_total
        last_prix_unitaire = last_total / total_days
        free_options = free_options_f(client_id=client_id)
                            
        if opt_paiement == "yes" :
            if free_options and free_options[0].get("option_six") == True:
                paiement_anticipe = Options.objects.filter(option_code="P_ANTICIPE").first()
                opt_payment_name = paiement_anticipe.name
                opt_payment_unit = 0
                opt_payment_total = 0
                to_pay = prix_jour
                total_option += opt_payment_total
                total += opt_payment_total
                last_total += opt_payment_total
            else:
                paiement_anticipe = Options.objects.filter(option_code="P_ANTICIPE").first()
                opt_payment_name = paiement_anticipe.name
                opt_payment_unit = paiement_anticipe.prix
                opt_payment_total = paiement_anticipe.prix * total_days if paiement_anticipe.type_option =="jour" else paiement_anticipe.prix
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
        
        if opt_klm == "yes" :
            klm_a_illimite = Options.objects.filter(option_code="KLM_ILLIMITED").first()
            if free_options and free_options[0].get("option_seven") == True:
                opt_klm_a_name = klm_a_illimite.name
                opt_klm_a_unit = 0
                opt_klm_a_total = 0
                opt_klm_a_categorie = klm_a_illimite.categorie.id
            else :
                opt_klm_a_name = klm_a_illimite.name
                opt_klm_a_unit = klm_a_illimite.prix
                opt_klm_a_total = klm_a_illimite.prix * total_days if klm_a_illimite.type_tarif == "jour" else klm_a_illimite.prix
                opt_klm_a_categorie = klm_a_illimite.categorie.id

            if free_options and free_options[0].get("option_seven") == True:
                klm_illimite_b = Options.objects.filter(option_code="KLM_ILLIMITED_B").first()
                opt_klm_b_name = klm_illimite_b.name
                opt_klm_b_unit = 0
                opt_klm_b_total = 0
                opt_klm_b_categorie = klm_illimite_b.categorie.id
            else :
                klm_illimite_b = Options.objects.filter(option_code="KLM_ILLIMITED_B").first()
                opt_klm_b_name = klm_illimite_b.name
                opt_klm_b_unit = klm_illimite_b.prix
                opt_klm_b_total = klm_illimite_b.prix * total_days if klm_illimite_b.type_tarif == "jour" else klm_illimite_b.prix
                opt_klm_b_categorie = klm_illimite_b.categorie.id
            
            if free_options and free_options[0].get("option_seven") == True:
                klm_illimite_c = Options.objects.filter(option_code="KLM_ILLIMITED_C").first()
                opt_klm_c_name = klm_illimite_c.name
                opt_klm_c_unit = 0
                opt_klm_c_total = 0
                opt_klm_c_categorie = klm_illimite_c.categorie.id
            else :
                opt_klm_c_name = klm_illimite_c.name
                opt_klm_c_unit = klm_illimite_c.prix
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
            base_a = Options.objects.filter(option_code="BASE_P_1").first()
            base_a_name = base_a.name
            base_a_unit = base_a.prix
            base_a_total = base_a.prix * total_days if base_a.type_tarif == "jour" else base_a.prix
            base_a_category = base_a.categorie.id
            base_a_caution = base_a.caution
            base_b = Options.objects.filter(option_code="BASE_P_2").first()
            base_b_name = base_b.name
            base_b_unit = base_b.prix
            base_b_total = base_b.prix * total_days if base_b.type_tarif == "jour" else base_b.prix
            base_b_category = base_b.categorie.id
            base_b_caution = base_b.caution
            base_c = Options.objects.filter(option_code="BASE_P_3").first()
            base_c_name = base_c.name
            base_c_unit = base_c.prix
            base_c_total = base_c.prix * total_days if base_c.type_tarif == "jour" else base_c.prix
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
            standart_a = Options.objects.filter(option_code="STANDART_P_1").first()
            standart_a_name = standart_a.name
            standart_a_unit = standart_a.prix
            standart_a_total = standart_a.prix * total_days if standart_a.type_tarif == "jour" else standart_a.prix
            standart_a_caution = standart_a.caution

            standart_b = Options.objects.filter(option_code="STANDART_P_2").first()
            standart_b_name = standart_b.name
            standart_b_unit = standart_b.prix
            standart_b_total = standart_b.prix * total_days if standart_b.type_tarif == "jour" else standart_b.prix
            standart_b_caution = standart_b.caution
            
            standart_c = Options.objects.filter(option_code="STANDART_P_3").first()
            standart_c_name = standart_c.name
            standart_c_unit = standart_c.prix
            standart_c_total = standart_c.prix * total_days if standart_c.type_tarif == "jour" else standart_c.prix
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
                max_a = Options.objects.filter(option_code="MAX_P_1").first()
                max_a_name = max_a.name
                max_a_unit = max_a.prix
                max_a_total = max_a.prix * total_days if max_a.type_tarif == "jour" else max_a.prix
                max_a_caution = max_a.caution
            else : 
                max_a = Options.objects.filter(option_code="MAX_P_1").first()
                max_a_name = max_a.name
                max_a_unit = max_a.prix
                max_a_total = max_a.prix * total_days if max_a.type_tarif == "jour" else max_a.prix
                max_a_caution = max_a.caution
            
            if free_options and free_options[0].get("option_eight") == True:
                max_b = Options.objects.filter(option_code="MAX_P_2").first()
                max_b_name = max_b.name
                max_b_unit = 0
                max_b_total = 0
                max_b_caution = max_b.caution
            else :
                max_b = Options.objects.filter(option_code="MAX_P_2").first()
                max_b_name = max_b.name
                max_b_unit = max_b.prix
                max_b_total = max_b.prix * total_days if max_b.type_tarif == "jour" else max_b.prix
                max_b_caution = max_b.caution

            if free_options and free_options[0].get("option_eight") == True:
                max_c = Options.objects.filter(option_code="MAX_P_3").first()
                max_c_name = max_c.name
                max_c_unit = 0
                max_c_total = 0
                max_c_caution = max_c.caution
            else :
                max_c = Options.objects.filter(option_code="MAX_P_3").first()
                max_c_name = max_c.name
                max_c_unit = max_c.prix
                max_c_total = max_c.prix * total_days if max_c.type_tarif == "jour" else max_c.prix
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
                carburant = Options.objects.filter(option_code="P_CARBURANT").first()
                carburant_name = carburant.name
                carburant_unit = 0
                carburant_total = 0
                total += carburant_total
                last_total += carburant_total
                total_option += carburant_total
            else:
                carburant = Options.objects.filter(option_code="P_CARBURANT").first()
                carburant_name = carburant.name
                carburant_unit = carburant.prix
                carburant_total = carburant.prix * total_days if carburant.type_tarif == "jour" else carburant.prix
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
                sb_a = Options.objects.filter(option_code="S_BEBE_5").first()
                sb_a_name = sb_a.name
                sb_a_unit = 0
                sb_a_total = 0
                total += sb_a_total
                last_total += sb_a_total
                total_option += sb_a_total
            else :
                sb_a = Options.objects.filter(option_code="S_BEBE_5").first()
                sb_a_name = sb_a.name
                sb_a_unit = sb_a.prix
                sb_a_total = sb_a.prix * total_days if sb_a.type_tarif == "jour" else sb_a.prix
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
                sb_b = Options.objects.filter(option_code="S_BEBE_13").first()
                sb_b_name = sb_b.name
                sb_b_unit = 0
                sb_b_total = 0
                total += sb_b_total 
                last_total += sb_b_total
                total_option += sb_b_total
            else:
                sb_b = Options.objects.filter(option_code="S_BEBE_13").first()
                sb_b_name = sb_b.name
                sb_b_unit = sb_b.prix
                sb_b_total = sb_b.prix * total_days if sb_b.type_tarif == "jour" else sb_b.prix
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
                sb_c = Options.objects.filter(option_code="S_BEBE_18").first()
                sb_c_name = sb_c.name
                sb_c_unit = 0
                sb_c_total = 0
                total += sb_c_total
                last_total += sb_c_total
                total_option += sb_c_total
            else:
                sb_c = Options.objects.filter(option_code="S_BEBE_18").first()
                sb_c_name = sb_c.name
                sb_c_unit = sb_c.prix
                sb_c_total = sb_c.prix * total_days if sb_c.type_tarif == "jour" else sb_c.prix
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
                    nd_driver_opt = Options.objects.filter(option_code="ND_DRIVER").first()
                    nd_driver_opt_name = nd_driver_opt.name
                    nd_driver_opt_unit = 0
                    nd_driver_opt_total = 0
                    total += nd_driver_opt_total
                    last_total += nd_driver_opt_total
                    total_option += nd_driver_opt_total
                else:
                    nd_driver_opt = Options.objects.filter(option_code="ND_DRIVER").first()
                    nd_driver_opt_name = nd_driver_opt.name
                    nd_driver_opt_unit = nd_driver_opt.prix
                    nd_driver_opt_total = nd_driver_opt.prix * total_days if nd_driver_opt.type_tarif == "jour" else nd_driver_opt.prix
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
        

        reservation = Reservation.objects.create(
            create_date=timezone.now(),
            status="en_attend",
            etat_reservation="reserve",
            date_heure_debut = date_heure_debut ,
            date_heure_fin = date_heure_fin,
            du_au = du_au_string,
            nbr_jour_reservation = total_days,
            duree_dereservation = duree,
            lieu_depart = depart,
            zone = depart.zone,
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
            opt_klm_price = opt_klm_unit,
            opt_klm_total = opt_klm_total,
            opt_payment = paiement_anticipe,
            opt_payment_name = opt_payment_name,
            opt_payment_price = opt_payment_unit,
            opt_payment_total = opt_payment_total,
            opt_protection = protection,
            opt_protection_name = protection_name,
            opt_protection_caution= protection_caution,
            opt_protection_price=protection_unit,
            opt_protection_total=protection_total,
            opt_nd_driver=nd_driver_opt,
            opt_nd_driver_name=nd_driver_opt_name,
            opt_nd_driver_price=nd_driver_opt_unit,
            opt_nd_driver_total=nd_driver_opt_total,
            opt_plein_carburant=carburant,
            opt_plein_carburant_name=carburant_name,
            opt_plein_carburant_prix= carburant_unit,
            opt_plein_carburant_total=carburant_total,
            opt_siege_a = sb_a,
            opt_siege_a_name=sb_a_name,
            opt_siege_a_prix=sb_a_unit,
            opt_siege_a_total=sb_a_total,
            opt_siege_b = sb_b,
            opt_siege_b_name= sb_b_name,
            opt_siege_b_prix=sb_b_unit,
            opt_siege_b_total=sb_b_total,
            opt_siege_c=sb_c,
            opt_siege_c_prix=sb_c_unit,
            opt_siege_c_name=sb_c_name,
            opt_siege_c_total=sb_c_total,
            num_vol=num_vol,
            frais_de_dossier = frais_dossier.prix,
            prix_jour = prix_jour,
            nbr_jour_one = total_days,
            frais_de_livraison = frais_livraison.montant,
            supplements = supp_total ,
            retour_tard = ecart_montant,
            total_afficher = total_afficher,
            prix_jour_afficher = prix_unitaire,
            options_total = total_option,
            total = total ,
            reduction = client_red_pr,
            total_afficher_reduit = total_afficher_red,
            prix_jour_afficher_reduit = last_prix_unitaire,
            total_reduit = last_total,
            total_reduit_euro = last_total
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
                    "unit_amount": int(montant_a_paye * 100),
                    "quantity": 1,
                    "currency": "eur",
                    "reservation_id": reservation.id,
                    "montant_total":last_total,
                    "montant_paye":montant_a_paye

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
            success_url=f"https://safar-el-amir.vercel.app/confirmation?id={reservation_id}",
            cancel_url="https://safar-el-amir.vercel.app/cancel",
            metadata={
                "reservation_id": str(reservation_id),
                "montant_total": str(data.get("montant_total", 0)), 
                "montant_paye": str(data.get("montant_paye", 0))
            }
        )

        return JsonResponse({"session_id": checkout_session.id, "url": checkout_session.url}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def stripe_webhook_reservation(request):
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
        montant_total = session.get("metadata", {}).get("montant_total")
        montant_paye = session.get("metadata", {}).get("montant_paye")

        montant_total = float(montant_total) if montant_total else 0
        montant_paye = float(montant_paye) if montant_paye else 0

        reservation = Reservation.objects.filter(id=reservation_id).first()
        reservation.status ="confirmee"
        reservation.save()
        reservation.montant_paye = F('montant_paye') + montant_paye
        reservation.save(update_fields=['montant_paye'])
        reservation.refresh_from_db()

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

        html_message = render_to_string('email/confirmation_mail.html', {
            "referance":reservation.name,
            "adresse_one":reservation.lieu_depart.address,
            "adresse_two":reservation.lieu_retour.address,
            'client': reservation.client.nom,
            'client_prenom':reservation.client.prenom,
            'durrée':reservation.duree_dereservation,
            'model_name':reservation.model_name,
            'reste_paye':montant_total - montant_paye,
            'caution':reservation.opt_protection_caution,
            'date_depart':date_debut,
            'heure_depart':heure_debut,
            'date_retoure':date_fin,
            'haure_retour':heure_fin,
            'lieu_depart':reservation.lieu_depart.name,
            'lieu_retour':reservation.lieu_retour.name

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
        taux_change = Decimal(taux.montant) if taux else Decimal("1.00")  # Taux de change par défaut

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
        print(f"Paiement réussi pour la réservation ID: {reservation_id}")

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
            success_url= f"https://safar-el-amir.vercel.app/confirmation?id={reservation_id}",
            cancel_url="https://safar-el-amir.vercel.app/cancel",
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
                    klm_option = Options.objects.filter(name=klm_name,categorie=category).first()
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
                    nd_driver_option = Options.objects.filter(name=nd_driver_name).first()
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
                    carburant_option = Options.objects.filter(name=carburant_name).first()
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
                    sb_a_option = Options.objects.filter(name=sb_a_name).first()
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
                    sb_b_option = Options.objects.filter(name=sb_b_name).first()
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
                    sb_c_option = Options.objects.filter(name=sb_c_name).first()
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
            success_url= f"https://safar-el-amir.vercel.app/confirmation?id={reservation_id}",
            cancel_url="https://safar-el-amir.vercel.app/cancel",
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
    country_code = request.headers.get("X-Country-Code")

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
        country_code = request.headers.get("X-Country-Code")

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
