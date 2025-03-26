from rest_framework import serializers
from .models import *


class HistoriqueSoldeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoriqueSolde
        fields = "__all__"

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"

class ConditionAnnulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionAnnulation
        fields = "__all__"

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = "__all__"

class LieuxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lieux
        fields = "__all__"

class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = "__all__"


class ModeleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modele
        fields = "__all__"

class VehiculeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicule
        fields = "__all__"

class CategorieClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategorieClient
        fields = "__all__"

class SoldeParrainageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoldeParrainage
        fields = "__all__"

class ListeClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListeClient
        fields = "__all__"

class SaisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Saison
        fields = "__all__"

class PeriodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Periode
        fields = "__all__"


class NombreDeJourSerializer(serializers.ModelSerializer):
    class Meta:
        model = NombreDeJour
        fields = "__all__"

class TarifsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarifs
        fields = "__all__"

class OptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Options
        fields = "__all__"


class FraisLivraisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = FraisLivraison
        fields = "__all__"


class SupplementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplement
        fields = "__all__"


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = "__all__"



class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = "__all__"


class LivraisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Livraison
        fields = "__all__"


class TauxChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TauxChange
        fields = "__all__"


class BookCarSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookCar
        fields = "__all__"
    def validate_lieu_depart(self, value):
        if isinstance(value, int):  # Si un ID direct est envoyé
            try:
                return Lieux.objects.get(id=value)
            except Lieux.DoesNotExist:
                raise serializers.ValidationError("Lieu non trouvé.")
        return value