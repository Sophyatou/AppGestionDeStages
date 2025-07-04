from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

class UserProfile(models.Model):
    USER_TYPES = (
        ('etudiant', _('Étudiant')),
        ('responsable', _('Responsable')),
        ('entreprise', _('Entreprise')),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    photo = models.ImageField(upload_to='photos/', null=True, blank=True, verbose_name=_('Photo de profil'))
    telephone = models.CharField(_("Téléphone"), max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Profil utilisateur')
        verbose_name_plural = _('Profils utilisateurs')

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_user_type_display()}"

    def clean(self):
        if self.user_type == 'etudiant' and not hasattr(self, 'etudiant'):
            raise ValidationError(_('Un profil étudiant doit avoir un profil étudiant associé.'))
        elif self.user_type == 'responsable' and not hasattr(self, 'responsable'):
            raise ValidationError(_('Un profil responsable doit avoir un profil responsable associé.'))
        elif self.user_type == 'entreprise' and not hasattr(self, 'entreprise'):
            raise ValidationError(_('Un profil entreprise doit avoir un profil entreprise associé.'))

class Etudiant(models.Model):
    FILIERES = (
        ('informatique', _('Informatique')),
        ('gestion', _('Gestion')),
        ('marketing', _('Marketing')),
        ('finance', _('Finance')),
        ('rh', _('Ressources Humaines')),
    )

    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='etudiant', null=True, blank=True)
    filiere = models.CharField(max_length=100, blank=True)
    GENRE_CHOICES = (
        ('M', 'Homme'),
        ('F', 'Femme'),
        ('A', 'Autre'),
    )
    genre = models.CharField(max_length=1, choices=GENRE_CHOICES, default='M')
    niveau = models.CharField(_("Niveau d'étude"), max_length=50, blank=True, null=True)
    cv = models.FileField(upload_to='cv/', blank=True, null=True, verbose_name=_("CV"))
    lettre_motivation = models.FileField(upload_to='lettres/', blank=True, null=True, verbose_name=_("Lettre de motivation"))
    date_inscription = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = _('Étudiant')
        verbose_name_plural = _('Étudiants')

    def __str__(self):
        if self.user_profile and self.user_profile.user:
            return self.user_profile.user.get_full_name()
        return "Étudiant (profil en attente)"

    def clean(self):
        if self.user_profile and self.user_profile.user_type != 'etudiant':
            raise ValidationError(_('Le profil associé doit être de type étudiant.'))

class Responsable(models.Model):
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='responsable', null=True)
    departement = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    date_inscription = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = _('Responsable')
        verbose_name_plural = _('Responsables')

    def __str__(self):
        return f"{self.profile.user.get_full_name()} - {self.departement}"

    def clean(self):
        if self.profile.user_type != 'responsable':
            raise ValidationError(_('Le profil associé doit être de type responsable.'))

class Entreprise(models.Model):
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='entreprise', null=True)
    nom = models.CharField(max_length=200)
    secteur_activite = models.CharField(max_length=100)
    adresse = models.TextField()
    telephone = models.CharField(max_length=20)
    site_web = models.URLField(blank=True)
    description = models.TextField()
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    date_inscription = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = _('Entreprise')
        verbose_name_plural = _('Entreprises')

    def __str__(self):
        return self.nom

    def clean(self):
        if self.profile.user_type != 'entreprise':
            raise ValidationError(_('Le profil associé doit être de type entreprise.'))

class Stage(models.Model):
    TYPE_CHOICES = [
        ('initiation', _('Initiation')),
        ('perfectionnement', _('Perfectionnement')),
        ('pfe', _('Projet de Fin d\'Études')),
    ]

    DUREE_CHOICES = [
        ('1-2', _('1-2 mois')),
        ('3-4', _('3-4 mois')),
        ('5-6', _('5-6 mois')),
    ]

    titre = models.CharField(_('Titre du stage'), max_length=200)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='stages')
    type_stage = models.CharField(_('Type de stage'), max_length=20, choices=TYPE_CHOICES)
    duree = models.CharField(_('Durée'), max_length=10, choices=DUREE_CHOICES)
    description = models.TextField(_('Description'))
    competences_requises = models.TextField(_('Compétences requises'))
    remuneration = models.DecimalField(_('Rémunération'), max_digits=10, decimal_places=2, null=True, blank=True)
    date_debut = models.DateField(_('Date de début'))
    date_fin = models.DateField(_('Date de fin'))
    nombre_places = models.PositiveIntegerField(_('Nombre de places'), default=1)
    date_publication = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)
    est_actif = models.BooleanField(_('Actif'), default=True)

    class Meta:
        verbose_name = _('Stage')
        verbose_name_plural = _('Stages')
        ordering = ['-date_publication']

    def __str__(self):
        return f"{self.titre} - {self.entreprise.nom}"

