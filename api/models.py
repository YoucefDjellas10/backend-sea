from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import random
import string
from datetime import date,datetime, timedelta

class IrAttachment(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True)
    mimetype = models.CharField(max_length=255, null=True)
    #datas = models.TextField(null=True)        # base64 text souvent
    store_fname = models.CharField(max_length=255, null=True)
    res_model = models.CharField(max_length=255, null=True)
    res_id = models.BigIntegerField(null=True)

    class Meta:
        db_table = 'ir_attachment'
        managed = False

class LivraisonIrAttachmentRel(models.Model):
    livraison_id = models.BigIntegerField()
    ir_attachment_id = models.BigIntegerField(primary_key=True)

    class Meta:
        db_table = 'ir_attachment_livraison_rel'
        managed = False
        unique_together = (('livraison_id', 'ir_attachment_id'),)

class TauxChange(models.Model):

    name = models.CharField(
        max_length=255,
        default='Devise €',
        verbose_name=_("Nom"),
        editable=False
    )

    montant = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Montant (DZD)")
    )
    primaire = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=1,
        null=True,
        blank=True,
        verbose_name=_("Montant (Devise)")
    )

    class Meta:
        db_table = 'taux_change'
        managed = False


class Zone(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    name = models.CharField(max_length=255, verbose_name="Nom de la zone")
    transmission_point = models.ForeignKey('Lieux', on_delete=models.CASCADE,db_column='transmission_point', related_name='zones_transmission') 

    class Meta:
        db_table = 'zone'
        managed = False

    def __str__(self):
        return self.name

class AlgerianCities(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nom de la ville")

    class Meta:
        db_table = 'algerian_cities'
        managed = False

    def __str__(self):
        return self.name

class Lieux(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name="Agence")
    name_en = models.CharField(max_length=255, verbose_name="Agence")
    name_ar = models.CharField(max_length=255, verbose_name="Agence")
    address = models.CharField(max_length=255, verbose_name="Adresse")
    address_en = models.CharField(null=True, blank=True)
    address_ar = models.CharField(null=True, blank=True)
    rendez_vous = models.CharField(max_length=255, verbose_name="rendez vous")
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE,db_column='zone', verbose_name="Zone de livraison")
    city = models.ForeignKey(AlgerianCities, on_delete=models.CASCADE,db_column='city', verbose_name="Ville")
    lieu_type_choices = [
        ('airport', 'Aéroport'),
        ('office', 'Bureau'),
    ]
    lieu_type = models.CharField(max_length=20, choices=lieu_type_choices, verbose_name="Type de lieu")
    mobile = models.CharField(max_length=20, verbose_name="Mobile")

    class Meta:
        db_table = 'lieux'
        managed = False

    def __str__(self):
        return self.name

class Categorie(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name="Catégorie")
    show_order = models.IntegerField(verbose_name="Ordre d'affichage")
    caution_classic = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Caution classique")
    caution_red = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Caution Réduite")

    class Meta:
        db_table = 'categorie'
        managed = False

    def __str__(self):
        return self.name


class Modele(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name="Nom du modèle")
    min_age = models.CharField(max_length=255, verbose_name="Âge minimum", null=True, blank=True)
    show_order_model = models.IntegerField(verbose_name="Ordre d'affichage", null=True, blank=True)
    caution_classic = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Caution classique", null=True, blank=True)
    caution_red = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Caution Réduite", null=True, blank=True)
    CARBURANT_CHOICES = [
        ('essence', 'Essence'),
        ('diesel', 'Diesel'),
        ('electrique', 'Électrique'),
    ]
    carburant = models.CharField(max_length=20, choices=CARBURANT_CHOICES, verbose_name="Carburant", null=True, blank=True)
    nombre_deplace = models.CharField(max_length=255, verbose_name="Nombre de places", null=True, blank=True)
    nombre_de_porte = models.CharField(max_length=255, verbose_name="Nombre de portes", null=True, blank=True)
    nombre_de_bagage = models.CharField(max_length=255, verbose_name="Nombre de bagages", null=True, blank=True)
    CLIMATISATION_CHOICES = [
        ('yes', 'Oui'),
        ('no', 'Non'),
    ]
    climatisation = models.CharField(max_length=10, choices=CLIMATISATION_CHOICES, verbose_name="Climatisation", null=True, blank=True)
    BOITE_VITESSE_CHOICES = [
        ('manuelle', 'Manuelle'),
        ('automatique', 'Automatique'),
    ]
    boite_vitesse = models.CharField(max_length=20, choices=BOITE_VITESSE_CHOICES, verbose_name="Boite Vitesse", null=True, blank=True)
    description_fr = models.TextField(verbose_name="Description (FR)", null=True, blank=True)
    description_en = models.TextField(verbose_name="Description (EN)", null=True, blank=True)
    description_ar = models.TextField(verbose_name="Description (AR)", null=True, blank=True)
    marketing_text_fr = models.CharField(max_length=255, verbose_name="Texte Marketing (FR)", null=True, blank=True)
    marketing_text_en = models.CharField(max_length=255, verbose_name="Texte Marketing (EN)", null=True, blank=True)
    condition_fr = models.TextField(verbose_name="Condition (FR)", null=True, blank=True)
    condition_en = models.TextField(verbose_name="Condition (EN)", null=True, blank=True)
    RECOMMENDATION_CHOICES = [
        ('yes', 'Oui'),
        ('no', 'Non'),
    ]
    recommendation = models.CharField(max_length=10, choices=RECOMMENDATION_CHOICES, verbose_name="Recommandation", default='no')
    categorie = models.ForeignKey(
        'Categorie',
        on_delete=models.SET_NULL,
        db_column='categorie',
        verbose_name="Catégorie",
        null=True,
        blank=True
    )
    photo_link = models.CharField(max_length=255, verbose_name="Photo Link", null=True, blank=True)
    photo_link_pay = models.CharField(max_length=255, verbose_name="Photo Link Pay", null=True, blank=True)
    STECKERS_CHOICES = [
        ('new', 'New'),
        ('promotion', 'promotion'),
        ('normal', 'Normal')
    ]
    stickers = models.CharField(max_length=10, choices=STECKERS_CHOICES, verbose_name="autocollant", default='normal')
    prix_one = models.IntegerField(verbose_name='Prix One')
    prix_two = models.IntegerField(verbose_name='Prix Two')
    prix_three = models.IntegerField(verbose_name='Prix Three')
    prix_four = models.IntegerField(verbose_name='Prix Four')
    prix_five = models.IntegerField(verbose_name='Prix Five')
    prix_six = models.IntegerField(verbose_name='Prix Six')
    prix_seven = models.IntegerField(verbose_name='Prix Seven')
    prix_eight = models.IntegerField(verbose_name='Prix Eight')
    prix_nine = models.IntegerField(verbose_name='Prix Nine')
    prix_ten = models.IntegerField(verbose_name='Prix Ten')

    MODEL_TYPE_CHOICES = [
        ('citadine', 'CITADINE'),
        ('cross', 'CROSS'),
        ('7_place', '7 PLACE'),
        ('9_place', '9 PLACE'),
        ('sedan', 'SEDAN'),
        ('compact', 'COMPACT')
    ]
    vehicule_type = models.CharField(max_length=10, choices=MODEL_TYPE_CHOICES, verbose_name="Type de véhicule")


    class Meta:
        db_table = 'modele'
        managed = False

    def __str__(self):
        return self.name

class Vehicule(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name="Véhicule", null=True, blank=True)
    matricule = models.CharField(max_length=255, verbose_name="Matricule", unique=True)
    model_name = models.CharField(max_length=255, verbose_name="Nom du modèle", unique=True)
    numero = models.CharField(max_length=255, verbose_name="Numéro", unique=True)
    couleur = models.CharField(max_length=255, verbose_name="Couleur", null=True, blank=True)
    couleur_tag = models.IntegerField(verbose_name="Couleur Tag", null=True, blank=True)
    modele = models.ForeignKey(
        'Modele',
        on_delete=models.SET_NULL,
        db_column='modele',
        verbose_name="Modèle",
        null=True,
        blank=True
    )
    categorie = models.ForeignKey(
        'Categorie',
        on_delete=models.SET_NULL,
        db_column='categorie',
        verbose_name="Catégorie",
        null=True,
        blank=True
    )
    carburant = models.CharField(
        max_length=20,
        choices=[
            ('essence', 'Essence'),
            ('diesel', 'Diesel'),
            ('electrique', 'Électrique')
        ],
        verbose_name="Carburant",
        null=True,
        blank=True
    )
    nombre_deplace = models.CharField(max_length=255, verbose_name="Nombre de places", null=True, blank=True)
    nombre_de_porte = models.CharField(max_length=255, verbose_name="Nombre de portes", null=True, blank=True)
    nombre_de_bagage = models.CharField(max_length=255, verbose_name="Nombre de bagages", null=True, blank=True)
    climatisation = models.CharField(
        max_length=10,
        choices=[
            ('yes', 'Oui'),
            ('no', 'Non')
        ],
        verbose_name="Climatisation",
        null=True,
        blank=True
    )
    boite_vitesse = models.CharField(
        max_length=20,
        choices=[
            ('manuelle', 'Manuelle'),
            ('automatique', 'Automatique')
        ],
        verbose_name="Boite Vitesse",
        null=True,
        blank=True
    )
    zone = models.ForeignKey(
        'Zone',
        on_delete=models.SET_NULL,
        db_column='zone',
        verbose_name="Zone de livraison",
        null=True,
        blank=True
    )
    marketing_text_fr = models.CharField(max_length=255, verbose_name="Marketing Text (FR)", null=True, blank=True)
    photo_link = models.CharField(max_length=255, verbose_name="Lien de la photo", null=True, blank=True)
    photo_link_nd = models.CharField(max_length=255, verbose_name="Lien de la 2eme photo", null=True, blank=True)
    age_min = models.CharField(max_length=255, verbose_name="age minimum", null=True, blank=True)
    sticker = models.CharField(max_length=20,
        choices=[
            ('new', 'new'),
            ('normal', 'normal'),
            ('promotion','promotion')
        ],
        verbose_name="sticker",
        null=True,
        blank=True)
    date_debut_service = models.DateField(verbose_name="Date mise en service", null=True, blank=True)
    date_fin_service = models.DateField(verbose_name="Date fin de service", null=True, blank=True)
    dernier_klm = models.IntegerField(verbose_name="Dernier kilométrage", null=True, blank=True)
    active_test = models.BooleanField(verbose_name="Actif", default=True)
    prix_achat = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix d'achat (DZD)",
        null=True,
        blank=True
    )
    prix_achat_eur = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix d'achat (EUR)",
        null=True,
        blank=True
    )
    COLOR_CHOICES = [
        ('noir', 'Noir'),
        ('blanc', 'Blanc'),
        ('gris', 'Gris'),
        ('bleu', 'Bleu'),
        ('rouge', 'Rouge'),
        ('argent', 'Argent'),
        ('vert', 'Vert'),
        ('orange', 'Orange'),
        ('marron', 'Marron'),
        ('violet', 'Violet'),
        ('beige', 'Beige'),
        ('bronze', 'Bronze'),
        ('bordeaux', 'Bordeaux'),
    ]
    color = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        verbose_name="Couleur du véhicule",
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'vehicule'
        managed = False

    def __str__(self):
        return f"{self.numero} - {self.matricule}"


