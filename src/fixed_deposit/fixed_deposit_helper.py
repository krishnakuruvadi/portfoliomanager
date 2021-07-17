from .models import FixedDeposit
from dateutil.relativedelta import relativedelta
from datetime import datetime, date

def add_fd_entry(number, bank_name, start_date, principal, time_period_days,
                    final_val, user, notes, goal, roi, mat_date):
    FixedDeposit.objects.create(number=number, 
                                bank_name=bank_name,
                                start_date=start_date,
                                principal=principal,
                                time_period=time_period_days,
                                final_val=final_val,
                                user=user,
                                notes=notes,
                                goal=goal,
                                roi=roi,
                                mat_date=mat_date)

def get_maturity_value(principal, start_date, roi, time_period_days, compound_frequency=4):
    '''
    start_date should either be a date object or of format "%Y-%m-%d"
    '''
    if not isinstance(start_date, date):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    maturity_date = start_date+relativedelta(days=time_period_days)
    #maturity_value = principal*(1+(roi/(100*compound_frequency))**(compound_frequency*float(time_period_days/365)))
    maturity_value = compound_interest_quarterly(principal, roi, float(time_period_days/365))

    '''
    p = float(input('Please enter principal amount:'))
    t = float(input('Please enter number of years:'))
    r = float(input('Please enter rate of interest:'))
    n = float(input('Please enter number of times the interest is compounded in a year:'))
    a = p*(1+(r/(100*n))**(n*t))
    '''
    print('Amount compounded to: ', maturity_value)
    return maturity_date.strftime("%Y-%m-%d"), int(maturity_value)

def compound_interest_quarterly(principal, roi, time):
    result = principal * (pow((1 + roi / (100*4)), time*4))
    return result
