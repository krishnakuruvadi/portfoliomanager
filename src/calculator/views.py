from django.shortcuts import render
from decimal import Decimal
import math
from shared.utils import get_float_or_zero_from_string

def calculator(request):
    template = 'calculator/calculator.html'
    context = {}
    fd_prin = 0
    fd_time = 0
    fd_roi = 0
    fd_final_val = 0
    fd_compound = 'fd_compound_yr'
    rd_prin = 0
    rd_time = 0
    rd_roi = 0
    rd_final_val = 0
    rd_compound = 'rd_compound_yr'
    if request.method == 'POST':
        fd_prin = get_float_or_zero_from_string(request.POST['fd_prin'])
        fd_time = get_float_or_zero_from_string(request.POST['fd_time'])
        fd_roi = get_float_or_zero_from_string(request.POST['fd_int'])
        fd_final_val = get_float_or_zero_from_string(request.POST['fd_final_val'])
        fd_compound = request.POST.get('fdcompounding', 'fd_compound_yr')
        rd_prin = get_float_or_zero_from_string(request.POST['rd_prin'])
        rd_time = get_float_or_zero_from_string(request.POST['rd_time'])
        rd_roi = get_float_or_zero_from_string(request.POST['rd_int'])
        rd_final_val = get_float_or_zero_from_string(request.POST['rd_final_val'])
        rd_compound = request.POST.get('rdcompounding','rd_compound_yr')
        print(request.POST)
        if "calculatefdprin" in request.POST:
            fd_prin = round(float(fd_calc_prin_val(fd_final_val, fd_time, fd_roi, fd_compound)),2)

        if "calculatefdtime" in request.POST:
            fd_time = fd_calc_time(fd_prin, fd_final_val, fd_roi, fd_compound)

        if "calculatefdint" in request.POST:
            fd_roi = round(float(fd_calc_roi(fd_prin, fd_time, fd_final_val, fd_compound)),2)

        if "calculatefdfinalval" in request.POST:
            fd_final_val = round(float(fd_calc_final_val(fd_prin, fd_time, fd_roi, fd_compound)),2)
        
        if "calculaterdfinalval" in request.POST:
            rd_final_val = round(float(rd_calc_final_val(rd_prin, rd_time, rd_roi, rd_compound)),2)

    context = {'fd_prin':fd_prin, 'fd_time':fd_time,
                 'fd_int':fd_roi, 'fd_final_val':fd_final_val, 'rd_final_val':rd_final_val,
                 'fd_compound':fd_compound, 'rd_prin':rd_prin, 'rd_time':rd_time, 'rd_int':rd_roi,
                'rd_compound':rd_compound, 'curr_module_id': 'id_calculator_module'}
    print('context', context)
    #if request.is_ajax():
    #    print('request is ajax')
    #    return HttpResponseRedirect('/calculator/',context)
    #else:
    #    print('request is not ajax')
    return render(request, template, context=context)

def fd_calc_final_val(fd_prin, fd_time, fd_roi, fd_compound):
    n = 1
    if fd_compound == 'fd_compound_qtr':
        n = 4
    if fd_compound == 'fd_compound_half':
        n = 2
    fd_time = float(fd_time)
    fd_roi = float(fd_roi)
    val = fd_prin * (((1 + (fd_roi/(100.0 * n))) ** (n*(fd_time/12))))
    return val

def fd_calc_prin_val(fd_final, fd_time, fd_roi, fd_compound):
    n = 1
    if fd_compound == 'fd_compound_qtr':
        n = 4
    if fd_compound == 'fd_compound_half':
        n = 2
    fd_time = float(fd_time)
    fd_roi = float(fd_roi)

    val = fd_final / (((1 + (fd_roi/(100.0 * n))) ** (n*(fd_time/12))))
    return val

def fd_calc_time(fd_prin, fd_final, fd_roi, fd_compound):
    n = 1
    if fd_compound == 'fd_compound_qtr':
        n = 4
    if fd_compound == 'fd_compound_half':
        n = 2
    #val = fd_prin * (((1 + (fd_roi/(100.0 * n))) ** (n*(fd_time/12))))
    val = (math.log10((fd_final/fd_prin)))/(n*(math.log10(1+fd_roi/(100*n))))
    val = math.ceil(val*12)
    if val < 1:
        val = 1
    return val

def fd_calc_roi(fd_prin, fd_time, fd_final, fd_compound):
    n = 1
    if fd_compound == 'fd_compound_qtr':
        n = 4
    if fd_compound == 'fd_compound_half':
        n = 2
    fd_time = float(fd_time)
    #val = fd_prin * (((1 + (fd_roi/(100.0 * n))) ** (n*(fd_time/12))))
    val = n*(((fd_final/fd_prin)**(1/(n*fd_time/12)))-1)
    val = val*100
    return val

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
    #val = rd_prin*((((1+rd_roi/(n*100))**(n*rd_time/12))-1)/(rd_roi/(100*n)))
    #val = fd_prin * (((1 + (fd_roi/(100.0 * n))) ** (n*(fd_time/12))))
    
    # What is the future value after 10 years of saving $200 now, 
    # with an additional monthly savings of $200. Assume the interest rate is 6% (annually)
    # compounded monthly?
    #>>> import numpy as np
    #>>> np.fv(0.06/12, 10*12, -200, -200)
    #print("prin",rd_prin)
    #print("roi",rd_roi)
    #print("months",rd_time)
    #print("n",n)
    #val = npf.fv(rd_roi*n/(100*12),(rd_time)/n, -1*rd_prin*n, 0, when="end")
    #return val
    
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