class CategorieClient(models.Model):
    name = models.CharField(max_length=255, verbose_name="Catégorie")
    name_en = models.CharField(max_length=255, verbose_name="Catégorie EN")
    name_ar = models.CharField(max_length=255, verbose_name="Catégorie AR")
    du_pts = models.IntegerField(verbose_name="Du (pts)")
    au_pts = models.IntegerField(verbose_name="Au (pts)")
    reduction = models.IntegerField(verbose_name="Réduction (%)")
    reduction_pr = models.CharField(max_length=10, verbose_name="Réduction affichée", blank=True, null=True)
    category_code = models.CharField(max_length=10, verbose_name="CODE")

    option_one = models.ForeignKey('Options', on_delete=models.SET_NULL, null=True, db_column='option_one', related_name='option_one')
    option_two = models.ForeignKey('Options', on_delete=models.SET_NULL, null=True, db_column='option_two', related_name='option_two')
    option_three = models.ForeignKey('Options', on_delete=models.SET_NULL, null=True, db_column='option_three', related_name='option_three')
    option_four = models.ForeignKey('Options', on_delete=models.SET_NULL, null=True, db_column='option_four', related_name='option_four')
    option_five = models.ForeignKey('Options', on_delete=models.SET_NULL, null=True, db_column='option_five', related_name='option_five')
    option_six = models.ForeignKey('Options', on_delete=models.SET_NULL, null=True, db_column='option_six', related_name='option_six')
    option_seven = models.ForeignKey('Options', on_delete=models.SET_NULL, null=True, db_column='option_seven', related_name='option_seven')
    option_eight = models.ForeignKey('Options', on_delete=models.SET_NULL, null=True, db_column='option_eight', related_name='option_eight')
    option_nine = models.ForeignKey('Options', on_delete=models.SET_NULL, null=True, db_column='option_nine', related_name='option_nine')
    option_ten = models.ForeignKey('Options', on_delete=models.SET_NULL, null=True, db_column='option_ten', related_name='option_ten')

    class Meta:
        db_table = 'categorie_client'
        managed = False

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.reduction_pr = f"{self.reduction} %"
        super().save(*args, **kwargs)

    def clean(self):
        if self.au_pts <= self.du_pts:
            raise ValidationError(_("Le champ 'Au (pts)' doit être supérieur à 'Du (pts)'."))

        overlapping_records = CategorieClient.objects.filter(
            id__ne=self.id,
            du_pts__lte=self.au_pts,
            au_pts__gte=self.du_pts
        )
        if overlapping_records.exists():
            overlapping_record = overlapping_records.first()
            raise ValidationError(
                _("Les intervalles de points que vous avez saisis chevauchent avec la catégorie '%(name)s' "
                  "[%(du_pts)d - %(au_pts)d].") % {
                    'name': overlapping_record.name,
                    'du_pts': overlapping_record.du_pts,
                    'au_pts': overlapping_record.au_pts
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class SoldeParrainage(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nom")
    parrain_solde = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Filleul (Euro)"
    )
    parrain_solde_da = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Filleul (Dinar algérien)",
        blank=True,
        null=True
    )

    filleul_solde = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Parrain (Euro)"
    )
    filleul_solde_da = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Parrain (Dinar algérien)",
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'solde_parrainage'
        managed = False


    def __str__(self):
        return self.name


class ListeClient(models.Model):
    CIVILITE_CHOICES = [
        ('Mr', 'M.'),
        ('Mme', 'Mme'),
        ('Mlle', 'Mlle'),
    ]
    RISQUE_CHOICES = [
        ('faible', 'Faible'),
        ('moyen', 'Moyen'),
        ('eleve', 'Elevé'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name="Nom complet", blank=True, null=True)
    civilite = models.CharField(max_length=10, choices=CIVILITE_CHOICES, verbose_name="Civilité", blank=True, null=True)
    nom = models.CharField(max_length=255, verbose_name="Nom", null=False)
    prenom = models.CharField(max_length=255, verbose_name="Prénom", blank=True, null=True)
    email = models.EmailField(verbose_name="Email", blank=True, null=True)
    date_de_naissance = models.DateField(verbose_name="Date de naissance", blank=True, null=True)
    mobile = models.CharField(max_length=20, verbose_name="Mobile", blank=True, null=True)
    telephone = models.CharField(max_length=20, verbose_name="Téléphone", blank=True, null=True)
    risque = models.CharField(
        max_length=10,
        choices=RISQUE_CHOICES,
        verbose_name="Risque",
        default="faible"
    )
    note = models.TextField(verbose_name="Note", blank=True, null=True)
    date_de_permis = models.DateField(verbose_name="Date de permis", blank=True, null=True)
    categorie_client = models.ForeignKey(
        'CategorieClient',
        on_delete=models.SET_NULL,
        db_column='categorie_client',
        verbose_name="Catégorie",
        blank=True,
        null=True
    )
    category_client_name = models.CharField()

    reduction = models.IntegerField(verbose_name="Réduction %", blank=True, null=True)

    total_points = models.IntegerField(verbose_name="Total des points", blank=True, null=True)
    total_points_char = models.CharField(max_length=50, verbose_name="Total des points (texte)", blank=True, null=True)
    solde = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Solde non consommé",
        blank=True,
        null=True
    )
    total_reservation = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total des réservations",
        blank=True,
        null=True
    )
    code_prime = models.CharField(
        max_length=50,
        verbose_name="Code Prime",
        blank=True,
        null=True
    )

    parrain = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        db_column='parrain',
        verbose_name="Le parrain",
        blank=True,
        null=True,
        related_name='filleuls'
    )
    solde_total = models.IntegerField(verbose_name="Solde Total", blank=True, null=True)
    solde_consomer = models.IntegerField(verbose_name="Solde consommé", blank=True, null=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    create_date = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.IntegerField(default=0)

    class Meta:
        db_table = 'liste_client'
        managed = False

    def __str__(self):
        return f"{self.nom} {self.prenom or ''}"

    def compute_full_name(self):
        """Calcule le champ `name` à partir des champs `civilite`, `nom` et `prenom`."""
        self.name = f"{self.civilite or ''} {self.nom} {self.prenom or ''}".strip()

    def compute_code_prime(self):
        year_suffix = str(datetime.now().year)[-2:]  
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) 
        self.code_prime = f"01{year_suffix}{random_part}"

    def compute_total_points_char(self):
        """Convertit les `total_points` en une chaîne de caractères."""
        self.total_points_char = f"{self.total_points} pts" if self.total_points is not None else ""

    def save(self, *args, **kwargs):
        self.compute_full_name()
        self.compute_code_prime()
        self.compute_total_points_char()
        super().save(*args, **kwargs)



