from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from .models import Stage, Candidature, UserProfile, Etudiant, Responsable, Entreprise, FicheStage, Document, Notification, Message
from .forms import StageForm, CandidatureForm, EtudiantSignUpForm, ResponsableSignUpForm, EntrepriseSignUpForm, FicheStageForm, DocumentForm, EtudiantProfileForm, UserProfileForm, UserEditForm, EntrepriseProfileForm
from django.contrib.auth import login
from django.contrib.auth import get_backends
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone
from django import forms
from datetime import datetime
from django.db.models.functions import TruncMonth
from django.db.models import Count
import calendar
from django.core.mail import send_mail

def home(request):
    if request.user.is_authenticated:
        return redirect('stages:dashboard')
    """Vue pour la page d'accueil avec la liste des stages actifs"""
    stages = Stage.objects.filter(est_actif=True)
    
    # Filtres
    query = request.GET.get('q')
    type_stage = request.GET.get('type')
    duree = request.GET.get('duree')
    
    if query:
        stages = stages.filter(
            Q(titre__icontains=query) |
            Q(description__icontains=query) |
            Q(entreprise__nom__icontains=query)
        )
    
    if type_stage:
        stages = stages.filter(type_stage=type_stage)
    
    if duree:
        stages = stages.filter(duree=duree)
    
    # Pagination
    paginator = Paginator(stages, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'type_choices': Stage.TYPE_CHOICES,
        'duree_choices': Stage.DUREE_CHOICES,
    }
    return render(request, 'stages/home.html', context)

def stage_list(request):
    """Vue pour la page d'accueil avec la liste des stages actifs"""
    user = request.user
    if user.is_authenticated and hasattr(user, 'profile') and user.profile.user_type == 'entreprise' and hasattr(user.profile, 'entreprise'):
        # L'entreprise ne voit que ses offres
        stages = Stage.objects.filter(est_actif=True, entreprise=user.profile.entreprise)
    else:
        # Les autres voient toutes les offres actives
        stages = Stage.objects.filter(est_actif=True)
    
    # Filtres
    query = request.GET.get('q')
    type_stage = request.GET.get('type')
    duree = request.GET.get('duree')
    
    if query:
        stages = stages.filter(
            Q(titre__icontains=query) |
            Q(description__icontains=query) |
            Q(entreprise__nom__icontains=query)
        )
    
    if type_stage:
        stages = stages.filter(type_stage=type_stage)
    
    if duree:
        stages = stages.filter(duree=duree)
    
    # Pagination
    paginator = Paginator(stages, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'type_choices': Stage.TYPE_CHOICES,
        'duree_choices': Stage.DUREE_CHOICES,
    }
    return render(request, 'stages/stage_list.html', context)

def stage_detail(request, pk):
    """Vue pour afficher les détails d'un stage"""
    stage = get_object_or_404(Stage, pk=pk)
    context = {
        'stage': stage,
        'can_apply': request.user.is_authenticated and not Candidature.objects.filter(
            stage=stage, etudiant=request.user
        ).exists()
    }
    return render(request, 'stages/stage_detail.html', context)

@login_required
def stage_create(request):
    """Vue pour créer un nouveau stage (offre)"""
    user_profile = request.user.profile
    if user_profile.user_type != 'entreprise' or not hasattr(user_profile, 'entreprise'):
        messages.error(request, _("Vous n'avez pas le droit de créer une offre."))
        return redirect('stages:dashboard')
    entreprise = user_profile.entreprise
    if request.method == 'POST':
        form = StageForm(request.POST)
        if form.is_valid():
            stage = form.save(commit=False)
            stage.entreprise = entreprise
            stage.save()
            messages.success(request, _('Stage créé avec succès !'))
            return redirect('stages:dashboard')
    else:
        form = StageForm(initial={'entreprise': entreprise.pk})
        form.fields['entreprise'].widget = forms.HiddenInput()
    return render(request, 'stages/stage_form.html', {'form': form, 'action': _('Créer')})

