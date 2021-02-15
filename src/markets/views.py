from django.shortcuts import render
from .models import PEMonthy, PBMonthy
from common.models import Preferences
from shared.utils import get_float_or_zero_from_string, convert_date_to_string

# Create your views here.

def markets_home(request):
    pass

def pe_view(request):
    template = 'markets/pe_view.html'
    if request.method == 'POST':
        display_type = request.POST['pe_type']
    else:
        display_type = 'pe_avg'
    pref_obj = Preferences.get_solo()
    sel_indexes = list()
    if pref_obj.indexes_to_scroll:
            for index in pref_obj.indexes_to_scroll.split('|'):
                sel_indexes.append(index)
    pe_vals = dict()
    pb_vals = dict()
    for index in sel_indexes:
        vals = PEMonthy.objects.filter(index_name=index).order_by('year', 'month')
        if vals and len(vals) > 0:
            if not index in pe_vals:
                pe_vals[index] = list()
            for val in vals:
                #if not val.year in pe_vals[index]:
                #    pe_vals[index][val.year] = [0] * 12
                dt = str(val.year)+ '/' + str(val.month)
                if display_type == 'pe_min':
                    pe_vals[index].append({'x':dt, 'y':get_float_or_zero_from_string(val.pe_min)})
                elif display_type == 'pe_max':
                    pe_vals[index].append({'x':dt, 'y':get_float_or_zero_from_string(val.pe_max)})
                else:
                    pe_vals[index].append({'x':dt, 'y':get_float_or_zero_from_string(val.pe_avg)})
        
        vals = PBMonthy.objects.filter(index_name=index).order_by('year', 'month')
        if vals and len(vals) > 0:
            if not index in pb_vals:
                pb_vals[index] = list()
            for val in vals:
                #if not val.year in pb_vals[index]:
                #    pb_vals[index][val.year] = [0] * 12
                dt = str(val.year)+ '/' + str(val.month)
                if display_type == 'pb_min':
                    pb_vals[index].append({'x':dt, 'y':get_float_or_zero_from_string(val.pb_min)})
                elif display_type == 'pb_max':
                    pb_vals[index].append({'x':dt, 'y':get_float_or_zero_from_string(val.pb_max)})
                else:
                    pb_vals[index].append({'x':dt, 'y':get_float_or_zero_from_string(val.pb_avg)})
        
    context = {}
    if len(pe_vals.keys()) > 0:
        context['pe_vals'] = pe_vals
    if len(pb_vals.keys()) > 0:
        context['pb_vals'] = pb_vals
    print(context)
    return render(request, template, context)