class Saison(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nom complet", blank=True, null=True)

    class Meta:
        db_table = 'saison'
        managed = False

class Periode(models.Model):
    name = models.CharField(max_length=255, editable=False, null=True, blank=True)
    saison = models.ForeignKey('Saison', on_delete=models.CASCADE,db_column='saison', related_name='periodes')
    date_debut = models.DateField()
    date_fin = models.DateField()
    tarif_id = models.ForeignKey(
        'Tarifs', on_delete=models.CASCADE,db_column='tarif_id', verbose_name="Tarif"
    )

    class Meta:
        db_table = 'periode'
        managed = False

    def save(self, *args, **kwargs):
        self.name = f"{self.saison} ({self.date_debut} - {self.date_fin})"
        super().save(*args, **kwargs)

    def clean(self):
        if self.date_fin <= self.date_debut:
            raise ValidationError("La date de fin doit être postérieure à la date de début.")

class NombreDeJour(models.Model):
    name = models.CharField(max_length=255, editable=False, null=True, blank=True)
    de = models.IntegerField()
    au = models.IntegerField()

    class Meta:
        db_table = 'nb_jour'
        managed = False

    def save(self, *args, **kwargs):
        self.name = f"{self.de} et +"
        super().save(*args, **kwargs)

    def clean(self):
        if self.de >= self.au:
            raise ValidationError("La valeur de 'au' doit être strictement supérieure à la valeur de 'de'.")

        overlapping_records = NombreDeJour.objects.filter(
            de__lte=self.au,
            au__gte=self.de
        ).exclude(id=self.id)
        if overlapping_records.exists():
            overlapping_intervals = ", ".join(
                f"de: {rec.de}, au: {rec.au}"
                for rec in overlapping_records
            )
            raise ValidationError(
                f"Les intervalles se chevauchent avec les enregistrements suivants : {overlapping_intervals}"
            )

class Tarifs(models.Model):
    name = models.CharField(max_length=255, editable=False, null=True, blank=True)
    saison = models.ForeignKey(
        'Saison', on_delete=models.CASCADE, db_column='saison',verbose_name="Saison", related_name="tarifs"
    )
    zone = models.ForeignKey(
        'Zone', on_delete=models.CASCADE, db_column='zone',verbose_name="zone", related_name="tarifs"
    )
    modele = models.ForeignKey(
        'Modele', on_delete=models.CASCADE, db_column='modele', verbose_name="Modèle", related_name="tarifs"
    )
    categorie = models.ForeignKey(
        'Categorie', on_delete=models.CASCADE, db_column='categorie', verbose_name="Categorie", related_name="tarifs"
    )
    prix = models.IntegerField(verbose_name="Prix")
    nb_jour = models.ForeignKey(
        'NombreDeJour', on_delete=models.CASCADE,db_column='nb_jour', verbose_name="Nombre de jours", related_name="tarifs"
    )
    nbr_de = models.IntegerField(editable=False, null=True, blank=True)
    nbr_au = models.IntegerField(editable=False, null=True, blank=True)
    date_depart_one = models.DateField(editable=False, null=True, blank=True)
    date_fin_one = models.DateField(editable=False, null=True, blank=True)
    date_depart_two = models.DateField(editable=False, null=True, blank=True)
    date_fin_two = models.DateField(editable=False, null=True, blank=True)
    date_depart_three = models.DateField(editable=False, null=True, blank=True)
    date_fin_three = models.DateField(editable=False, null=True, blank=True)
    date_depart_four = models.DateField(editable=False, null=True, blank=True)
    date_fin_four = models.DateField(editable=False, null=True, blank=True)

    class Meta:
        db_table = 'tarifs'
        managed = False

class TypeOptions(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Type",
        null=False,
        blank=False
    )
    class Meta:
        db_table = 'type_options'
        managed = False

    def __str__(self):
        return self.name

class Options(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Nom de l'option",
        null=False,
        blank=False
    )
    type_option = models.ForeignKey(
        'TypeOptions',
        on_delete=models.CASCADE,
        db_column='type_option',
        verbose_name="Type de l'option",
        related_name="options"
    )
    description = models.TextField(
        verbose_name="Description",
        null=True,
        blank=True
    )
    tout_modele = models.CharField(
        max_length=3,
        choices=[('oui', 'Oui'), ('non', 'Non')],
        verbose_name="Appliquer sur toutes les catégories",
        default='oui'
    )
    modele = models.ForeignKey(
        'Modele',
        on_delete=models.CASCADE,
        verbose_name="Modèle",
        db_column='modele',
        null=True,
        blank=True,
        related_name="options"
    )
    zone = models.ForeignKey(
        'Zone',
        on_delete=models.CASCADE,
        verbose_name="Zone",
        db_column='zone',
        null=True,
        blank=True,
        related_name="options"
    )
    categorie = models.ForeignKey(
        'Categorie',
        on_delete=models.CASCADE,
        db_column='categorie',
        verbose_name="Catégorie",
        null=True,
        blank=True,
        related_name="options"
    )
    prix = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Prix",
        null=True,
        blank=True
    )
    min_prix = models.FloatField(
        verbose_name="Prix Min",
        null=True,
        blank=True
    )
    type_tarif = models.CharField(
        max_length=10,
        choices=[('jour', 'Par jour'), ('fixe', 'Montant fixe'),('un_jour', 'prix un jour')],
        verbose_name="Type de Tarif",
        default='jour'
    )
    option_code = models.CharField(
        max_length=255,
        verbose_name="CODE",
        null=False,
        blank=False
    )
    caution = models.IntegerField(
        verbose_name="Caution",
        null=True,
        blank=True
    )
    limit_Klm = models.IntegerField(
        verbose_name="Limit KLM",
        null=True,
        blank=True
    )
    penalite_Klm = models.FloatField(
        verbose_name="Penalité KLM",
        null=True,
        blank=True
    )
    name_en = models.CharField(
        max_length=255,
        verbose_name="Nom de l'option",
        null=False,
        blank=False
    ) 
    name_ar = models.CharField(
        max_length=255,
        verbose_name="Nom de l'option",
        null=False,
        blank=False
    )

    class Meta:
        db_table = 'options'
        managed = False

    def __str__(self):
        return self.name

