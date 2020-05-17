from .models import Goal

def one_time_pay_final_val(curr_val, inflation, time_period):
    #final_val = curr_val*(pow(1+inflation/100, time_period/12)-1)
    final_val = int(curr_val*(1+inflation/100)**(time_period/12))
    print('curr_val:',curr_val, ' inflation:', inflation, ' timeperiod:', time_period, ' final value:', final_val)

    return final_val

def recur_revenue_final_val(curr_val, inflation, accum_period, expense_period, post_returns):
    inflated_exp = curr_val*(pow(1+inflation/100, accum_period))
    if inflation == post_returns:
        post_returns = post_returns - 0.0000001
    real_ret =(((1+post_returns/100)/(1+inflation/100))-1)*100
    corpus = inflated_exp*((1-pow((1+real_ret/100), -1*expense_period))/(real_ret/100))
    print("corpus:",corpus)
    return corpus

def add_goal_entry(name, start_date, curr_val, time_period, inflation,
            final_val, user, recurring_pay_goal, expense_period,
            post_returns, notes):
    Goal.objects.create(name=name, start_date=start_date, curr_val=curr_val,
        time_period=time_period, inflation=inflation, final_val=final_val,
        user=user, recurring_pay_goal=recurring_pay_goal, expense_period=expense_period,
        post_returns=post_returns, notes=notes)