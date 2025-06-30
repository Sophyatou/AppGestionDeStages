from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import Stage, Candidature, UserProfile, Etudiant, Responsable, Entreprise, FicheStage, Document

class StageForm(forms.ModelForm):
    class Meta:
        model = Stage
        fields = [
            'titre', 'entreprise', 'type_stage', 'duree',
            'description', 'competences_requises', 'remuneration',
            'date_debut', 'date_fin', 'nombre_places'
        ]
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'competences_requises': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        if date_debut and date_fin and date_debut > date_fin:
            raise forms.ValidationError(
                _("La date de début doit être antérieure à la date de fin.")
            )

        return cleaned_data

class CandidatureForm(forms.ModelForm):
    class Meta:
        model = Candidature
        fields = ['cv', 'lettre_motivation', 'commentaire']
        widgets = {
            'commentaire': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_cv(self):
        cv = self.cleaned_data.get('cv')
        if cv:
            if cv.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError(_("Le fichier CV ne doit pas dépasser 5MB."))
            if not cv.name.lower().endswith(('.pdf', '.doc', '.docx')):
                raise forms.ValidationError(_("Le CV doit être au format PDF ou Word."))
        return cv

    def clean_lettre_motivation(self):
        lettre = self.cleaned_data.get('lettre_motivation')
        if lettre:
            if lettre.size > 2 * 1024 * 1024:  # 2MB
                raise forms.ValidationError(_("La lettre de motivation ne doit pas dépasser 2MB."))
            if not lettre.name.lower().endswith(('.pdf', '.doc', '.docx')):
                raise forms.ValidationError(_("La lettre de motivation doit être au format PDF ou Word."))
        return lettre

class UserProfileForm(forms.ModelForm):
    """Formulaire pour le profil utilisateur (communs)"""
    class Meta:
        model = UserProfile
        fields = ['telephone', 'photo']
        widgets = {
            'telephone': forms.TextInput(attrs={'placeholder': _('Ex: +33 6 12 34 56 78')}),
        }

class EtudiantSignUpForm(UserCreationForm):
    filiere = forms.CharField(max_length=100, label=_('Filière'))
    NIVEAUX = [
        ('L1', 'Licence 1'),
        ('L2', 'Licence 2'),
        ('L3', 'Licence 3'),
        ('M1', 'Master 1'),
        ('M2', 'Master 2'),
        ('DUT1', 'DUT 1'),
        ('DUT2', 'DUT 2'),
        ('BTS1', 'BTS 1'),
        ('BTS2', 'BTS 2'),
        ('Autre', 'Autre'),
    ]
    niveau_etude = forms.ChoiceField(choices=NIVEAUX, label=_("Niveau d'étude"))
    

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        help_texts = {f: '' for f in fields}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = ''

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile = UserProfile.objects.create(user=user, user_type='etudiant')
            Etudiant.objects.create(
                user_profile=profile,
                filiere=self.cleaned_data['filiere'],
                niveau=self.cleaned_data['niveau_etude'],
                cv=self.cleaned_data.get('cv')
            )
        return user

class ResponsableSignUpForm(UserCreationForm):
    departement = forms.CharField(max_length=100, label=_('Département'))
    telephone = forms.CharField(max_length=20, label=_('Téléphone'))

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        help_texts = {f: '' for f in fields}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = ''

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile = UserProfile.objects.create(user=user, user_type='responsable')
            Responsable.objects.create(
                profile=profile,
                departement=self.cleaned_data['departement'],
                telephone=self.cleaned_data['telephone']
            )
        return user

class EntrepriseSignUpForm(UserCreationForm):
    nom = forms.CharField(max_length=200, label=_('Nom de l\'entreprise'))
    secteur_activite = forms.CharField(max_length=100, label=_('Secteur d\'activité'))
    telephone = forms.CharField(max_length=20, label=_('Téléphone'))
    site_web = forms.URLField(required=False, label=_('Site web'))
    description = forms.CharField(widget=forms.Textarea, label=_('Description'))
    # username sera caché et auto-rempli
    username = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        help_texts = {f: '' for f in fields}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = ''
        self.fields['username'].required = False
        self.fields['username'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        # On force le username à être le nom de l'entreprise (slugifié si besoin)
        nom = cleaned_data.get('nom', '')
        if nom:
            username = nom.lower().replace(' ', '_')
            cleaned_data['username'] = username
            self.data = self.data.copy()
            self.data['username'] = username
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['username']
        if commit:
            user.save()
            profile = UserProfile.objects.create(user=user, user_type='entreprise')
            Entreprise.objects.create(
                profile=profile,
                nom=self.cleaned_data['nom'],
                secteur_activite=self.cleaned_data['secteur_activite'],
                telephone=self.cleaned_data['telephone'],
                site_web=self.cleaned_data.get('site_web'),
                description=self.cleaned_data['description']
            )
        return user

class FicheStageForm(forms.ModelForm):
    """Formulaire pour la fiche de stage"""
    class Meta:
        model = FicheStage
        exclude = ['etudiant', 'date_creation', 'date_modification']
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'type': 'date'}),
            'date_soutenance': forms.DateInput(attrs={'type': 'date'}),
            'mission': forms.Textarea(attrs={'rows': 4}),
            'commentaires': forms.Textarea(attrs={'rows': 3}),
        }

class DocumentForm(forms.ModelForm):
    """Formulaire pour les documents"""
    class Meta:
        model = Document
        exclude = ['etudiant', 'date_upload', 'valide']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class EtudiantProfileForm(forms.ModelForm):
    """Formulaire pour le profil étudiant (spécifiques)"""
    class Meta:
        model = Etudiant
        fields = ['filiere', 'niveau']

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class EntrepriseProfileForm(forms.ModelForm):
    """Formulaire pour le profil entreprise (spécifiques)"""
    class Meta:
        model = Entreprise
        fields = ['nom', 'secteur_activite', 'site_web', 'description', 'logo']