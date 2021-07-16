import datetime
from scipy import optimize
from dateutil.relativedelta import relativedelta

def secant_method(tol, f, x0):
    """
    Solve for x where f(x)=0, given starting x0 and tolerance.
    
    Arguments
    ----------
    tol: tolerance as percentage of final result. If two subsequent x values are with tol percent, the function will return.
    f: a function of a single variable
    x0: a starting value of x to begin the solver

    Notes
    ------
    The secant method for finding the zero value of a function uses the following formula to find subsequent values of x. 
    
    x(n+1) = x(n) - f(x(n))*(x(n)-x(n-1))/(f(x(n))-f(x(n-1)))
    
    Warning 
    --------
    This implementation is simple and does not handle cases where there is no solution. Users requiring a more robust version should use scipy package optimize.newton.

    """

    x1 = x0*1.1
    while (abs(x1-x0)/abs(x1) > tol):
        x0, x1 = x1, x1-f(x1)*(x1-x0)/(f(x1)-f(x0))
    return x1

def xnpv(rate,cashflows):
    """
    Calculate the net present value of a series of cashflows at irregular intervals.

    Arguments
    ---------
    * rate: the discount rate to be applied to the cash flows
    * cashflows: a list object in which each element is a tuple of the form (date, amount), where date is a python datetime.date object and amount is an integer or floating point number. Cash outflows (investments) are represented with negative amounts, and cash inflows (returns) are positive amounts.
    
    Returns
    -------
    * returns a single value which is the NPV of the given cash flows.

    Notes
    ---------------
    * The Net Present Value is the sum of each of cash flows discounted back to the date of the first cash flow. The discounted value of a given cash flow is A/(1+r)**(t-t0), where A is the amount, r is the discout rate, and (t-t0) is the time in years from the date of the first cash flow in the series (t0) to the date of the cash flow being added to the sum (t).  
    * This function is equivalent to the Microsoft Excel function of the same name. 

    """

    chron_order = sorted(cashflows, key = lambda x: x[0])
    t0 = chron_order[0][0] #t0 is the date of the first cash flow

    return sum([cf/(1+rate)**((t-t0).days/365.0) for (t,cf) in chron_order])

def xirr(cashflows,guess=0.1):
    """
    Calculate the Internal Rate of Return of a series of cashflows at irregular intervals.

    Arguments
    ---------
    * cashflows: a list object in which each element is a tuple of the form (date, amount), where date is a python datetime.date object and amount is an integer or floating point number. Cash outflows (investments) are represented with negative amounts, and cash inflows (returns) are positive amounts.
    * guess (optional, default = 0.1): a guess at the solution to be used as a starting point for the numerical solution. 

    Returns
    --------
    * Returns the IRR as a single value
    
    Notes
    ----------------
    * The Internal Rate of Return (IRR) is the discount rate at which the Net Present Value (NPV) of a series of cash flows is equal to zero. The NPV of the series of cash flows is determined using the xnpv function in this module. The discount rate at which NPV equals zero is found using the secant method of numerical solution. 
    * This function is equivalent to the Microsoft Excel function of the same name.
    * For users that do not have the scipy module installed, there is an alternate version (commented out) that uses the secant_method function defined in the module rather than the scipy.optimize module's numerical solver. Both use the same method of calculation so there should be no difference in performance, but the secant_method function does not fail gracefully in cases where there is no solution, so the scipy.optimize.newton version is preferred.

    """
    
    #return secant_method(0.0001,lambda r: xnpv(r,cashflows),guess)
    try:
        return optimize.newton(lambda r: xnpv(r,cashflows),guess)
    except Exception as ex:
        print(f'exception while getting cash flows {ex}')
        print(f'cash flows: {cashflows}')
        return 0

# Source: https://github.com/peliot/XIRR-and-XNPV/blob/master/financial.py

def get_required_xirr(initial_amt, yrly_investment, target_date, target_amt):
    yrly_investment = float(yrly_investment)
    target_amt = float(target_amt)
    initial_amt = float(initial_amt)
    cash_flows = list()
    cash_flows.append((datetime.date.today(), -1*initial_amt))
    for year in range(datetime.date.today().year, target_date.year):
        cash_flows.append((datetime.date(year=year, month=12, day=31), -1*yrly_investment))
    cash_flows.append((target_date, target_amt))
    return round(xirr(cash_flows)*100, 2)

