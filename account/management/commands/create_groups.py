from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Creates user groups'

    def handle(self, *args, **options):
        groups = ['AdminMagasin', 'Accueillants', 'Caissiers', 'Livraisons']
        
        for group in groups:
            Group.objects.get_or_create(name=group)
        
        self.stdout.write(self.style.SUCCESS('Successfully created user groups'))
