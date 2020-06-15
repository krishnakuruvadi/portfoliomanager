from epf.models import Epf, EpfEntry
from espp.models import Espp
from fixed_deposit.models import FixedDeposit
from ppf.models import Ppf, PpfEntry
from ssy.models import Ssy, SsyEntry
from users.models import User
from goal.models import Goal
import calendar
import datetime

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

def get_user_id_from_name(name):
    try:
        user_obj = User.objects.get(name=name)
        return user_obj.id
    except Exception as e:
        return None

def get_day_range_of_month(year, month):
    last_day_of_month = calendar.monthrange(2019,8)[1]
    first_day = datetime.datetime(year, month, 1)
    last_day = datetime.datetime(year, month, last_day_of_month)
    return first_day, last_day

def get_start_day_across_portfolio():
    start_day = datetime.date.today()
    epf_objs = Epf.objects.all()
    for epf_obj in epf_objs:    
        start_day = start_day if start_day < epf_obj.start_date else epf_obj.start_date
    espp_objs = Espp.objects.all()
    for espp_obj in espp_objs:
        start_day = start_day if start_day < espp_obj.purchase_date else espp_obj.purchase_date
    fd_objs = FixedDeposit.objects.all()
    for fd_obj in fd_objs:
        start_day = start_day if start_day < fd_obj.start_date else fd_obj.start_date
        
    ppf_objs = Ppf.objects.all()
    for ppf_obj in ppf_objs:
        start_day = start_day if start_day < ppf_obj.start_date else ppf_obj.start_date
    
    ssy_objs = Ssy.objects.all()
    for ssy_obj in ssy_objs:
        start_day = start_day if start_day < ssy_obj.start_date else ssy_obj.start_date
    
    new_start_day = datetime.date(start_day.year, start_day.month, 1)
    return new_start_day
    