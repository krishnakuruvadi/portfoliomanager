from users.models import User
from goal.models import Goal

def get_all_users_names_as_list():
    users_list = list()
    users = User.objects.all()
    for user in users:
        users_list.append(user.name)
    return users_list

def get_all_goals_for_user_as_list(user):
    goal_list = list()
    goals = Goal.objects.filter(user=user)
    for goal in goals:
        goal_list.append(goal.name)
    return goal_list

def get_goal_id_from_name(user, name):
    try:
        goal = Goal.objects.get(user=user, name=name)
        print("in get_goal_id_from_name returning", goal.id)
        return goal.id
    except Goal.DoesNotExist:
        print("goal with user ", user, " and name ", name, " does not exist")
        return None

def get_goal_name_from_id(goal_id):
    try:
        goal = Goal.objects.get(id=goal_id)
        print("in get_goal_id_from_name returning", goal.name)
        return goal.name
    except Goal.DoesNotExist:
        print("goal with id", goal_id, " does not exist")
        return None

def get_all_goals_id_to_name_mapping():
    goal_mapping = dict()
    goals = Goal.objects.all()
    for goal in goals:
        goal_mapping[goal.id] = goal.name
    return goal_mapping