@login_required
def stage_update(request, pk):
    """Vue pour modifier un stage existant"""
    stage = get_object_or_404(Stage, pk=pk)
    if request.method == 'POST':
        form = StageForm(request.POST, instance=stage)
        if form.is_valid():
            form.save()
            messages.success(request, _('Stage mis à jour avec succès !'))
            return redirect('stages:stage_detail', pk=stage.pk)
    else:
        form = StageForm(instance=stage)
    
    return render(request, 'stages/stage_form.html', {'form': form, 'action': _('Modifier')})

@login_required
def stage_delete(request, pk):
    stage = get_object_or_404(Stage, pk=pk)
    user_profile = request.user.profile
    if user_profile.user_type != 'entreprise' or not hasattr(user_profile, 'entreprise') or stage.entreprise != user_profile.entreprise:
        messages.error(request, _("Vous n'avez pas le droit de supprimer cette offre."))
        return redirect('stages:dashboard')
    if request.method == 'POST':
        stage.delete()
        messages.success(request, _("Offre supprimée avec succès."))
        return redirect('stages:dashboard')
    return render(request, 'stages/stage_confirm_delete.html', {'stage': stage})

@login_required
def candidature_create(request, stage_pk):
    """Vue pour créer une nouvelle candidature"""
    stage = get_object_or_404(Stage, pk=stage_pk)
    
    if Candidature.objects.filter(stage=stage, etudiant=request.user).exists():
        messages.error(request, _('Vous avez déjà postulé à ce stage.'))
        return redirect('stages:stage_detail', pk=stage_pk)
    
    if request.method == 'POST':
        form = CandidatureForm(request.POST, request.FILES)
        if form.is_valid():
            candidature = form.save(commit=False)
            candidature.stage = stage
            candidature.etudiant = request.user
            candidature.save()
            # Notification automatique à l'étudiant
            Notification.objects.create(
                destinataire=request.user,
                titre=_('Candidature envoyée'),
                message=_('Votre candidature pour le stage "{}" est en cours de traitement par l\'entreprise.').format(stage.titre)
            )
            messages.success(request, _('Candidature envoyée avec succès !'))
            return redirect('stages:stage_detail', pk=stage_pk)
    else:
        form = CandidatureForm()
    
    return render(request, 'stages/candidature_form.html', {
        'form': form,
        'stage': stage,
        'action': _('Postuler')
    })

@login_required
def mes_candidatures(request):
    """Vue pour afficher les candidatures de l'utilisateur"""
    candidatures = Candidature.objects.filter(etudiant=request.user)
    return render(request, 'stages/mes_candidatures.html', {'candidatures': candidatures})

def signup_choice(request):
    """Vue pour choisir le type d'inscription"""
    return render(request, 'stages/signup_choice.html')

def etudiant_signup(request):
    """Vue pour l'inscription des étudiants"""
    if request.method == 'POST':
        form = EtudiantSignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            user.backend = 'stages.backends.MultiFieldModelBackend'
            login(request, user)
            messages.success(request, _('Inscription réussie ! Bienvenue.'))
            return redirect('stages:dashboard')
    else:
        form = EtudiantSignUpForm()
    return render(request, 'stages/signup.html', {'form': form, 'user_type': 'etudiant'})

def responsable_signup(request):
    """Vue pour l'inscription des responsables"""
    if request.method == 'POST':
        form = ResponsableSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.backend = 'stages.backends.MultiFieldModelBackend'
            login(request, user)
            messages.success(request, _('Inscription réussie ! Bienvenue.'))
            return redirect('stages:dashboard')
    else:
        form = ResponsableSignUpForm()
    return render(request, 'stages/signup.html', {'form': form, 'user_type': 'responsable'})

def entreprise_signup(request):
    """Vue pour l'inscription des entreprises"""
    if request.method == 'POST':
        form = EntrepriseSignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            user.backend = 'stages.backends.MultiFieldModelBackend'
            login(request, user)
            messages.success(request, _('Inscription réussie ! Bienvenue.'))
            return redirect('stages:dashboard')
    else:
        form = EntrepriseSignUpForm()
    return render(request, 'stages/signup.html', {'form': form, 'user_type': 'entreprise'})