class FraisLivraison(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Nom",
        blank=True,
        null=True
    )
    depart = models.ForeignKey(
        'Lieux',
        on_delete=models.CASCADE,
        db_column='depart',
        verbose_name="Départ",
        related_name="livraisons_depart",
        null=False,
        blank=False
    )
    zone = models.ForeignKey(
        'Zone',
        on_delete=models.CASCADE,
        verbose_name="Zone",
        db_column='zone',
        related_name="livraisons_zone",
        null=True,
        blank=True
    )
    retour = models.ForeignKey(
        'Lieux',
        on_delete=models.CASCADE,
        db_column='retour',
        verbose_name="Retour",
        related_name="livraisons_retour",
        null=False,
        blank=False
    )
    montant = models.IntegerField(
        verbose_name="Montant",
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'frais_livraison'
        managed = False

    def __str__(self):
        if self.depart and self.retour:
            return f"De {self.depart.name} au {self.retour.name}"
        return "Frais de Livraison"

    def save(self, *args, **kwargs):
        """Calcule automatiquement le nom avant de sauvegarder."""
        if self.depart and self.retour:
            self.name = f"De {self.depart.name} au {self.retour.name}"
        else:
            self.name = ""
        super().save(*args, **kwargs)

class Supplement(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Nom",
        blank=True,
        null=True
    )
    heure_debut = models.CharField(
        max_length=5,
        verbose_name="Heure début",
        blank=True,
        null=True
    )
    heure_fin = models.CharField(
        max_length=5,
        verbose_name="Heure Fin",
        blank=True,
        null=True
    )
    heure_debut_float = models.FloatField(
        verbose_name="Heure début (float)",
        blank=True,
        null=True
    )
    heure_fin_float = models.FloatField(
        verbose_name="Heure Fin (float)",
        blank=True,
        null=True
    )
    montant = models.IntegerField(
        verbose_name="Montant",
        blank=True,
        null=True
    )
    reatrd = models.IntegerField(
        verbose_name="Si dépasse (heure)",
        blank=True,
        null=True
    )
    valeur = models.IntegerField(
        verbose_name="Valeur %",
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'supplements'
        managed = False

    def __str__(self):
        return self.name or "Supplément"


class Promotion(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Nom",
        blank=True,
        null=True
    )
    tout_modele = models.CharField(
        max_length=3,
        choices=[('oui', 'Oui'), ('non', 'Non')],
        default='oui',
        verbose_name="Appliquer sur tout les modèles"
    )
    modele = models.ForeignKey(
        'Modele',
        on_delete=models.SET_NULL,
        db_column='modele',
        verbose_name="Modèle",
        null=True,
        blank=True
    )
    date_debut = models.DateField(
        verbose_name="Date début",
        default=date.today
    )
    date_fin = models.DateField(
        verbose_name="Date fin",
        default=lambda: date.today() + timedelta(days=30)
    )
    debut_visibilite = models.DateField(
        verbose_name="Début visibilité",
        default=date.today
    )
    fin_visibilite = models.DateField(
        verbose_name="Fin visibilité",
        default=lambda: date.today() + timedelta(days=30)
    )
    code_promo = models.CharField(
        max_length=255,
        verbose_name="Code promo",
        blank=True,
        null=True
    )
    reduction = models.IntegerField(
        verbose_name="Réduction %",
        blank=True,
        null=True
    )
    zone = models.ForeignKey(
        'Zone',
        on_delete=models.SET_NULL,
        db_column='zone',
        verbose_name="Zone", null=True, blank=True)
    active_passive = models.BooleanField(
        verbose_name="Active",
        default=False
    )
    tout_zone = models.CharField(
        max_length=3,
        choices=[('oui', 'Oui'), ('non', 'Non')],
        default='oui',
        verbose_name="Appliquer sur tout les modèles"
    )
    model_one = models.ForeignKey(Modele, on_delete=models.SET_NULL,related_name='model_one', db_column='model_one', verbose_name="Modèle", null=True, blank=True)
    model_two = models.ForeignKey(Modele, on_delete=models.SET_NULL,related_name='model_two', db_column='model_two', verbose_name="Modèle", null=True, blank=True)
    model_three = models.ForeignKey(Modele, on_delete=models.SET_NULL,related_name='model_three', db_column='model_three', verbose_name="Modèle", null=True, blank=True)
    model_four = models.ForeignKey(Modele, on_delete=models.SET_NULL,related_name='model_four', db_column='model_four', verbose_name="Modèle", null=True, blank=True)
    model_five = models.ForeignKey(Modele, on_delete=models.SET_NULL,related_name='model_five', db_column='model_five', verbose_name="Modèle", null=True, blank=True)
    zone_one = models.ForeignKey(Zone, on_delete=models.SET_NULL,related_name='zone_one', db_column='zone_one', verbose_name="Modèle", null=True, blank=True)
    zone_two = models.ForeignKey(Zone, on_delete=models.SET_NULL,related_name='zone_two', db_column='zone_two', verbose_name="Modèle", null=True, blank=True)
    zone_three = models.ForeignKey(Zone, on_delete=models.SET_NULL,related_name='zone_three', db_column='zone_three', verbose_name="Modèle", null=True, blank=True)
    nbr_model = models.IntegerField(null=True, blank=True)
    nbr_zone = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'promotion'
        managed = False

    def __str__(self):
        return self.name or "Promotion"

class AnnulerRaison(models.Model):
    name = models.AutoField(primary_key=True)
    name_en = models.CharField()
    name_ar = models.CharField()
    class Meta:
        db_table = 'annuler_raison'
        managed = False

class Users(models.Model):
    id = models.AutoField(primary_key=True)
    class Meta:
        db_table = 'res_users'
        managed = False

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('en_attend', 'En attente'),
        ('rejete', 'Rejeté'),
        ('annule', 'Annulé'),
        ('confirmee', 'Confirmée'),
        ('confirme', 'Confirmé')
    ]

    ETAT_RESERVATION_CHOICES = [
        ('reserve', 'Réservé'),
        ('loue', 'Loué'),
        ('annule', 'Annulé')
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=10, unique=True, editable=False, default='')
    country_code = models.CharField(max_length=10, unique=True, editable=False, default='')
    numero_lieu = models.CharField(max_length=10, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    create_date = models.DateTimeField(default=datetime.now)
    etat_reservation = models.CharField(max_length=10, choices=ETAT_RESERVATION_CHOICES, default='reserve')
    date_heure_debut = models.DateTimeField(default=datetime.now)
    date_heure_fin = models.DateTimeField(default=lambda: datetime.now() + timedelta(days=3))
    nbr_jour_reservation = models.IntegerField(editable=False)
    duree_dereservation = models.CharField(max_length=100, editable=False)

    lieu_depart = models.ForeignKey('Lieux', on_delete=models.CASCADE,db_column='lieu_depart', related_name='lieu_depart_reservations')
    zone = models.ForeignKey('Zone', on_delete=models.CASCADE,db_column='zone', related_name='zone_reservations', editable=False)
    lieu_retour = models.ForeignKey('Lieux', on_delete=models.CASCADE,db_column='lieu_retour', related_name='lieu_retour_reservations')
    vehicule = models.ForeignKey('Vehicule', on_delete=models.CASCADE,db_column='vehicule', null=True, blank=True)
    modele = models.ForeignKey('Modele', on_delete=models.CASCADE,db_column='modele', editable=False, null=True, blank=True)
    categorie = models.ForeignKey('Categorie', on_delete=models.CASCADE,db_column='categorie', editable=False, null=True, blank=True)
    carburant = models.CharField(max_length=50, editable=False, null=True, blank=True)
    date_debut_service = models.DateField(editable=False, null=True, blank=True)
    date_fin_service = models.DateField(editable=False, null=True, blank=True)
    matricule = models.CharField(max_length=50, editable=False, null=True, blank=True)
    numero = models.CharField(max_length=50, editable=False, null=True, blank=True)


    model_name = models.CharField(max_length=50, editable=False, null=True, blank=True)
    marketing_text_fr = models.CharField(max_length=50, editable=False, null=True, blank=True)
    photo_link_nd = models.CharField(max_length=50, editable=False, null=True, blank=True)
    photo_link = models.CharField(max_length=50, editable=False, null=True, blank=True)
    nombre_deplace = models.CharField(max_length=50, editable=False, null=True, blank=True)
    nombre_de_porte = models.CharField(max_length=50, editable=False, null=True, blank=True)
    nombre_de_bagage = models.CharField(max_length=50, editable=False, null=True, blank=True)
    boite_vitesse = models.CharField(max_length=50, editable=False, null=True, blank=True)
    age_min = models.CharField(max_length=50, editable=False, null=True, blank=True)


    client = models.ForeignKey('ListeClient', on_delete=models.CASCADE,db_column='client', related_name='reservations')
    nd_client = models.ForeignKey('ListeClient', on_delete=models.CASCADE,db_column='nd_client', related_name='nd_client_reservations')
    nom = models.CharField(max_length=255, editable=False)
    prenom = models.CharField(max_length=255, editable=False)
    email = models.EmailField(editable=False)
    date_de_naissance = models.DateField(editable=False, null=True, blank=True)
    permis_date = models.DateField(editable=False, null=True, blank=True)
    mobile = models.CharField(max_length=50, editable=False, null=True, blank=True)
    telephone = models.CharField(max_length=50, editable=False, null=True, blank=True)
    risque = models.CharField(max_length=50, editable=False, null=True, blank=True)
    note = models.TextField(editable=False, null=True, blank=True)
    categorie_client = models.ForeignKey('CategorieClient', on_delete=models.SET_NULL,db_column='categorie_client', null=True, blank=True, editable=False)
    code_prime = models.CharField(max_length=100, editable=False, null=True, blank=True)
    reduction = models.IntegerField(editable=False, null=True, blank=True)
    solde = models.DecimalField(max_digits=10, decimal_places=2, editable=False, null=True, blank=True)
    solde_total = models.IntegerField(editable=False, null=True, blank=True)
    solde_consomer = models.IntegerField(editable=False, null=True, blank=True)
    exchange_amount = models.FloatField(null=True, blank=True)

    prix_jour = models.IntegerField(editable=False)
    prix_jour_two = models.IntegerField(null=True, blank=True)
    nbr_jour_two = models.IntegerField(null=True, blank=True)
    nbr_jour_one = models.IntegerField(null=True, blank=True)
    frais_de_livraison = models.IntegerField(editable=False)
    options_total = models.IntegerField(editable=False)
    options_total_reduit = models.IntegerField(editable=False)

    total = models.IntegerField(editable=False)
    total_reduit = models.IntegerField(editable=False)
    total_reduit_euro = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    total_revenue = models.FloatField()
    montant_paye = models.FloatField()
    du_au = models.CharField(max_length=255, editable=False)

    total_afficher = models.IntegerField(editable=False)
    total_afficher_reduit = models.IntegerField(editable=False)
    prix_jour_afficher = models.FloatField(editable=False)
    prix_jour_afficher_reduit = models.FloatField(editable=False)
    supplements = models.IntegerField(editable=False)
    retour_tard = models.IntegerField(editable=False)

    civilite_nd_condicteur = models.CharField(
        max_length=10,
        choices=[('Mr', 'M.'), ('Mme', 'Mme'), ('Mlle', 'Mlle')],
        null=True, blank=True
    )
    nom_nd_condicteur = models.CharField(max_length=255, null=True, blank=True)
    prenom_nd_condicteur = models.CharField(max_length=255, null=True, blank=True)
    email_nd_condicteur = models.EmailField(null=True, blank=True)
    date_nd_condicteur = models.DateField(null=True, blank=True)
    date_de_permis = models.DateField(null=True, blank=True)
    nd_conducteur = models.CharField(
        max_length=10,
        choices=[('oui', 'oui'), ('non', 'non')],
        default='non'
    )
    nd_conducteur_two = models.CharField(
        max_length=10,
        choices=[('oui', 'oui'), ('non', 'non')],
        default='non'
    )
    is_nd_cond = models.BooleanField(editable=False)

    client_created = models.BooleanField(default=False)
    liste_client_id = models.ForeignKey('ListeClient', on_delete=models.SET_NULL,db_column='liste_client_id', null=True, blank=True)
    note_lv_d = models.TextField(null=True, blank=True)
    note_lv_r = models.TextField(null=True, blank=True)
    annuler_raison = models.ForeignKey('AnnulerRaison', on_delete=models.SET_NULL,db_column='annuler_raison', null=True, blank=True)
    #rejet_raison = models.ForeignKey('RejetRaison', on_delete=models.SET_NULL, null=True, blank=True)
    prolonge = models.CharField(
        max_length=10,
        choices=[('non', 'Non'), ('oui', 'Oui')],
        default='non'
    )
    total_prolone = models.IntegerField(editable=False)
    depart_retour = models.CharField(max_length=255, editable=False)
    frais_de_dossier = models.IntegerField(editable=False)
    retour_avance = models.BooleanField(default=False)
    date_retour_avance = models.DateTimeField(null=True, blank=True)

    klm_moyen = models.CharField(max_length=255, editable=False)
    klm_moyen_int = models.IntegerField(editable=False)

    color_tag = models.IntegerField(null=True, blank=True)
    solde_reduit = models.IntegerField(null=True, blank=True)

    opt_payment = models.ForeignKey('Options', on_delete=models.CASCADE,db_column='opt_payment', related_name='opt_payment')
    opt_payment_name = models.CharField(max_length=255, null=True, blank=True)
    opt_payment_price = models.FloatField(null=True, blank=True)
    opt_payment_total = models.IntegerField(null=True, blank=True)
    opt_klm = models.ForeignKey(
        'Options', on_delete=models.CASCADE,
        db_column='opt_klm', related_name='opt_klm',
        null=True, blank=True
    ) 
    opt_klm_name = models.CharField(max_length=255, null=True, blank=True)
    opt_klm_price = models.FloatField(null=True, blank=True)
    opt_klm_total = models.IntegerField(null=True, blank=True)
    opt_kilometrage = models.IntegerField(null=True, blank=True)
    opt_protection = models.ForeignKey('Options', on_delete=models.CASCADE,db_column='opt_protection', related_name='opt_protection', null=True, blank=True)
    opt_protection_name = models.CharField(max_length=255, null=True, blank=True)
    opt_protection_caution = models.IntegerField(null=True, blank=True)
    opt_protection_price = models.FloatField(null=True, blank=True)
    opt_protection_total = models.IntegerField(null=True, blank=True)
    opt_nd_driver = models.ForeignKey(
        'Options',
        on_delete=models.CASCADE,
        db_column='opt_nd_driver',
        related_name='opt_nd_driver',
        null=True,
        blank=True
    )
    opt_nd_driver_name = models.CharField(max_length=255, null=True, blank=True)
    opt_nd_driver_price = models.FloatField(null=True, blank=True)
    opt_nd_driver_total = models.IntegerField(null=True, blank=True)
    opt_plein_carburant = models.ForeignKey(
        'Options', on_delete=models.CASCADE,
        db_column='opt_plein_carburant', related_name='opt_plein_carburant',
        null=True, blank=True
    )
    opt_plein_carburant_name = models.CharField(max_length=255, null=True, blank=True)
    opt_plein_carburant_prix = models.FloatField(null=True, blank=True)
    opt_plein_carburant_total = models.IntegerField(null=True, blank=True)
    opt_siege_a = models.ForeignKey(
        'Options', on_delete=models.CASCADE,
        db_column='opt_siege_a', related_name='opt_siege_a',
        null=True, blank=True
    )
    opt_siege_a_name = models.CharField(max_length=255, null=True, blank=True)
    opt_siege_a_prix = models.FloatField(null=True, blank=True)
    opt_siege_a_total = models.IntegerField(null=True, blank=True)
    opt_siege_b = models.ForeignKey(
        'Options', on_delete=models.CASCADE,
        db_column='opt_siege_b', related_name='opt_siege_b',
        null=True, blank=True
    )
    opt_siege_b_name = models.CharField(max_length=255, null=True, blank=True)
    opt_siege_b_prix = models.FloatField(null=True, blank=True)
    opt_siege_b_total = models.IntegerField(null=True, blank=True)
    opt_siege_c = models.ForeignKey(
        'Options', on_delete=models.CASCADE,
        db_column='opt_siege_c', related_name='opt_siege_c',
        null=True, blank=True
    )
    opt_siege_c_prix = models.FloatField(null=True, blank=True)
    opt_siege_c_name = models.CharField(max_length=255, null=True, blank=True)
    opt_siege_c_total = models.IntegerField(null=True, blank=True)
    num_vol = models.CharField()
    client_create_date = models.DateTimeField()
    address_fr = models.CharField(null=True, blank=True)
    address_en = models.CharField(null=True, blank=True)
    address_ar = models.CharField(null=True, blank=True)
    du_au_modifier = models.CharField(null=True, blank=True)
    ancien_lieu = models.CharField(null=True, blank=True)
    reste_payer = models.FloatField(null=True, blank=True)
    
    date_depart_char = models.CharField(null=True, blank=True)
    date_retour_char = models.CharField(null=True, blank=True)
    heure_depart_char = models.CharField(null=True, blank=True)
    heure_retour_char = models.CharField(null=True, blank=True)
    
    confirmation_date = models.DateTimeField(null=True, blank=True)
    cancelation_date = models.DateTimeField(null=True, blank=True)


    class Meta:
        db_table = 'reservation'

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self._generate_unique_code_()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_unique_code_():
        current_date = datetime.now()
        year = current_date.strftime('%y')  # Deux derniers chiffres de l'année
        while True:
            random_digits = ''.join(random.choices(string.digits, k=4))  # Quatre chiffres aléatoires
            unique_code = f'{year}{random_digits}'
            if not Reservation.objects.filter(name=unique_code).exists():
                return unique_code

    def __str__(self):
        return self.name

class Livraison(models.Model):
    name = models.CharField(max_length=255, verbose_name='Nom')
    reservation = models.ForeignKey('Reservation', on_delete=models.CASCADE,db_column='reservation', related_name='livraisons', verbose_name='Reservation')
    total_prolone = models.IntegerField(verbose_name='Prolongation', null=True, blank=True)
    total_prolone_eur = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Prolongation (EUR)', null=True, blank=True)
    lv_type = models.CharField(max_length=20, choices=[('livraison', 'D'), ('restitution', 'R')], verbose_name='Type')
    status = models.CharField(max_length=50, verbose_name='État', null=True, blank=True)
    note_lv_d = models.TextField(verbose_name='Note LV Début', null=True, blank=True)
    note_lv_r = models.TextField(verbose_name='Note LV Retour', null=True, blank=True)
    date_heure_debut = models.DateTimeField(verbose_name='Date Début', null=True, blank=True)
    date_de_reservation = models.DateTimeField(verbose_name='Date de Réservation', null=True, blank=True)
    date_heure_fin = models.DateTimeField(verbose_name='Date Fin', null=True, blank=True)
    nbr_jour_reservation = models.IntegerField(verbose_name='Durée de Réservation', null=True, blank=True)
    duree_dereservation = models.CharField(max_length=255, verbose_name='Durée', null=True, blank=True)

    lieu_depart = models.ForeignKey('Lieux', on_delete=models.SET_NULL,db_column='lieu_depart', null=True, blank=True, related_name='depart_livraisons', verbose_name='Lieu de Départ')
    zone = models.ForeignKey('Zone', on_delete=models.SET_NULL,db_column='zone', null=True, blank=True, verbose_name='Zone')
    lieu_retour = models.ForeignKey('Lieux', on_delete=models.SET_NULL,db_column='lieu_retour', null=True, blank=True, related_name='retour_livraisons', verbose_name='Lieu de Retour')
    vehicule = models.ForeignKey('Vehicule', on_delete=models.SET_NULL,db_column='vehicule', null=True, blank=True, verbose_name='Véhicule')
    modele = models.ForeignKey('Modele', on_delete=models.SET_NULL, null=True,db_column='modele', blank=True, verbose_name='Modèle')

    caution_classic = models.FloatField(verbose_name='Caution Classique', null=True, blank=True)
    caution_red = models.FloatField(verbose_name='Caution Réduite', null=True, blank=True)
    caution_classic_eur = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Caution (EUR)', null=True, blank=True)
    carburant = models.CharField(max_length=50, verbose_name='Carburant', null=True, blank=True)

    client = models.ForeignKey('ListeClient', on_delete=models.SET_NULL,db_column='client', null=True, blank=True, verbose_name='Client')
    nom = models.CharField(max_length=255, verbose_name='Nom Client', null=True, blank=True)
    prenom = models.CharField(max_length=255, verbose_name='Prénom Client', null=True, blank=True)
    email = models.EmailField(verbose_name='Email', null=True, blank=True)
    mobile = models.CharField(max_length=20, verbose_name='Mobile', null=True, blank=True)

    kilomtrage = models.IntegerField(verbose_name='Kilométrage', null=True, blank=True)
    siege_bebe = models.BooleanField(default=False, verbose_name='Siège Bébé')
    document_vehicule = models.BooleanField(default=True, verbose_name='Document Véhicule')
    garantie = models.BooleanField(default=False, verbose_name='Caution Déposée')
    etat_carburant = models.CharField(max_length=20, choices=[
        ('plein', 'Plein carburant'),
        ('demi', '1/2 plein carburant'),
        ('tiere', '1/3 plein carburant'),
        ('quart', '1/4 plein carburant'),
    ], verbose_name='État du Carburant', null=True, blank=True)
    document_fournis = models.CharField(max_length=20, choices=[
        ('passport', 'Passport'),
        ('cin', 'CIN'),
    ], verbose_name='Document Fourni', null=True, blank=True)
    #signature = models.TextField(verbose_name='Signature', null=True, blank=True)

    total_da = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total Dégradation (DA)', null=True, blank=True)
    total_eur = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Dégradation (EUR)', null=True, blank=True)

    stage = models.CharField(max_length=20, choices=[
        ('reserve', 'Planifié'),
        ('livre', 'Livré'),
    ], default='reserve', verbose_name='Étape')

    total_da = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Total dégradation (DA)")
    )
    total_eur = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Dégradation (EUR)")
    )
    total_restitution_eur = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Total restitution (EUR)")
    )
    lv_note = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Note")
    )
    assurance_complementaire = models.BooleanField(
        default=False,
        verbose_name=_("Assurance complémentaire")
    )
    change_lieu_retour = models.BooleanField(
        default=False,
        verbose_name=_("Changer lieu de retour")
    )
    change_heure_retour = models.BooleanField(
        default=False,
        verbose_name=_("Changer heure de retour")
    )
    action_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date")
    )
    action_lieu = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Lieu")
    )
    color = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Couleur")
    )
    total_reduit_euro = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Total réduit (EUR)")
    )
    date_retour_one = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Ancienne date retour")
    )
    lieu_retour_one = models.ForeignKey(
        'Lieux',
        on_delete=models.SET_NULL,
        db_column='lieu_retour_one',
        related_name='anciennes_livraisons',
        null=True,
        verbose_name=_("Ancien lieu retour")
    )
    total_rduit_one = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Ancien total")
    )
    ecart_a_paye = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Écart à payer")
    )
    montant_dz_pay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Total  (DA)")
    )
    montant_euro_pay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Total (EUR)")
    )

    penalit_klm_dinar = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("penalite klm (DA)")
    )

    penalit_carburant = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("penalite carburant (DA)")
    )
    opt_protection =  models.CharField()

    opt_carburant = models.ForeignKey(Options, on_delete=models.SET_NULL,db_column='opt_carburant', null=True, blank=True, verbose_name='Lieu de Départ')
    opt_carburant_check = models.BooleanField()
    opt_klm = models.ForeignKey(Options, on_delete=models.SET_NULL,db_column='opt_klm', null=True, blank=True, verbose_name='Lieu de Départ')
    opt_klm_check = models.BooleanField()
    opt_nd_driver = models.ForeignKey(Options, on_delete=models.SET_NULL,db_column='opt_nd_driver', null=True, blank=True, verbose_name='Lieu de Départ')
    opt_nd_driver_check = models.BooleanField()
    opt_sb_a = models.ForeignKey(Options, on_delete=models.SET_NULL,db_column='opt_sb_a', null=True, blank=True, verbose_name='Lieu de Départ')
    opt_sb_a_check = models.BooleanField()
    opt_sb_b = models.ForeignKey(Options, on_delete=models.SET_NULL,db_column='opt_sb_b', null=True, blank=True, verbose_name='Lieu de Départ')
    opt_sb_b_check = models.BooleanField()
    opt_sb_c = models.ForeignKey(Options, on_delete=models.SET_NULL,db_column='opt_sb_c', null=True, blank=True, verbose_name='Lieu de Départ')
    opt_sb_c_check = models.BooleanField()

    date_depart_char_ = models.CharField(null=True, blank=True)
    date_retour_char_ = models.CharField(null=True, blank=True)
    heure_depart_char_ = models.CharField(null=True, blank=True)
    heure_retour_char_ = models.CharField(null=True, blank=True)
    num_vol = models.CharField()

    opt_protection_caution = models.IntegerField(null=True, blank=True)

    total_payer = models.FloatField(null=True, blank=True)
    total_payer_dz = models.FloatField(null=True, blank=True)
    date_de_livraison = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'livraison'
        managed = False


    def __str__(self):
        return self.name

