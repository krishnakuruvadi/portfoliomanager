from django.shortcuts import render
from decimal import Decimal
import math

def calculator(request):
    template = 'calculator/calculator.html'
    context = {}
    fd_prin = 0
    fd_time = 0
    fd_roi = 0
    fd_final_val = 0
    fd_compound = 'fd_compound_yr'
    if request.method == 'POST':
        print(request.POST)
        if "calculatefdprin" in request.POST:
            fd_time = float(request.POST['fd_time'])
            fd_roi = float(request.POST['fd_int'])
            fd_compound = request.POST['fdcompounding']
            fd_final_val = float(request.POST['fd_final_val'])
            fd_prin = round(float(fd_calc_prin_val(fd_final_val, fd_time, fd_roi, fd_compound)),2)

        if "calculatefdtime" in request.POST:
            fd_prin = float(request.POST['fd_prin'])
            fd_roi = float(request.POST['fd_int'])
            fd_compound = request.POST['fdcompounding']
            fd_final_val = float(request.POST['fd_final_val'])
            fd_time = fd_calc_time(fd_prin, fd_final_val, fd_roi, fd_compound)

        if "calculatefdint" in request.POST:
            fd_prin = float(request.POST['fd_prin'])
            fd_time = float(request.POST['fd_time'])
            fd_compound = request.POST['fdcompounding']
            fd_final_val = float(request.POST['fd_final_val'])
            fd_roi = round(float(fd_calc_roi(fd_prin, fd_time, fd_final_val, fd_compound)),2)

        if "calculatefdfinalval" in request.POST:
            fd_prin = float(request.POST['fd_prin'])
            fd_time = float(request.POST['fd_time'])
            fd_roi = float(request.POST['fd_int'])
            fd_compound = request.POST['fdcompounding']
            fd_final_val = round(float(fd_calc_final_val(fd_prin, fd_time, fd_roi, fd_compound)),2)
        
    context = {'fd_prin':fd_prin, 'fd_time':fd_time, 'fd_int':fd_roi, 'fd_final_val':fd_final_val, 'fd_compound':fd_compound}
    print('context', context)
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