'''
input:
  initial_amt: start at this amount
  xirr: rate at which amount will grow
  target_date: date by which we need to reach target
  target_amt: target amount to reach
returns:
  yearly investment required to reach target
'''
def get_required_yrly_investment(initial_amt, xirr, target_date, target_amt):
    target_amt = float(target_amt)
    rd = relativedelta(target_date, datetime.date.today())
    print(rd)
    period_months = rd.years*12+rd.months
    
    if period_months == 0:
        period_months = 1
    initial_amt_final_return = get_fd_final_val(initial_amt, 'fd_compound_yearly', period_months, xirr)
    remaining_amt = target_amt - initial_amt_final_return
    print(f'{remaining_amt} remaining of {target_amt}')
    yrly_investment = 0
    if remaining_amt > 0:
        yrly_investment = remaining_amt/2
        diff = remaining_amt/2
        i=0
        while (i<40):
            val = rd_calc_final_val(yrly_investment, period_months, xirr, 'rd_compound_yearly')
            print(f'{yrly_investment} invested monthly compounds to {val} after {period_months} months if compounded yearly at {xirr}')
            diff = float(val)/float(remaining_amt)
            if val > remaining_amt and  diff > 1.00000000000000005:
                yrly_investment = yrly_investment/(val/remaining_amt)
                diff = diff/2
            elif diff < 0.9:
                yrly_investment = yrly_investment *(val/remaining_amt)
                diff = diff/2
            else:
                return round(yrly_investment*12, 2)
            i = i+1
    return round(yrly_investment*12, 2)

'''
input:
  rd_prin: per month contrib
  rd_compound: 'rd_compound_qtr' or 'rd_compound_half' or 'rd_compound_yearly'. Default is 'rd_compound_yearly'
  rd_time: time period left in months
  rd_roi: rate of interest
returns:
  final amount of the initial investment
'''
def rd_calc_final_val(rd_prin, rd_time, rd_roi, rd_compound):
    n = 1
    every = 12
    if rd_compound == 'rd_compound_qtr':
        n = 4
        every = 3
    if rd_compound == 'rd_compound_half':
        n = 2
        every = 6
    rd_time = float(rd_time)
    rd_roi = float(rd_roi)
    
    val = 0
    p = 0
    i = 0
    for t in range(int(rd_time)):
        p = p + rd_prin
        i = i + p*rd_roi/(100*12)
        if t != 0 and t % every == 0:
            p = p + i
            i = 0
    val = p + i
    
    return val


'''
input:
  fd_prin: principal
  fd_compound: 'fd_compound_qtr' or 'fd_compound_half' or 'fd_compound_yearly'. Default is 'fd_compound_yearly'
  fd_time: time period left in months
  fd_roi: rate of interest
returns:
  final amount of the initial investment
'''
def get_fd_final_val(fd_prin, fd_compound, fd_time, fd_roi, print_logs=False):
    if fd_prin == 0:
        return 0
    if fd_time == 0:
        return fd_prin
    if fd_time < 0 :
        raise ValueError('fd_time cannot be less than 0')
    n = 1
    if fd_compound == 'fd_compound_qtr':
        n = 4
    if fd_compound == 'fd_compound_half':
        n = 2
    fd_time = float(fd_time)
    fd_roi = float(fd_roi)
    val = fd_prin * (((1 + (fd_roi/(100.0 * n))) ** (n*(fd_time/12))))
    if print_logs:
        print(f'{fd_prin} compounded {fd_compound} @ {fd_roi}% for {fd_time} months = {val}')
    return val

def get_fv_from_cashflows(cash_flows, roi, debug=False):
    total = 0
    #last_date = cash_flows[len(cash_flows)-1][0]
    next_sell_dt = None
    fvs = list()
    if debug:
        print(f'cash_flows[0] is {cash_flows[0]}')
    for i in range(len(cash_flows)):            
        if not next_sell_dt:
            for j in range (i, len(cash_flows)):
                if cash_flows[j][1] > 0:
                    next_sell_dt = cash_flows[j][0]
                    break
            if total > 0:
                d = relativedelta(next_sell_dt, cash_flows[i][0])
                months = d.months + d.years*12
                if debug:
                    print(f'Before: cash_flows[i][0] {cash_flows[i][0]} total {total} next_sell_dt {next_sell_dt}')
                total = get_fd_final_val(total, 'fd_compound_yearly', months, roi, True)
                if debug:
                    print(f'After: cash_flows[i][0] {cash_flows[i][0]} total {total} next_sell_dt {next_sell_dt}')
            else:
                if debug:
                    print(f'Else: cash_flows[i][0] {cash_flows[i][0]} total {total} next_sell_dt {next_sell_dt}')

        if cash_flows[i][1] > 0:
            if debug:
                print(f'Removing {cash_flows[i][1]} from {total} on {cash_flows[i][0]} = {total-cash_flows[i][1]}')
            total -= cash_flows[i][1]
            next_sell_dt = None
        else:
            if cash_flows[i][1] == 0:
                continue
            d = relativedelta(next_sell_dt, cash_flows[i][0])
            months = d.months + d.years*12
            total += get_fd_final_val(-1*cash_flows[i][1], 'fd_compound_yearly', months, roi, False)
            if debug:
                print(f'total {total} cf {cash_flows[i][1]} months {months} roi {roi}')
        fvs.append({'x':cash_flows[i][0].strftime('%Y-%m-%d'), 'y':int(total)})
    if debug:
        print(f'total for goal {total}')
    return total, fvs

'''
initial_amt = 0
xir = 6.5
target_date = datetime.date.today()+relativedelta(years=12, months=6)
target_amt = 302144
print(get_required_yrly_investment(initial_amt, xir, target_date, target_amt))
'''