@login_required
def dashboard(request):
    user = request.user
    user_profile = user.profile
    template = ''
    context = {}

    if user_profile.user_type == 'etudiant':
        etudiant_profile = get_object_or_404(Etudiant, user_profile=user_profile)
        
        candidatures = Candidature.objects.filter(etudiant=request.user)
        candidatures_recentes = candidatures.order_by('-date_candidature')[:5]
        # Filtrer les offres par filière de l'étudiant
        offres_disponibles = Stage.objects.filter(est_actif=True, entreprise__secteur_activite__iexact=etudiant_profile.filiere)
        
        # Statistiques des candidatures
        total_candidatures = candidatures.count()
        en_attente_count = candidatures.filter(statut='en_attente').count()
        acceptee_count = candidatures.filter(statut='acceptee').count()
        refusee_count = candidatures.filter(statut='refusee').count()
        
        stage_actif = Stage.objects.filter(candidatures__etudiant=request.user, candidatures__statut='acceptee', date_fin__gte=timezone.now()).distinct().first()
        
        notifications = Notification.objects.filter(destinataire=user).order_by('-date_creation')
        notifications_non_lues = notifications.filter(lue=False).count()

        stages_postules = list(candidatures.values_list('stage_id', flat=True))
        # Statut étudiant
        statut_etudiant = "En stage" if stage_actif else "En recherche"
        context = {
            'etudiant': etudiant_profile,
            'candidatures_recentes': candidatures_recentes,
            'offres_disponibles': offres_disponibles,
            'stages_postules': stages_postules,
            'stage_actif': stage_actif,
            'statut_etudiant': statut_etudiant,
            'today': timezone.now(),
            'notifications': notifications,
            'notifications_non_lues': notifications_non_lues,
            'total_candidatures': total_candidatures,
            'en_attente_count': en_attente_count,
            'acceptee_count': acceptee_count,
            'refusee_count': refusee_count,
        }
        template = 'stages/dashboard_etudiant.html'

    elif user_profile.user_type == 'responsable':
        responsable = user_profile.responsable
        stages = Stage.objects.all()
        etudiants_sans_stage = Etudiant.objects.filter(profile__user__candidatures__isnull=True)
        nb_entreprises = stages.values_list('entreprise', flat=True).distinct().count()
        context = {
            'stages': stages,
            'etudiants_sans_stage': etudiants_sans_stage,
            'responsable': responsable,
            'nb_entreprises': nb_entreprises,
        }
        template = 'stages/dashboard_responsable.html'
    
    elif user_profile.user_type == 'entreprise':
        if hasattr(user_profile, 'entreprise') and user_profile.entreprise:
            entreprise_profile = user_profile.entreprise
            offres_recentes = Stage.objects.filter(entreprise=entreprise_profile).order_by('-date_publication')[:5]
            candidatures_recues = Candidature.objects.filter(stage__entreprise=entreprise_profile).order_by('-date_candidature')[:5]
            offres_actives_count = Stage.objects.filter(entreprise=entreprise_profile, est_actif=True).count()
            offres_pourvues_count = Stage.objects.filter(entreprise=entreprise_profile, est_actif=False).count()
            candidatures_count = Candidature.objects.filter(stage__entreprise=entreprise_profile).count()
            now = timezone.now()
            # Candidatures du mois courant (tous genres)
            candidatures_mois_count = Candidature.objects.filter(stage__entreprise=entreprise_profile, date_candidature__year=now.year, date_candidature__month=now.month).count()
            # Candidatures femmes du mois courant
            candidatures_femmes_mois = Candidature.objects.filter(
                stage__entreprise=entreprise_profile,
                date_candidature__year=now.year,
                date_candidature__month=now.month,
                etudiant__profile__etudiant__genre='F'
            ).count()
            # Candidatures hommes du mois courant
            candidatures_hommes_mois = Candidature.objects.filter(
                stage__entreprise=entreprise_profile,
                date_candidature__year=now.year,
                date_candidature__month=now.month,
                etudiant__profile__etudiant__genre='M'
            ).count()
            # Calcul des pourcentages H/F du mois courant
            total_candidatures_genre_mois = candidatures_femmes_mois + candidatures_hommes_mois
            pourcentage_femmes_mois = round((candidatures_femmes_mois / total_candidatures_genre_mois * 100) if total_candidatures_genre_mois > 0 else 0)
            pourcentage_hommes_mois = round((candidatures_hommes_mois / total_candidatures_genre_mois * 100) if total_candidatures_genre_mois > 0 else 0)
            
            messages_non_lus = Notification.objects.filter(destinataire=user, lue=False).count() if 'Notification' in globals() else 0
            
            # Récupérer les candidatures récentes (limité à 5)
            candidatures_recentes = Candidature.objects.filter(
                stage__entreprise=entreprise_profile
            ).select_related(
                'etudiant',
                'stage'
            ).order_by('-date_candidature')[:5]
            
            context = {
                'entreprise': entreprise_profile,
                'offres_actives_count': offres_actives_count,
                'offres_pourvues_count': offres_pourvues_count,
                'candidatures_count': candidatures_count,
                'candidatures_mois_count': candidatures_mois_count,
                'messages_non_lus': messages_non_lus,
                'candidatures_recentes': candidatures_recentes,
                # Ajout pour le graphique H/F du mois
                'candidatures_femmes_mois': candidatures_femmes_mois,
                'candidatures_hommes_mois': candidatures_hommes_mois,
                'pourcentage_femmes_mois': pourcentage_femmes_mois,
                'pourcentage_hommes_mois': pourcentage_hommes_mois,
            }
        template = 'stages/dashboard_entreprise.html'

    return render(request, template, context)

