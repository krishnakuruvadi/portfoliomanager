import factory
from faker import Faker

fake = Faker()
from users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    name = fake.name()
    email = "some@some.com"
    dob = fake.date()
    

