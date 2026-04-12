from rest_framework import serializers
from .models import *


class RefundTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundTable
        fields = "__all__"

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
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        request = self.context.get('request')
        country_code = request.headers.get('X-Country-Code') if request else None

        Taux = TauxChange.objects.get(id=2)
        change = Taux.montant
        
        if country_code == 'DZ':
            if representation.get('total_reduit_euro') is not None:
                representation['total_reduit_euro'] = float(representation['total_reduit_euro']) * float(change)
                representation['montant_paye'] = float(representation['montant_paye']) * float(change)
                representation['total_revenue'] = float(representation['total_revenue']) * float(change)
                representation['total_reduit'] = float(representation['total_reduit']) * float(change)
                representation['total'] = float(representation['total']) * float(change)
                representation['reste_payer'] = float(representation['reste_payer']) * float(change)

        
        return representation



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