@login_required
def fiche_stage(request):
    """Vue pour gérer la fiche de stage de l'étudiant"""
    try:
        fiche = FicheStage.objects.get(etudiant=request.user.profile.etudiant)
    except FicheStage.DoesNotExist:
        fiche = None
    
    if request.method == 'POST':
        form = FicheStageForm(request.POST, instance=fiche)
        if form.is_valid():
            fiche = form.save(commit=False)
            fiche.etudiant = request.user.profile.etudiant
            fiche.save()
            messages.success(request, _('Fiche de stage mise à jour avec succès.'))
            return redirect('stages:dashboard')
    else:
        form = FicheStageForm(instance=fiche)
    
    return render(request, 'stages/fiche_stage.html', {
        'form': form,
        'fiche': fiche
    })

@login_required
def documents(request):
    """Vue pour gérer les documents de l'étudiant"""
    documents = Document.objects.filter(etudiant=request.user.profile.etudiant)
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.etudiant = request.user.profile.etudiant
            document.save()
            messages.success(request, _('Document téléversé avec succès.'))
            return redirect('stages:documents')
    else:
        form = DocumentForm()
    
    return render(request, 'stages/documents.html', {
        'documents': documents,
        'form': form
    })

@login_required
def notifications(request):
    """Vue pour afficher les notifications de l'étudiant"""
    notifications = Notification.objects.filter(
        destinataire=request.user
    ).order_by('-date_creation')
    
    # Marquer toutes les notifications comme lues
    notifications.filter(lue=False).update(lue=True)
    
    return render(request, 'stages/notifications.html', {
        'notifications': notifications
    })

@login_required
def profil(request):
    """Vue pour gérer le profil de l'étudiant"""
    user = request.user
    user_profile = user.profile
    etudiant_instance = user_profile.etudiant

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        etudiant_form = EtudiantProfileForm(request.POST, request.FILES, instance=etudiant_instance)

        if user_form.is_valid() and profile_form.is_valid() and etudiant_form.is_valid():
            user_form.save()
            profile_form.save()
            etudiant_form.save()
            messages.success(request, _('Profil mis à jour avec succès.'))
            return redirect('stages:dashboard')
    else:
        user_form = UserEditForm(instance=user)
        profile_form = UserProfileForm(instance=user_profile)
        etudiant_form = EtudiantProfileForm(instance=etudiant_instance)

    return render(request, 'stages/profil.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'etudiant_form': etudiant_form,
        'user_profile': user_profile
    })