class Candidature(models.Model):
    STATUT_CHOICES = [
        ('en_attente', _('En attente')),
        ('acceptee', _('Acceptée')),
        ('refusee', _('Refusée')),
        ('annulee', _('Annulée')),
    ]

    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name='candidatures')
    etudiant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='candidatures')
    cv = models.FileField(_('CV'), upload_to='cvs/')
    lettre_motivation = models.FileField(_('Lettre de motivation'), upload_to='lettres/')
    statut = models.CharField(_('Statut'), max_length=20, choices=STATUT_CHOICES, default='en_attente')
    date_candidature = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)
    commentaire = models.TextField(_('Commentaire'), blank=True)

    class Meta:
        verbose_name = _('Candidature')
        verbose_name_plural = _('Candidatures')
        unique_together = ['stage', 'etudiant']

    def __str__(self):
        return f"{self.etudiant.get_full_name()} - {self.stage.titre}"

class Rapport(models.Model):
    candidature = models.OneToOneField(Candidature, on_delete=models.CASCADE, related_name='rapport')
    fichier = models.FileField(_('Rapport'), upload_to='rapports/')
    date_soumission = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)
    note = models.DecimalField(_('Note'), max_digits=4, decimal_places=2, null=True, blank=True)
    commentaire = models.TextField(_('Commentaire'), blank=True)

    class Meta:
        verbose_name = _('Rapport')
        verbose_name_plural = _('Rapports')

    def __str__(self):
        return f"Rapport de {self.candidature.etudiant.get_full_name()} - {self.candidature.stage.titre}"

class FicheStage(models.Model):
    """Modèle pour la fiche de stage"""
    etudiant = models.OneToOneField('Etudiant', on_delete=models.CASCADE, related_name='fiche_stage')
    titre = models.CharField(_("Titre du stage"), max_length=200)
    entreprise = models.ForeignKey('Entreprise', on_delete=models.CASCADE)
    encadrant = models.CharField(_("Nom de l'encadrant"), max_length=100)
    email_encadrant = models.EmailField(_("Email de l'encadrant"))
    telephone_encadrant = models.CharField(_("Téléphone de l'encadrant"), max_length=20)
    mission = models.TextField(_("Description de la mission"))
    date_debut = models.DateField(_("Date de début"))
    date_fin = models.DateField(_("Date de fin"))
    date_soutenance = models.DateField(_("Date de soutenance"), null=True, blank=True)
    technologies = models.CharField(_("Technologies utilisées"), max_length=200)
    commentaires = models.TextField(_("Commentaires"), blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Fiche de stage")
        verbose_name_plural = _("Fiches de stage")

    def __str__(self):
        return f"Fiche de stage - {self.etudiant}"

class Document(models.Model):
    """Modèle pour les documents de stage"""
    TYPE_CHOICES = [
        ('convention', _('Convention de stage')),
        ('rapport', _('Rapport de stage')),
        ('presentation', _('Présentation')),
        ('attestation', _('Attestation de stage')),
        ('autre', _('Autre document')),
    ]

    etudiant = models.ForeignKey('Etudiant', on_delete=models.CASCADE, related_name='documents')
    type = models.CharField(_("Type de document"), max_length=20, choices=TYPE_CHOICES)
    titre = models.CharField(_("Titre"), max_length=200)
    fichier = models.FileField(_("Fichier"), upload_to='documents/')
    description = models.TextField(_("Description"), blank=True)
    date_upload = models.DateTimeField(auto_now_add=True)
    valide = models.BooleanField(_("Validé"), default=False)

    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")
        ordering = ['-date_upload']

    def __str__(self):
        return f"{self.get_type_display()} - {self.etudiant}"

class Notification(models.Model):
    """Modèle pour les notifications"""
    TYPE_CHOICES = [
        ('info', _('Information')),
        ('success', _('Succès')),
        ('warning', _('Avertissement')),
        ('error', _('Erreur')),
    ]

    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    titre = models.CharField(_("Titre"), max_length=200)
    message = models.TextField(_("Message"))
    type = models.CharField(_("Type"), max_length=20, choices=TYPE_CHOICES, default='info')
    lien = models.CharField(_("Lien"), max_length=200, blank=True)
    lue = models.BooleanField(_("Lue"), default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.titre} - {self.destinataire}"

class Message(models.Model):
    expediteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_envoyes')
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_recus')
    sujet = models.CharField(max_length=200)
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sujet} ({self.expediteur} → {self.destinataire})"
