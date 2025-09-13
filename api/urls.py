from django.urls import path
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register('apilieux', LieuxViewset, basename='lieux')
router.register('apicategory', CategorieViewset, basename='categorie')
router.register('apimodels', ModeleViewset, basename='modele')
router.register('apivehicls', VehiculeViewset, basename='vehicule')
router.register('apicategorieclient', CategorieClientViewset, basename='categorie_client')
router.register('apisoldeparrainage', SoldeParrainageViewset, basename='solde_parrainage')
router.register('apilisteclient', ListeClientViewset, basename='liste_client')
router.register('apisaison', SaisonViewset, basename='saison')
router.register('apiperiode', PeriodeViewset, basename='periode')
router.register('apinbjour', NombreDeJourViewset, basename='nb_jour')
router.register('apitarifs', TarifsViewset, basename='tarifs')
router.register('apioptions', OptionsViewset, basename='options')
router.register('apifraislivraison', FraisLivraisonViewset, basename='frais_livraison')
router.register('apisupplements', SupplementViewset, basename='supplements')
router.register('apipromotions', PromotionViewset, basename='promotion')
router.register('apireservations', ReservationViewset, basename='reservation')
router.register('apilivraison', LivraisonViewset, basename='livraison')
router.register('apichange', TauxChangeViewset, basename='taux_change')
router.register('apibookcar', BookCarViewset, basename='book_car')

urlpatterns = router.urls

urlpatterns += [
    path('search-vehicles/', search_vehicles, name='search_vehicles'),
    path('search-price/', search_price_view, name='search_price'),
    path('search-result/', search_result_view, name='search_result'),
    path('opt-send/', otp_send_client, name='search_or_create_client'),
    path('otp-verify/', otp_verify_client, name='otp_verify_client'),
    path('search-ma-reservation/', ma_reservation_view, name='ma_reservation'),
    path('verify-calculate-ma-reservation/', verify_and_calculate_view, name='ma_reservation'),
    path('verify-edit-ma-reservation/', verify_and_do_view, name='ma_reservation'),
    path('create-payment-link/', create_payment_link, name='create_payment_link'),
    path("create-payment-session/", create_payment_session, name="create_payment_session"),
    path("create-payment-session-protection/", create_payment_session_protection, name="create_payment_session_protection"),
    path("create-payment-session-reservation/", create_payment_session_reservation, name="create_payment_session_reservation"),
    path("create-payment-session-verify-calculate/", create_payment_session_verify_calculate, name="create_payment_session_verify_calculate"),
    path("create-payment-session-option/", create_payment_session_option, name="create_payment_session_option"),
    path("stripe-webhook/", stripe_webhook, name="stripe_webhook"),
    path("stripe-webhook-reservation/", stripe_webhook_reservation, name="stripe_webhook_reservation"),
    path("stripe-webhook-verfy-calculate/", stripe_webhook_verfy_calculate, name="stripe_webhook_verfy_calculate"),
    path('cancel-request/', cancel_request_view, name='cancel_request'),
    path('cancel-do/', cancel_do_view, name='cancel_do'),
    path('my-reservations/', mes_reservations_view, name='my_reservations'),
    path('add-options-request/', add_options_request_view, name='add_options_request'),
    path('add-options-put/', add_options_put_view, name='add_options_put'),
    path('new-models/', new_modeles_view, name='new_modeles'),
    path('post-reservation/', add_reservation_post_view, name='add_reservation_post'),
    path('client-verification/', verify_client_view, name='verify_client'),
    path('create-account/', create_account_view, name='create_account'),
    path('contact-messages/', create_contact_message, name='contact-message-create'),
    path('ajouter-liste-attente/', ajouter_liste_attente, name='ajouter_liste_attente'),
    path('categories/', get_all_categories, name='categories-list'),
    path('protection-request/', protection_request_view, name='protection-request-view'),
    path('protection-put/', protection_put_view, name='protection-put-view'),
    path('vip-reduction/', vip_reduction_view, name='vip_reduction_view'),
    path('homepage-promotion/', promotion_hompage, name='promotion_hompage'),
    path('news-letter/', create_news_letter, name='create_news_letter'),
    path('unsubscribe-news-letter/', unsubscribe_newsletter_view, name='unsubscribe_newsletter_view'),
    path('create-payment-authorization/',create_payment_authorization_session, name='create_payment_authorization'),
    path('capture-payment/',capture_authorized_payment, name='capture_payment'),
    path('cancel-authorization/',cancel_authorized_payment, name='cancel_authorization'),
    path('client-info/',client_info_view, name='client_info_view'),
    path('solde-history/',solde_history_view, name='solde_history_view'),
    path('comming-soon-email/',coming_soon_email_view, name='coming_soon_email_view'),
    path('livraison/<int:livraison_id>/photo/<int:attachment_id>/', livraison_photo_by_res, name='livraison_photo'),
    path('inspection-report/', success_pick_up_view, name='inspection_report'),
    path('signature/<int:livraison_id>/', get_signature_by_id, name='signature_by_id'),
    path("contract-download/", contract_download, name="contract_download"),
    path("success-pickup-email/", pick_up_mail_view, name="pick_up_mail_view"),
    path("restitution-email/", restitution_email_view, name="restitution_email_view"),
]
