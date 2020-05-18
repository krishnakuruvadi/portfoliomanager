from .models import Goal
from dateutil.relativedelta import relativedelta
from datetime import datetime


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
