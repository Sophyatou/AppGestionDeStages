from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import UserProfile, Etudiant, Responsable, Entreprise, Stage, Candidature, Rapport

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'created_at')
    list_filter = ('user_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')

@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'filiere', 'niveau', 'date_inscription')
    search_fields = ('user_profile__user__username', 'user_profile__user__first_name', 'user_profile__user__last_name', 'filiere')
    list_filter = ('filiere', 'niveau', 'date_inscription')

@admin.register(Responsable)
class ResponsableAdmin(admin.ModelAdmin):
    list_display = ('profile', 'departement', 'telephone', 'date_inscription')
    list_filter = ('departement', 'date_inscription')
    search_fields = ('profile__user__username', 'profile__user__email', 'profile__user__first_name', 'profile__user__last_name')

@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'secteur_activite', 'telephone', 'site_web', 'date_inscription')
    list_filter = ('secteur_activite', 'date_inscription')
    search_fields = ('nom', 'secteur_activite', 'description')

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('titre', 'entreprise', 'type_stage', 'duree', 'date_debut', 'date_fin', 'est_actif')
    list_filter = ('type_stage', 'duree', 'est_actif', 'date_publication')
    search_fields = ('titre', 'description', 'entreprise__nom')
    date_hierarchy = 'date_publication'

@admin.register(Candidature)
class CandidatureAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'stage', 'statut', 'date_candidature')
    list_filter = ('statut', 'date_candidature')
    search_fields = ('etudiant__username', 'stage__titre', 'commentaire')
    date_hierarchy = 'date_candidature'

@admin.register(Rapport)
class RapportAdmin(admin.ModelAdmin):
    list_display = ('candidature', 'date_soumission', 'note')
    list_filter = ('date_soumission',)
    search_fields = ('candidature__etudiant__username', 'candidature__stage__titre', 'commentaire')
    date_hierarchy = 'date_soumission'
