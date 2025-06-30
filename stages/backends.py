from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

class MultiFieldModelBackend(ModelBackend):
    """
    Permet de se connecter avec username, email ou téléphone.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None
        # Recherche par username ou email
        try:
            user = UserModel.objects.get(
                Q(username__iexact=username) |
                Q(email__iexact=username)
            )
        except UserModel.DoesNotExist:
            # Recherche par téléphone dans UserProfile
            try:
                from stages.models import UserProfile
                profile = UserProfile.objects.get(telephone__iexact=username)
                user = profile.user
            except UserProfile.DoesNotExist:
                return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None 