@login_required
def candidatures_list(request):
    """Vue pour afficher toutes les candidatures reçues par l'entreprise"""
    user_profile = request.user.profile
    if user_profile.user_type != 'entreprise':
        messages.error(request, _("Vous n'avez pas accès à cette page."))
        return redirect('stages:dashboard')
    
    entreprise = user_profile.entreprise
    candidatures = Candidature.objects.filter(
        stage__entreprise=entreprise
    ).select_related(
        'etudiant',
        'stage'
    ).order_by('-date_candidature')

    # Filtres
    statut = request.GET.get('statut')
    stage = request.GET.get('stage')
    search = request.GET.get('search')

    if statut:
        candidatures = candidatures.filter(statut=statut)
    if stage:
        candidatures = candidatures.filter(stage_id=stage)
    if search:
        candidatures = candidatures.filter(
            Q(etudiant__user_profile__user__first_name__icontains=search) |
            Q(etudiant__user_profile__user__last_name__icontains=search) |
            Q(stage__titre__icontains=search)
        )

    # Statistiques
    total_candidatures = candidatures.count()
    en_attente_count = candidatures.filter(statut='en_attente').count()
    acceptees_count = candidatures.filter(statut='acceptee').count()
    refusees_count = candidatures.filter(statut='refusee').count()

    context = {
        'candidatures': candidatures,
        'total_candidatures': total_candidatures,
        'en_attente_count': en_attente_count,
        'acceptees_count': acceptees_count,
        'refusees_count': refusees_count,
        'stages': Stage.objects.filter(entreprise=entreprise),
        'statut_choices': Candidature.STATUT_CHOICES,
        'selected_statut': statut,
        'selected_stage': stage,
        'search': search,
    }
    return render(request, 'stages/candidatures_list.html', context)

@login_required
def candidature_detail(request, pk):
    """Vue pour afficher les détails d'une candidature"""
    user_profile = request.user.profile
    if user_profile.user_type != 'entreprise':
        messages.error(request, _("Vous n'avez pas accès à cette page."))
        return redirect('stages:dashboard')
    
    candidature = get_object_or_404(
        Candidature.objects.select_related(
            'etudiant',
            'stage'
        ),
        pk=pk,
        stage__entreprise=user_profile.entreprise
    )
    
    context = {
        'candidature': candidature,
    }
    return render(request, 'stages/candidature_detail.html', context)

@login_required
def candidature_update_status(request, pk, nouveau_statut):
    """Vue pour mettre à jour le statut d'une candidature"""
    user_profile = request.user.profile
    if user_profile.user_type != 'entreprise':
        messages.error(request, _("Vous n'avez pas accès à cette action."))
        return redirect('stages:dashboard')
    
    candidature = get_object_or_404(
        Candidature,
        pk=pk,
        stage__entreprise=user_profile.entreprise
    )
    
    if nouveau_statut not in dict(Candidature.STATUT_CHOICES):
        messages.error(request, _("Statut invalide."))
        return redirect('stages:candidature_detail', pk=pk)
    
    old_status = candidature.statut
    candidature.statut = nouveau_statut
    candidature.save()

    # Créer une notification/message personnalisé selon le statut
    if nouveau_statut == 'acceptee':
        notif_message = _(f"Félicitations ! Votre candidature pour l'offre '{candidature.stage.titre}' a été acceptée. L'entreprise vous contactera prochainement.")
    elif nouveau_statut == 'refusee':
        notif_message = _(f"Nous sommes désolés, votre candidature pour l'offre '{candidature.stage.titre}' a été refusée. Nous vous souhaitons bonne chance pour la suite.")
    else:
        notif_message = _(f"Le statut de votre candidature pour l'offre '{candidature.stage.titre}' est en cours de traitement.")

    Notification.objects.create(
        destinataire=candidature.etudiant,
        titre=_("Mise à jour de votre candidature"),
        message=notif_message
    )

    messages.success(request, _("Le statut de la candidature a été mis à jour."))
    return redirect('stages:candidature_detail', pk=pk)