class BookCar(models.Model):

    name = models.CharField(max_length=255, verbose_name='Name',default='test')
    lieu_depart = models.ForeignKey(
        Lieux,
        related_name='lieu_depart',
        db_column='lieu_depart',
        on_delete=models.CASCADE,
        verbose_name='Lieu de départ'
    )
    zone = models.ForeignKey(
        Zone,
        db_column='zone',
        on_delete=models.CASCADE,
        verbose_name='Zone de départ',
        editable=False,
        null=True,
        blank=True
    )
    lieu_retour = models.ForeignKey(
        Lieux,
        related_name='lieu_retour',
        db_column='lieu_retour',
        on_delete=models.CASCADE,
        verbose_name='Lieu de retour'
    )
    date_depart = models.DateField(verbose_name='Date de départ')
    date_retour = models.DateField(verbose_name='Date de retour')
    heure_debut = models.CharField(max_length=5, verbose_name='Heure début')
    heure_fin = models.CharField(max_length=5, verbose_name='Heure Fin')

    class Meta:
        db_table = 'book_car'

    def save(self, *args, **kwargs):
        if self.lieu_depart and self.lieu_depart.zone:
            self.zone = self.lieu_depart.zone
        super().save(*args, **kwargs)


class ContactMessage(models.Model):
    name = models.CharField(max_length=255, verbose_name='ID', editable=False)
    nom_complet = models.CharField(max_length=255, verbose_name='Nom Complet', editable=False)
    email = models.CharField(max_length=255, verbose_name='E-mail', editable=False)
    message = models.TextField(verbose_name='Message', editable=False)
    client = models.ForeignKey(ListeClient, on_delete=models.CASCADE, verbose_name='Client', db_column='client')
    create_date = models.DateTimeField(verbose_name='Date')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'contact_message'




