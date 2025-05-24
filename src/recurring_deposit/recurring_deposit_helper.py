from .models import RecurringDeposit
from dateutil.relativedelta import relativedelta
from datetime import datetime, date

def add_rd_entry(number, bank_name, start_date, principal, time_period_months,
                    final_val, user, notes, goal, roi, mat_date):
    RecurringDeposit.objects.create(number=number, 
                                bank_name=bank_name,
                                start_date=start_date,
                                principal=principal,
                                time_period=time_period_months,
                                final_val=final_val,
                                user=user,
                                notes=notes,
                                goal=goal,
                                roi=roi,
                                mat_date=mat_date)

def get_maturity_value(principal, start_date, roi, time_period_months, compound_frequency=4):
    '''
    start_date should either be a date object or of format "%Y-%m-%d"
    '''
    if not isinstance(start_date, date):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    maturity_date = start_date+relativedelta(months=time_period_months)
    #maturity_value = principal*(1+(roi/(100*compound_frequency))**(compound_frequency*float(time_period_days/365)))
    maturity_value = compound_interest_quarterly(principal, roi, float(time_period_months))

    '''
    p = float(input('Please enter principal amount:'))
    t = float(input('Please enter number of years:'))
    r = float(input('Please enter rate of interest:'))
    n = float(input('Please enter number of times the interest is compounded in a year:'))
    a = p*(1+(r/(100*n))**(n*t))
    '''
    print('Amount compounded to: ', maturity_value)
    return maturity_date.strftime("%Y-%m-%d"), int(maturity_value)

def compound_interest_quarterly(principal, roi, time, rd_compound='rd_compound_qtr'):
    n = 1
    every = 12
    if rd_compound == 'rd_compound_qtr':
        n = 4
        every = 3
    if rd_compound == 'rd_compound_half':
        n = 2
        every = 6
    rd_time = float(time)
    rd_roi = float(roi)
    
    val = 0
    p = 0
    i = 0
    for t in range(int(rd_time)):
        p = p + principal
        i = i + p*rd_roi/(100*12)
        if t != 0 and t % every == 0:
            p = p + i
            i = 0
    val = p + i
    
    return val


def get_maturity_value_on_date(principal, start_date, roi, maturity_date, compound_frequency=4):
    '''
    start_date should either be a date object or of format "%Y-%m-%d"
    '''
    if not isinstance(start_date, date):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if not isinstance(maturity_date, date):
        maturity_date = datetime.strptime(maturity_date, "%Y-%m-%d").date()
    time_period_months = (maturity_date-start_date).months
    #maturity_value = principal*(1+(roi/(100*compound_frequency))**(compound_frequency*float(time_period_days/365)))
    maturity_value = compound_interest_quarterly(principal, roi, float(time_period_months))

    '''
    p = float(input('Please enter principal amount:'))
    t = float(input('Please enter number of years:'))
    r = float(input('Please enter rate of interest:'))
    n = float(input('Please enter number of times the interest is compounded in a year:'))
    a = p*(1+(r/(100*n))**(n*t))
    '''
    print('Amount compounded to: ', maturity_value)
    return int(maturity_value)