@login_required
def contact_etudiant(request, pk):
    """Vue pour contacter un étudiant"""
    user_profile = request.user.profile
    if user_profile.user_type != 'entreprise':
        messages.error(request, _("Vous n'avez pas accès à cette page."))
        return redirect('stages:dashboard')
    
    etudiant = get_object_or_404(Etudiant, pk=pk)
    
    if request.method == 'POST':
        sujet = request.POST.get('sujet')
        message = request.POST.get('message')
        
        if not sujet or not message:
            messages.error(request, _( "Veuillez remplir tous les champs." ))
        else:
            # Créer une notification pour l'étudiant
            destinataire = etudiant.user_profile.user if hasattr(etudiant, 'user_profile') and etudiant.user_profile else etudiant.user
            Notification.objects.create(
                destinataire=destinataire,
                titre=sujet,
                message=message,
                expediteur=request.user
            )
            # Envoi d'un email à l'étudiant
            send_mail(
                subject=sujet,
                message=message,
                from_email=request.user.email,
                recipient_list=[destinataire.email],
                fail_silently=True
            )
            messages.success(request, _( "Message envoyé avec succès (notification + email)." ))
            return redirect('stages:candidatures_list')
    
    context = {
        'etudiant': etudiant,
    }
    return render(request, 'stages/contact_etudiant.html', context)

@login_required
def entreprise_profile(request):
    """Vue pour gérer le profil de l'entreprise"""
    user_profile = request.user.profile
    if user_profile.user_type != 'entreprise' or not hasattr(user_profile, 'entreprise'):
        messages.error(request, _("Vous n'avez pas accès à cette page."))
        return redirect('stages:dashboard')

    entreprise_instance = user_profile.entreprise

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        entreprise_form = EntrepriseProfileForm(request.POST, request.FILES, instance=entreprise_instance)

        if user_form.is_valid() and profile_form.is_valid() and entreprise_form.is_valid():
            user_form.save()
            profile_form.save()
            entreprise_form.save()
            messages.success(request, _('Profil mis à jour avec succès.'))
            return redirect('stages:entreprise_profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
        entreprise_form = EntrepriseProfileForm(instance=entreprise_instance)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'entreprise_form': entreprise_form,
    }
    return render(request, 'stages/entreprise_profile.html', context)

@login_required
def messages_list(request):
    """Vue pour afficher la boîte de réception de l'utilisateur (étudiant ou entreprise)"""
    messages_recus = Message.objects.filter(destinataire=request.user).order_by('-date_envoi')
    messages_envoyes = Message.objects.filter(expediteur=request.user).order_by('-date_envoi')
    return render(request, 'stages/messages_list.html', {
        'messages_recus': messages_recus,
        'messages_envoyes': messages_envoyes,
    })

@login_required
def message_detail(request, pk):
    """Vue pour lire un message et y répondre"""
    message = get_object_or_404(Message, pk=pk)
    if message.destinataire != request.user and message.expediteur != request.user:
        return redirect('stages:messages_list')
    # Marquer comme lu si c'est le destinataire
    if message.destinataire == request.user and not message.lu:
        message.lu = True
        message.save()
    if request.method == 'POST':
        contenu = request.POST.get('contenu')
        if contenu:
            Message.objects.create(
                expediteur=request.user,
                destinataire=message.expediteur,
                sujet='RE: ' + message.sujet,
                contenu=contenu
            )
            # Créer une notification pour l'expéditeur initial
            Notification.objects.create(
                destinataire=message.expediteur,
                titre='Nouveau message',
                message=f"Vous avez reçu une réponse à votre message : {message.sujet}"
            )
            return redirect('stages:messages_list')
    return render(request, 'stages/message_detail.html', {'message': message})