class ListeAttente(models.Model):
    name = models.CharField(max_length=255, verbose_name='id')
    client = models.ForeignKey(ListeClient, on_delete=models.CASCADE, verbose_name='Client', db_column='client')
    full_name = models.CharField(max_length=255, verbose_name='Nom et Prenom')
    email = models.CharField(max_length=255, verbose_name='Email')
    phone_number = models.CharField(max_length=255, verbose_name='Numero de telephone')
    car_model = models.ForeignKey(Modele, on_delete=models.CASCADE, verbose_name='Modele', db_column='car_model')
    lieu_depart = models.ForeignKey(Lieux, on_delete=models.CASCADE, related_name='departures',db_column='lieu_depart', verbose_name='Lieu de depart')
    date_depart = models.DateField(verbose_name='Date de depart')
    lieu_retour = models.ForeignKey(Lieux, on_delete=models.CASCADE, related_name='returns',db_column='lieu_retour', verbose_name='Lieu de retour')
    date_retour = models.DateField(verbose_name='Date de retour')
    heure_debut = models.CharField(max_length=5, verbose_name='Heure début')
    heure_fin = models.CharField(max_length=5, verbose_name='Heure Fin')
    heure_debut_float = models.FloatField(verbose_name='Heure début (float)', editable=False)
    heure_fin_float = models.FloatField(verbose_name='Heure Fin (float)', editable=False)

    def save(self, *args, **kwargs):
        self.heure_debut_float = self._convert_hour_to_float(self.heure_debut)
        self.heure_fin_float = self._convert_hour_to_float(self.heure_fin)
        super().save(*args, **kwargs)

    def _convert_hour_to_float(self, heure_str):
        if heure_str:
            try:
                time_obj = datetime.strptime(heure_str, '%H:%M')
                return time_obj.hour + time_obj.minute / 60
            except ValueError:
                raise ValidationError(f"L'heure {heure_str} n'est pas au format HH:MM")
        return 0.0

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'lite_atente'

