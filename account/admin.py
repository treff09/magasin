from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Profile
from stock.models import*

# Définir un inline admin descriptor pour le modèle Profile
# qui agit un peu comme un singleton
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False

# Définir une nouvelle classe d'admin User
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

# Réenregistrer le UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Profile)
admin.site.register(Ticket)
admin.site.register(Panier)
admin.site.register(Commande)

