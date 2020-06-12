from ppf.models import Ppf, PpfEntry
from ssy.models import Ssy, SsyEntry
from fixed_deposit.models import FixedDeposit
from espp.models import Espp
from epf.models import Epf, EpfEntry
from goal.models import Goal
from users.models import User

def get_ppf_amount_for_goal(id):
    ppf_objs = Ppf.objects.filter(goal=id)
    total_ppf = 0
    for ppf_obj in ppf_objs:
        ppf_num = ppf_obj.number
        amt = 0
        ppf_trans = PpfEntry.objects.filter(number=ppf_num)
        for entry in ppf_trans:
            if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                amt += entry.amount
            else:
                amt -= entry.amount
        if amt < 0:
            amt = 0
        total_ppf += amt
    return total_ppf

def get_ssy_amount_for_goal(id):
    ssy_objs = Ssy.objects.filter(goal=id)
    total_ssy = 0
    for ssy_obj in ssy_objs:
        ssy_num = ssy_obj.number
        amt = 0
        ssy_trans = SsyEntry.objects.filter(number=ssy_num)
        for entry in ssy_trans:
            if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                amt += entry.amount
            else:
                amt -= entry.amount
        if amt < 0:
            amt = 0
        total_ssy += amt
    return total_ssy

def get_fd_amount_for_goal(id):
    fd_objs = FixedDeposit.objects.filter(goal=id)
    total_fd = 0
    for fd_obj in fd_objs:
        total_fd += fd_obj.final_val
    return total_fd

def get_espp_amount_for_goal(id):
    espp_objs = Espp.objects.filter(goal=id)
    total_espp = 0
    for espp_obj in espp_objs:
        if not espp_obj.total_sell_price:
            total_espp += espp_obj.latest_value
    return total_espp

def get_epf_amount_for_goal(id):
    epf_objs = Epf.objects.filter(goal=id)
    total_epf = 0
    for epf_obj in epf_objs:
        epf_id = epf_obj.id
        amt = 0
        epf_trans = EpfEntry.objects.filter(epf_id=epf_id)
        for entry in epf_trans:
            if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                amt += entry.employee_contribution + entry.employer_contribution + entry.interest_contribution
            else:
                amt -= entry.employee_contribution + entry.employer_contribution + entry.interest_contribution
        if amt < 0:
            amt = 0
        total_epf += amt
    return total_epf

def get_goal_contributions(goal_id):
    print("inside get_goal_contributions")
    contrib = dict()
    contrib['epf'] = int(get_epf_amount_for_goal(goal_id))
    contrib['espp'] = int(get_espp_amount_for_goal(goal_id))
    contrib['fd'] = int(get_fd_amount_for_goal(goal_id))
    contrib['ppf'] =int( get_ppf_amount_for_goal(goal_id))
    contrib['ssy'] =int( get_ssy_amount_for_goal(goal_id))
    contrib['equity'] = contrib['espp']
    contrib['debt'] = contrib['epf'] + contrib['fd'] + contrib['ppf'] + contrib['ssy']
    contrib['total'] = contrib['equity'] + contrib['debt']
    contrib['distrib_labels'] = ['EPF','ESPP','FD','PPF','SSY']
    contrib['distrib_vals'] = [contrib['epf'],contrib['espp'],contrib['fd'],contrib['ppf'],contrib['ssy']]
    contrib['distrib_colors'] = ['#f15664', '#f9c5c6','#006f75','#92993c']
    print("contrib:", contrib)
    return contrib

def get_ppf_amount_for_user(name):
    ppf_objs = Ppf.objects.filter(user=name)
    total_ppf = 0
    for ppf_obj in ppf_objs:
        ppf_num = ppf_obj.number
        amt = 0
        ppf_trans = PpfEntry.objects.filter(number=ppf_num)
        for entry in ppf_trans:
            if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                amt += entry.amount
            else:
                amt -= entry.amount
        if amt < 0:
            amt = 0
        total_ppf += amt
    return total_ppf

def get_ssy_amount_for_user(name):
    ssy_objs = Ssy.objects.filter(user=name)
    total_ssy = 0
    for ssy_obj in ssy_objs:
        ssy_num = ssy_obj.number
        amt = 0
        ssy_trans = SsyEntry.objects.filter(number=ssy_num)
        for entry in ssy_trans:
            if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                amt += entry.amount
            else:
                amt -= entry.amount
        if amt < 0:
            amt = 0
        total_ssy += amt
    return total_ssy

def get_fd_amount_for_user(name):
    fd_objs = FixedDeposit.objects.filter(user=name)
    total_fd = 0
    for fd_obj in fd_objs:
        total_fd += fd_obj.final_val
    return total_fd

def get_espp_amount_for_user(name):
    espp_objs = Espp.objects.filter(user=name)
    total_espp = 0
    for espp_obj in espp_objs:
        if not espp_obj.total_sell_price:
            total_espp += espp_obj.latest_value
    return total_espp

def get_epf_amount_for_user(name):
    epf_objs = Epf.objects.filter(user=name)
    total_epf = 0
    for epf_obj in epf_objs:
        epf_id = epf_obj.id
        amt = 0
        epf_trans = EpfEntry.objects.filter(epf_id=epf_id)
        for entry in epf_trans:
            if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                amt += entry.employee_contribution + entry.employer_contribution + entry.interest_contribution
            else:
                amt -= entry.employee_contribution + entry.employer_contribution + entry.interest_contribution
        if amt < 0:
            amt = 0
        total_epf += amt
    return total_epf

def get_goal_target_for_user(user_name):
    goal_objs = Goal.objects.filter(user=user_name)
    target_amt = 0
    for goal_obj in goal_objs:
        target_amt += goal_obj.final_val
    return target_amt

def get_user_contributions(user_id):
    print("inside get_user_contributions")
    try:
        user_obj = User.objects.get(id=user_id)
        user_name = user_obj.name
        contrib = dict()
        contrib['target'] = get_goal_target_for_user(user_name)
        contrib['epf'] = int(get_epf_amount_for_user(user_name))
        contrib['espp'] = int(get_espp_amount_for_user(user_name))
        contrib['fd'] = int(get_fd_amount_for_user(user_name))
        contrib['ppf'] =int( get_ppf_amount_for_user(user_name))
        contrib['ssy'] =int( get_ssy_amount_for_user(user_name))
        contrib['equity'] = contrib['espp']
        contrib['debt'] = contrib['epf'] + contrib['fd'] + contrib['ppf'] + contrib['ssy']
        contrib['total'] = contrib['equity'] + contrib['debt']
        contrib['distrib_labels'] = ['EPF','ESPP','FD','PPF']
        contrib['distrib_vals'] = [contrib['epf'],contrib['espp'],contrib['fd'],contrib['ppf'],contrib['ssy']]
        contrib['distrib_colors'] = ['#f15664', '#f9c5c6','#006f75','#92993c']
        print("contrib:", contrib)
        return contrib
    except User.DoesNotExist:
        print("User with id ", user_id, " does not exist" )
        pass
