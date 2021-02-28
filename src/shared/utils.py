import datetime
from dateutil.relativedelta import relativedelta

def get_float_or_zero_from_string(input):
    if input != None and input != '':
        try:
            res = float(input)
            return res
        except Exception as e:
            print('error converting ', input, ' to float')
    return 0

def get_float_or_none_from_string(input):
    if input != None and input != '':
        try:
            res = float(input)
            return res
        except Exception as e:
            print('error converting ', input, ' to float')
    return None

def get_int_or_none_from_string(input):
    if input != None and input != '':
        try:
            res = int(input)
            return res
        except Exception as e:
            print('error converting ', input, ' to int')
    return None

# default format expected of kind 2020-06-01
def get_datetime_or_none_from_string(input, format='%Y-%m-%d'):
    if input != None and input != '':
        try:
            res = datetime.datetime.strptime(input, format)
            return res
        except Exception as e:
            print('error converting ', input, ' to date')
    return None

# default format expected of kind 2020-06-01
def get_date_or_none_from_string(input, format='%Y-%m-%d'):
    if input != None and input != '':
        try:
            res = datetime.datetime.strptime(input, format).date()
            return res
        except Exception as e:
            print('error converting ', input, ' to date' + str(e))
    return None

def convert_date_to_string(input, format='%Y-%m-%d'):
    return input.strftime(format)

def get_diff(x,y):
    if x>y:
        return x-y
    return y-x
    
'''
today = datetime.date.today()
vals, dates = get_monthly_projected_vals_and_dates(today, 100, 12, 8)
print(vals)
print(dates)
output:
[100, 100.66666666666667, 101.33333333333333, 102.0, 102.66666666666667, 103.33333333333333, 104.0, 104.66666666666667, 105.33333333333333, 106.0, 106.66666666666667, 107.33333333333333, 108.0]
['2020-12-12', '2021-01-12', '2021-02-12', '2021-03-12', '2021-04-12', '2021-05-12', '2021-06-12', '2021-07-12', '2021-08-12', '2021-09-12', '2021-10-12', '2021-11-12', '2021-12-12']
'''
def get_monthly_projected_vals_and_dates(start_date, start_amount, period, inflation, format='%Y-%m-%d'):
    vals = list()
    dates = list()
    for i in range(period+1):
        if i == 0:
            vals.append(start_amount)
            dates.append(start_date.strftime(format))
        else:
            vals.append(start_amount+(start_amount*i*inflation/(100*12)))
            new_date = start_date+relativedelta(months=i)
            dates.append(new_date.strftime(format))
    return vals, dates

