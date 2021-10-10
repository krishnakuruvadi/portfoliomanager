from shared.handle_chart_data import get_user_contributions
from .models import User
import datetime

def update_user_networth(user_id):
    if user_id:
        try:
            u = User.objects.get(id=user_id)
            c = get_user_contributions(u.id)
            u.total_networth = c['total']
            u.as_on = datetime.datetime.now()
            u.save()
        except User.DoesNotExist:
            print(f'no user with id {user_id}')
    else:
        for u in User.objects.all():
            c = get_user_contributions(u.id)
            u.total_networth = c['total']
            u.as_on = datetime.datetime.now()
            u.save()