#test
class ConditionAnnulation(models.Model):
    name = models.CharField(max_length=255, default='condition d annulation')
    haute_saison = models.ForeignKey(Saison, on_delete=models.SET_NULL, db_column='haute_saison', null=True, related_name='haute_saison')
    basse_saison = models.ForeignKey(Saison, on_delete=models.SET_NULL, db_column='basse_saison', null=True, related_name='basse_saison')
    haute_montant = models.IntegerField(verbose_name='Jour Haute saison')
    basse_montant = models.IntegerField(verbose_name='Jour Basse saison')

    def __str__(self):
        return self.name
    class Meta:
        db_table = 'condition_annulation'

from django.core.validators import MinValueValidator
class Payment(models.Model):
    name = models.CharField(max_length=255, unique=True, editable=False)
    reservation = models.ForeignKey(Reservation, db_column='reservation', on_delete=models.CASCADE,related_name='payments')
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE,db_column='vehicule', null=True, blank=True,related_name='vehicule')
    modele = models.ForeignKey(Modele, on_delete=models.CASCADE, db_column='modele', verbose_name="Modèle", related_name='modele')
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE,db_column='zone', verbose_name="Zone de livraison",related_name='zone')
    total_reduit_euro = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency_id = models.IntegerField(blank=True, null=True)
    montant = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    montant_dzd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    montant_eur_dzd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    montant_dzd_eur = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    total_reduit_dinar = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ecart_eur = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ecart_da = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    MODE_PAIEMENT_CHOICES = [
        ('carte', 'Banque'),
        ('liquide', 'Liquide'),
        ('autre', 'Autre'),
    ]
    mode_paiement = models.CharField(max_length=10, choices=MODE_PAIEMENT_CHOICES)
    total_encaisse = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    create_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f'PAY-{self.reservation.id}'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'revenue_record'


class HistoriqueSolde(models.Model):
    name = models.CharField(max_length=255)
    client = models.ForeignKey(ListeClient,db_column='client' ,on_delete=models.CASCADE, related_name='client')
    reservation = models.ForeignKey(Reservation,db_column='reservation', on_delete=models.CASCADE, related_name='historique_soldes')
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    create_date = models.DateTimeField()
    
    def __str__(self):
        return f"{self.name} - {self.client} - {self.montant}"
    class Meta:
        db_table = 'historique_solde'


class NewsLetter(models.Model):
    name = models.CharField(max_length=255, verbose_name='Name')
    email = models.EmailField(verbose_name='Email')
    SUBSCRIBE_CHOICES = [
        ('oui', 'Oui'),
        ('non', 'Non'),
    ]
    subscribe = models.CharField(max_length=3, choices=SUBSCRIBE_CHOICES, default='oui', verbose_name='Civilité')

    def __str__(self):
        return self.name
    class Meta:
        db_table = 'news_letter'



