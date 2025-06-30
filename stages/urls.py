from django.urls import path
from . import views

app_name = 'stages'

urlpatterns = [
    path('', views.home, name='home'),
    path('stage/<int:pk>/', views.stage_detail, name='stage_detail'),
    path('stage/<int:stage_pk>/candidater/', views.candidature_create, name='candidature_create'),
    path('mes-candidatures/', views.mes_candidatures, name='mes_candidatures'),
    
    # URLs pour l'inscription
    path('inscription/', views.signup_choice, name='signup_choice'),
    path('inscription/etudiant/', views.etudiant_signup, name='etudiant_signup'),
    path('inscription/responsable/', views.responsable_signup, name='responsable_signup'),
    path('inscription/entreprise/', views.entreprise_signup, name='entreprise_signup'),
    
    # URL pour le tableau de bord
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profil/', views.profil, name='profil'),
    path('stage/creer/', views.stage_create, name='stage_create'),
    path('stages/', views.stage_list, name='stage_list'),
    
    # Nouvelles URLs pour les fonctionnalités étudiant
    path('fiche-stage/', views.fiche_stage, name='fiche_stage'),
    path('documents/', views.documents, name='documents'),
    path('notifications/', views.notifications, name='notifications'),
    path('stage/<int:pk>/supprimer/', views.stage_delete, name='stage_delete'),
    path('stage/<int:pk>/modifier/', views.stage_update, name='stage_update'),
    
    # URLs pour la gestion des candidatures par l'entreprise
    path('candidatures/', views.candidatures_list, name='candidatures_list'),
    path('candidature/<int:pk>/', views.candidature_detail, name='candidature_detail'),
    path('candidature/<int:pk>/statut/<str:nouveau_statut>/', views.candidature_update_status, name='candidature_update_status'),
    path('contact/etudiant/<int:pk>/', views.contact_etudiant, name='contact_etudiant'),
    path('profil-entreprise/', views.entreprise_profile, name='entreprise_profile'),
    path('messages/', views.messages_list, name='messages'),
] 