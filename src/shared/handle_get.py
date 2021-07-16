import calendar
import datetime
import os
import pathlib
from epf.epf_interface import EpfInterface
from espp.espp_interface import EsppInterface
from fixed_deposit.fd_interface import FdInterface
from ppf.ppf_interface import PpfInterface
from ssy.ssy_interface import SsyInterface
from shares.share_interface import ShareInterface
from mutualfunds.mf_interface import MfInterface
from retirement_401k.r401k_interface import R401KInterface
from rsu.rsu_interface import RsuInterface
from users.models import User
from goal.models import Goal
from shared.utils import get_min

def get_all_users_names_as_list():
    users_list = list()
    users = User.objects.all()
    for user in users:
        users_list.append(user.name)
    return users_list

def get_all_goals_for_user_as_list(user_id):
    goal_list = list()
    goals = Goal.objects.filter(user=user_id)
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

def get_all_users(short_name_prefer=True):
    ret_user = dict()
    users = User.objects.all()
    for user in users:
        if short_name_prefer and user.short_name:
            ret_user[user.id] = user.short_name
        else:
            ret_user[user.id] = user.name
    return ret_user

def get_user_id_from_name(name):
    try:
        user_obj = User.objects.get(name=name)
        return user_obj.id
    except Exception as e:
        return None

def get_user_name_from_id(id):
    try:
        user_obj = User.objects.get(id=id)
        return user_obj.name
    except Exception as e:
        return None

def get_user_short_name_or_name_from_id(id):
    try:
        user_obj = User.objects.get(id=id)
        if user_obj.short_name and user_obj.short_name != '':
            return user_obj.short_name
        return user_obj.name
    except Exception as e:
        return None

def get_day_range_of_month(year, month):
    last_day_of_month = calendar.monthrange(2019,8)[1]
    first_day = datetime.datetime(year, month, 1)
    last_day = datetime.datetime(year, month, last_day_of_month)
    return first_day, last_day


def get_start_day_across_portfolio(user_id=None):
    #TODO: Fill for other investment avenues
    start_day = datetime.date.today()
    start_day = get_min(EpfInterface.get_start_day(user_id), start_day)
    start_day = get_min(EsppInterface.get_start_day(user_id), start_day)
    start_day = get_min(FdInterface.get_start_day(user_id), start_day)
    start_day = get_min(MfInterface.get_start_day(user_id), start_day)
    start_day = get_min(PpfInterface.get_start_day(user_id), start_day)
    start_day = get_min(SsyInterface.get_start_day(user_id), start_day)
    start_day = get_min(ShareInterface.get_start_day(user_id), start_day)
    start_day = get_min(R401KInterface.get_start_day(user_id), start_day)
    start_day = get_min(RsuInterface.get_start_day(user_id), start_day)

    new_start_day = datetime.date(start_day.year, start_day.month, 1)
    return new_start_day


def get_path_to_chrome_driver():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    for file in os.listdir(path):
        if "chromedriver" in file.lower():
            path = os.path.join(path, file)
            break
    print('path to chrome driver ', path)
    return path

def get_files_in_dir(dir):
    file_list = list()
    for file in os.listdir(dir):
        path = os.path.join(dir, file)
        file_list.append(path)

    return file_list

def get_new_files_added(dir, existing_list):
    new_file_list = list()
    for file in os.listdir(dir):
        path = os.path.join(dir, file)
        if path not in existing_list:
            new_file_list.append(path)
    return new_file_list