class RefundTable(models.Model):
    name = models.CharField(max_length=100, verbose_name='ref', editable=False)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE,db_column='reservation', verbose_name='Reservation')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Montant')
    STATUS_CHOICES = [
        ('en_attent', 'En attent'),
        ('effectuer', 'Effectué'),
        ('refuser', 'Refusé'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attent', verbose_name='Statut')
    date = models.DateTimeField(verbose_name='Date')

    class Meta:
        db_table = 'refund_table'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super(RefundTable, self).save(*args, **kwargs)
        if is_new:
            self.name = f'refund-{self.pk}'
            super(RefundTable, self).save(update_fields=['name'])

    def __str__(self):
        return self.name
    
class Prolongation(models.Model):
    STAGE_CHOICES = [
        ('en_attend', 'En Attend'),
        ('confirme', 'Confirmé'),
    ]
    
    name = models.CharField(
        max_length=255, 
        verbose_name='Name', 
        default='New',
        help_text='Nom de la prolongation'
    )
    effectuer_par = models.ForeignKey(
        Users,  
        on_delete=models.CASCADE,
        verbose_name='effectuer_par',
        db_column='effectuer_par',
        related_name='prolongationss'
    )
    
    stage = models.CharField(
        max_length=20,
        choices=STAGE_CHOICES,
        default='en_attend',
        verbose_name='Status'
    )
    reservation = models.ForeignKey(
        Reservation,  
        on_delete=models.CASCADE,
        verbose_name='Réservation',
        db_column='reservation',
        related_name='prolongations'
    )
    
    status = models.CharField(
        max_length=50,
        verbose_name='Etat de confirmation',
        blank=True,
        null=True
    )
    
    etat_reservation = models.CharField(
        max_length=50,
        verbose_name='Etat de réservation',
        blank=True,
        null=True
    )
    
    date_heure_debut = models.DateTimeField(
        verbose_name='Date heure début',
        null=True,
        blank=True
    )
    
    date_heure_fin = models.DateTimeField(
        verbose_name='Date heure fin',
        null=True,
        blank=True
    )
    
    nbr_jour_reservation = models.IntegerField(
        verbose_name='Durée (jours)',
        null=True,
        blank=True
    )
    
    duree_dereservation = models.CharField(
        max_length=100,
        verbose_name='Durée',
        blank=True,
        null=True
    )
    
    lieu_depart = models.ForeignKey(
        Lieux,  
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Lieu de départ',
        db_column='lieu_depart',
        related_name='prolongations_depart'
    )
    
    zone = models.ForeignKey(
        Zone,  
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Zone de départ',
        db_column='zone',
        related_name='prolongations_zone'
    )
    
    lieu_retour = models.ForeignKey(
        Lieux,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Lieu de retour',
        db_column='lieu_retour',
        related_name='prolongations_retour'
    )
    
    vehicule = models.ForeignKey(
        Vehicule,  
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Véhicule',
        db_column='vehicule',
        related_name='prolongations'
    )
    
    modele = models.ForeignKey(
        Modele,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Modèle',
        db_column='modele',
        related_name='prolongations'
    )
    
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Catégorie',
        db_column='categorie',
        related_name='prolongations'
    )
    
    prix_jour = models.IntegerField(
        verbose_name='Prix par jour',
        default=0
    )
    
    prix_jour_two = models.IntegerField(
        verbose_name='Prix Jour Two',
        default=0
    )
    
    nbr_jour_two = models.IntegerField(
        verbose_name='Nombre de Jours Two',
        default=0
    )
    
    nbr_jour_one = models.IntegerField(
        verbose_name='Nombre de Jours One',
        default=0
    )
    
    frais_de_livraison = models.IntegerField(
        verbose_name='Frais de livraison',
        default=0
    )
    
    options_total = models.IntegerField(
        verbose_name='Total des options',
        default=0
    )
    
    total = models.IntegerField(
        verbose_name='Total Général',
        default=0
    )
    
    total_afficher = models.IntegerField(
        verbose_name='Total Afficher',
        default=0
    )
    
    prix_jour_afficher = models.FloatField(
        verbose_name='Prix par jour Afficher',
        default=0.0
    )
    
    supplements = models.IntegerField(
        verbose_name='Suppléments',
        default=0
    )
    
    retour_tard = models.IntegerField(
        verbose_name='Retour tard',
        default=0
    )
    
    date_prolonge = models.DateTimeField(
        verbose_name='Date prolongée',
        null=True,
        blank=True
    )
    
    nb_jour_prolonge = models.IntegerField(
        verbose_name='Jour prolongé',
        default=0,
        editable=False  
    )
    
    heure_prolonge = models.IntegerField(
        verbose_name='Heure prolongé',
        default=0,
        editable=False  
    )
    
    nb_jour_prolonge_l = models.CharField(
        max_length=50,
        verbose_name='Jour prolongé (libellé)',
        blank=True,
        editable=False
    )
    
    heure_prolonge_l = models.CharField(
        max_length=50,
        verbose_name='Heure prolongé (libellé)',
        blank=True,
        editable=False
    )
    
    prix_prolongation = models.IntegerField(
        verbose_name='Prix de prolongation',
        default=0,
        editable=False
    )
    
    total_option_prolonge = models.IntegerField(
        verbose_name='Total options prolongées',
        default=0,
        editable=False
    )
    
    total_prolongation = models.IntegerField(
        verbose_name='Total Prolongation',
        default=0,
        editable=False
    )
    
    supplements_prolonge = models.IntegerField(
        verbose_name='Suppléments Prolongés',
        default=0,
        editable=False
    )
    
    date_fin_un = models.DateTimeField(
        verbose_name='Ancienne date fin',
        null=True,
        blank=True
    )
    
    prix_prolongation_devise = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Prix de prolongation (devise)',
        default=0.00,
        editable=False
    )

    date_du_au = models.CharField()
    date_du_au_new = models.CharField()
    date_prolongation = models.DateTimeField()
    
    class Meta:
        db_table = 'prolongation'
        managed = False  

class RetourAvance(models.Model):
    
    name = models.CharField(max_length=255, verbose_name='Nom', null=True, blank=True)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, db_column='reservation', verbose_name='Reservation')
    lieu_depart = models.ForeignKey(Lieux, on_delete=models.CASCADE, db_column='lieu_depart', verbose_name='lieu_depart')
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, db_column='zone', verbose_name='zone')
    lieu_retour = models.ForeignKey(Lieux, on_delete=models.CASCADE, db_column='lieu_retour', verbose_name='lieu_retour')
    
    date_retour_avance = models.DateTimeField(
        verbose_name='Date de retour avance', 
        null=True, 
        blank=True,
        help_text='Date prévue pour le retour anticipé'
    )
    effectuer_par = models.ForeignKey(
        Users,  
        on_delete=models.CASCADE,
        verbose_name='effectuer_par',
        db_column='effectuer_par',
        related_name='prolongationss'
    )
    
    differance_heure = models.IntegerField(
        verbose_name='Différence Heure',
        default=0,
        help_text='Différence en heures par rapport à la date de fin prévue'
    )
    
    date_du_au = models.CharField(
        max_length=255,
        verbose_name='Anciennes dates',
        blank=True,
        null=True,
        help_text='Dates originales de la réservation'
    )
    
    date_du_au_new = models.CharField(
        max_length=255,
        verbose_name='Nouvelles dates',
        blank=True,
        null=True,
        help_text='Nouvelles dates après modification'
    )
    
    date_retour_avance = models.DateTimeField(
        verbose_name='Date de prolongation',
        null=True,
        blank=True,
        help_text='Date à laquelle la modification a été effectuée'
    )
    prix_retour_avance = models.FloatField()

    class Meta:
        verbose_name = 'Retour Avancé'
        db_table = 'retour_avance'

    def __str__(self):
        return f"- {self.name or f'Réservation {self.reservation.name}'}"
    
class BlockCar(models.Model):
    vehicule = models.ForeignKey(
        Vehicule,
        on_delete=models.CASCADE,
        verbose_name="Véhicule à bloquer",
        related_name="blocks"
    )
    date_from = models.DateField(verbose_name="Du")
    date_to = models.DateField(verbose_name="Au")
    reason = models.TextField(verbose_name="Raison du blocage")
    class Meta:
        verbose_name = 'Blocker un vehicule'
        db_table = 'block_car'

class ReservationCorrection(models.Model):
    # Relations Many2one -> ForeignKey
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        db_column='reservation',
        related_name="corrections",
        verbose_name="Réservation"
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('en_attend', 'En attente'),
            ('rejete', 'Rejeté'),
            ('annule', 'Annulé'),
            ('confirmee', 'Confirmé'),
        ],
        verbose_name="État confirmation",
        blank=True,
        null=True
    )

    date_depart = models.DateField(verbose_name="Date départ", blank=True, null=True)
    date_retour = models.DateField(verbose_name="Date retour", blank=True, null=True)
    heure_depart = models.CharField(max_length=10, verbose_name="Heure départ", blank=True, null=True)
    heure_retour = models.CharField(max_length=10, verbose_name="Heure retour", blank=True, null=True)

    vehicule = models.ForeignKey(
        Vehicule,
        on_delete=models.SET_NULL,
        db_column='vehicule',
        related_name="corrections",
        verbose_name="Véhicule",
        blank=True,
        null=True
    )

    status_new = models.CharField(
        max_length=20,
        choices=[
            ('en_attend', 'En attente'),
            ('rejete', 'Rejeté'),
            ('annule', 'Annulé'),
            ('confirmee', 'Confirmé'),
        ],
        verbose_name="Nouvel état confirmation",
        blank=True,
        null=True
    )

    date_depart_new = models.DateField(verbose_name="Nouvelle date départ", blank=True, null=True)
    date_retour_new = models.DateField(verbose_name="Nouvelle date retour", blank=True, null=True)
    heure_depart_new = models.CharField(max_length=10, verbose_name="Nouvelle heure départ", blank=True, null=True)
    heure_retour_new = models.CharField(max_length=10, verbose_name="Nouvelle heure retour", blank=True, null=True)

    vehicule_new = models.ForeignKey(
        Vehicule,
        on_delete=models.SET_NULL,
        db_column='vehicule_new',
        related_name="corrections_new",
        verbose_name="Nouveau véhicule",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'reservation correction'
        db_table = 'reservation_correction'
