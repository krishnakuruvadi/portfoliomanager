from .models import Goal
from dateutil.relativedelta import relativedelta
from datetime import datetime
from shared.handle_chart_data import get_goal_contributions

def one_time_pay_final_val(curr_val, inflation, time_period):
    #final_val = curr_val*(pow(1+inflation/100, time_period/12)-1)
    final_val = int(curr_val*(1+inflation/100)**(time_period/12))
    print('curr_val:',curr_val, ' inflation:', inflation, ' timeperiod:', time_period, ' final value:', final_val)

    return final_val

def add_goal_entry(name, start_date, curr_val, time_period, inflation,
            final_val, user, recurring_pay_goal, expense_period,
            post_returns, notes):
    Goal.objects.create(name=name, start_date=start_date, curr_val=curr_val,
        time_period=time_period, inflation=inflation, final_val=final_val,
        user=user, recurring_pay_goal=recurring_pay_goal, expense_period=expense_period,
        post_returns=post_returns, notes=notes)


def get_inflated_val(curr_val, time_period, inflation):
  final_val = int(curr_val*(1+inflation/100)**(time_period))
  #print("Todays ", curr_exp, " is same as ", final_val, " after ", time_period, " months at an inflation of ", inflation, "\n")
  return final_val

def get_curr_val_from_fut_val(fut_val, time_period, inflation):
  inflation = inflation - 0.01 # to adjust for rounding errors
  curr_exp = int(fut_val/(1+inflation/100)**(time_period))
  #print(fut_val, " after ", time_period, " months at an inflation of ", inflation, " is same as todays", curr_exp, "\n")
  return curr_exp

def get_depletion_vals(corpus, curr_exp, accum_period_yrs, depletion_period_yrs, inflation, roi_during_depletion, start_date):
    save_now = corpus
    corpus_vals = list()
    expense_vals = list()
    dates = list()
    depl_date = datetime.strptime(start_date, "%Y-%m-%d").date()+relativedelta(years=accum_period_yrs)
    for i in range(depletion_period_yrs+1):
        fut_exp = get_inflated_val(curr_exp, (accum_period_yrs+i), inflation)
        print(i, "\t", save_now, "\t", fut_exp)
        
        dates.append(depl_date.strftime("%Y-%m-%d"))
        expense_vals.append(fut_exp)
        corpus_vals.append(save_now)

        depl_date = depl_date+relativedelta(years=+1)
        save_now= save_now-fut_exp
        save_now = get_inflated_val(save_now, 1, roi_during_depletion)
    return dates, corpus_vals, expense_vals


def get_corpus_to_be_saved(curr_yrly_exp, inflation, accum_period, depletion_period, roi_during_depletion):
    corpus = 0
    for i in range(accum_period, accum_period+depletion_period):
        fut_exp = get_inflated_val(curr_yrly_exp, i, inflation)

        if i == accum_period:
            cur_sav = fut_exp
        else:
            cur_sav = get_curr_val_from_fut_val(fut_exp, (i-accum_period), roi_during_depletion)
        corpus = corpus + cur_sav
    return corpus


def update_all_goals_contributions():
    for goal_obj in Goal.objects.all():
        update_goal_contributions(goal_obj.id)

def update_goal_contributions(id):
    try:
        goal_obj = Goal.objects.get(id=id)
        contrib = get_goal_contributions(id)

        goal_obj.debt_contrib = contrib['debt']
        goal_obj.equity_contrib = contrib['equity']
        goal_obj.achieved_amt = contrib['total']
        target = goal_obj.final_val
        if target < 1:
            target = 1
        remaining = target - contrib['total']
        if remaining < 0:
            remaining = 0
        goal_obj.pending_percent = int(remaining*100/target)
        goal_obj.achieved_percent = int(contrib['total']*100/target)
        goal_obj.pending_amt = remaining
        goal_obj.epf_conitrib = contrib['epf']
        goal_obj.espp_conitrib = contrib['espp']
        goal_obj.fd_conitrib = contrib['fd']
        goal_obj.ppf_conitrib = contrib['ppf']
        goal_obj.ssy_conitrib = contrib['ssy']
        goal_obj.rsu_conitrib = contrib['rsu']
        goal_obj.shares_conitrib = contrib['shares']
        goal_obj.mf_conitrib = contrib['mf']
        goal_obj.r_401k_contribution = contrib.get('401k', 0)
        goal_obj.save()
    except Exception as e:
        print(e)


def get_goal_id_name_mapping_for_user(id):
    data = dict()
    try:
        goal_list = dict()
        goal_objs = Goal.objects.filter(user=id)
        for goal_obj in goal_objs:
            goal_list[goal_obj.id] = goal_obj.name
        return goal_list
    except Exception as e:
        print(e)
    return data

def get_unallocated_amount():
    from ssy.ssy_interface import SsyInterface
    from ppf.ppf_interface import PpfInterface
    from epf.epf_interface import EpfInterface
    from espp.espp_interface import EsppInterface
    from fixed_deposit.fd_interface import FdInterface
    from mutualfunds.mf_interface import MfInterface
    from ppf.ppf_interface import PpfInterface
    from retirement_401k.r401k_interface import R401KInterface
    from shares.share_interface import ShareInterface
    from rsu.rsu_interface import RsuInterface

    amt = 0
    amt += SsyInterface.get_no_goal_amount()
    amt += PpfInterface.get_no_goal_amount()
    amt += EpfInterface.get_no_goal_amount()
    amt += EsppInterface.get_no_goal_amount()
    amt += FdInterface.get_no_goal_amount()
    amt += MfInterface.get_no_goal_amount()
    amt += PpfInterface.get_no_goal_amount()
    amt += R401KInterface.get_no_goal_amount()
    amt += ShareInterface.get_no_goal_amount()
    amt += RsuInterface.get_no_goal_amount()

    return round(amt, 2)
