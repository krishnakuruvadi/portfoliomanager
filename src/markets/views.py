from django.shortcuts import render
from .models import PEMonthy, PBMonthy, News
from common.models import Preferences
from shared.utils import get_float_or_zero_from_string, convert_date_to_string
from newspaper import Article
import requests
# Create your views here.

def markets_home(request):
    template = 'markets/markets_home.html'
    context = {'curr_module_id':'id_markets_module'}
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                            'like Gecko) '
                            'Chrome/80.0.3987.149 Safari/537.36',
            'accept-language': 'en,gu;q=0.9,hi;q=0.8', 'accept-encoding': 'gzip, deflate, br'}
    r = requests.get(headers=headers,
        url='https://www.wsj.com/market-data/stocks/asia/indexes?id=%7B%22application%22%3A%22WSJ%22%2C%22instruments%22%3A%5B%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FGDOW%22%2C%22name%22%3A%22The%20Global%20Dow%20(World)%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FXX%2F%2FDGW2DOWA%22%2C%22name%22%3A%22DJ%20Global%20ex%20U.S.%20(World)%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FXX%2F%2FADOW%22%2C%22name%22%3A%22Asia%20Dow%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FAU%2F%2FXAO%22%2C%22name%22%3A%22Australia%3A%20All%20Ordinaries%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FAU%2F%2FXJO%22%2C%22name%22%3A%22Australia%3A%20S%26P%2FASX%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FCN%2F%2FHSCEI%22%2C%22name%22%3A%22China%3A%20H-Share%20Index%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FCN%2F%2FSHCOMP%22%2C%22name%22%3A%22China%3A%20Shanghai%20Composite%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FCN%2F%2F399106%22%2C%22name%22%3A%22China%3A%20Shenzhen%20Composite%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FHK%2F%2FHSI%22%2C%22name%22%3A%22Hong%20Kong%3A%20Hang%20Seng%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FIN%2F%2F1%22%2C%22name%22%3A%22India%3A%20S%26P%20BSE%20Sensex%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FIN%2F%2FNIFTY50%22%2C%22name%22%3A%22India%3A%20S%26P%20CNX%20Nifty%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FID%2F%2FJAKIDX%22%2C%22name%22%3A%22Indonesia%3A%20JSX%20Index%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FJP%2F%2FNIK%22%2C%22name%22%3A%22Japan%3A%20Nikkei%20225%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FMY%2F%2FFBMKLCI%22%2C%22name%22%3A%22Malaysia%3A%20FTSE%20Bursa%20Malaysia%20KLCI%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FNZ%2F%2FNZ50GR%22%2C%22name%22%3A%22New%20Zealand%3A%20S%26P%2FNZX%2050%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FPH%2F%2FPSEI%22%2C%22name%22%3A%22Philippines%3A%20PSEi%20Index%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FKR%2F%2FSEU%22%2C%22name%22%3A%22S.%20Korea%3A%20KOSPI%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FSG%2F%2FSTI%22%2C%22name%22%3A%22Singapore%3A%20Straits%20Times%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FXX%2F%2FY9999%22%2C%22name%22%3A%22Taiwan%3A%20TAIEX%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FTH%2F%2FSET%22%2C%22name%22%3A%22Thailand%3A%20SET%22%7D%5D%2C%22expanded%22%3Atrue%2C%22refreshInterval%22%3A60000%2C%22serverSideType%22%3A%22mdc_quotes%22%7D&type=mdc_quotes', timeout=15)
    context['instruments'] = list()
    if r.status_code==200:
        #print(r)
        #print(r.json())
        for k,v in r.json().items():
            print(k)
        json_data = r.json()
        for item in json_data['data']['instruments']:
            inst = dict()
            inst['country'] = item['country']
            inst['name'] = item['formattedName']
            inst['timestamp'] = item['timestamp']
            inst['oneYearHigh'] = item['oneYearHigh']
            inst['oneYearLow'] = item['oneYearLow']
            inst['1yearPercentChange'] = item['yearAgoPercentChange']
            inst['ytdPercentageChange'] = item['yearToDatePercentChange']
            inst['1dPriceChange'] = item['priceChange']
            inst['1dPercentChange'] = item['percentChange']
            inst['1wPriceChange'] = item['weekAgoChange']
            inst['1wPercentChange'] = item['weekAgoPercentChange']
            context['instruments'].append(inst)
    else:
        print(f'failed to get response {r.status_code}')

    print(context)
    return render(request, template, context)

def news_view(request):
    template = 'markets/news.html'
    
    context = dict()
    context['curr_module_id'] = 'id_markets_module'
    context['news'] = list()
    for news in News.objects.all().order_by('-date'):
        n = dict()
        n['date'] = news.date
        n['link'] = news.link
        n['exchange'] = news.exchange
        n['symbol'] = news.symbol
        n['source'] = news.source
        n['text'] = news.text
        context['news'].append(n)

    print(context)
    return render(request, template, context)

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
    context['curr_module_id'] = 'id_markets_module'
    print(context)
    return render(request, template, context)