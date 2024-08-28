from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=255, choices=[
        ('AdminMagasin', 'adminMagasin'),
        ('Accueillants', 'accueillants'),
        ('Caissiers', 'caissiers'),
        ('Livraisons', 'livraisons'),
    ])

#mot de passe oublié
class PWD_FORGET(models.Model):
    otp = models.IntegerField()
    status = models.CharField(max_length=1 ,default="0")
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    creat_at = models.DateTimeField(auto_now_add=True)