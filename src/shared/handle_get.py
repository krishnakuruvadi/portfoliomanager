from users.models import User

def get_all_users_names_as_list():
    users_list = list()
    users = User.objects.all()
    for user in users:
        users_list.append(user.name)
    return users_list