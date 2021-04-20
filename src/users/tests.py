from django.test import TestCase
from .models import User
import datetime
# Create your tests here.

def add_default_user():
    return User.objects.create(
        name='Ramakrishna',
        email='ramakrishna@test.com',
        dob=datetime.date(year=1990,month=12,day=10)
    )
