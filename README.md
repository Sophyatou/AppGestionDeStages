# Application de Gestion des Stages

Cette application Django permet de gérer les stages, les offres de stage, les candidatures et les relations entre étudiants, entreprises et responsables pédagogiques.

## Fonctionnalités principales

- Gestion des offres de stage
- Système de candidature
- Suivi des stages
- Statistiques et rapports
- Gestion des documents (CV, rapports)
- Système de notifications par email

## Installation

1. Cloner le dépôt :
```bash
git clone <votre-depot>
cd AppGestionDeStages
```

2. Créer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurer l'environnement :
- Copier le fichier `.env.example` vers `.env`
- Modifier les valeurs selon votre environnement

5. Initialiser la base de données :
```bash
python manage.py migrate
```

6. Créer un superutilisateur :
```bash
python manage.py createsuperuser
```

7. Lancer le serveur de développement :
```bash
python manage.py runserver
```

L'application sera accessible à l'adresse : http://127.0.0.1:8000/

## Structure des dossiers

- `stages/` : Application principale
  - `models.py` : Modèles de données
  - `views.py` : Vues et logique métier
  - `forms.py` : Formulaires
  - `urls.py` : Configuration des URLs
  - `templates/` : Templates HTML
  - `static/` : Fichiers statiques
  - `utils/` : Utilitaires (PDF, etc.)

## Utilisation

1. Connexion admin : http://127.0.0.1:8000/admin/
   - Utilisez les identifiants du superutilisateur créé

2. Types d'utilisateurs :
   - Étudiants : Peuvent postuler aux offres et déposer des rapports aux responsables
   - Entreprises : Peuvent publier des offres et gérer les candidatures
   - Responsables : Peuvent superviser les stages et  gérer les stages

## Fonctionnalités détaillées

### Système de fichiers
- Gestion sécurisée des uploads
- Validation des types MIME
- Redimensionnement automatique des images

### Recherche
- Recherche multi-critères des offres
- Filtres par niveau, lieu, durée, rémunération
- Suggestions personnalisées

### Statistiques
- Tableaux de bord personnalisés
- Statistiques par utilisateur
- Rapports PDF

## Maintenance

Pour nettoyer les fichiers temporaires et mettre à jour les statistiques :
```bash
python manage.py maintenance
```

## Sécurité

- Validation des fichiers uploadés
- Protection contre les injections SQL
- Validation des formulaires
- Gestion des permissions 