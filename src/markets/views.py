from django.shortcuts import render
from .models import IndexRollingReturns, IndexYearlyReturns, IndexQuarterlyReturns, IndexMonthlyReturns, PEMonthy, PBMonthy, News
from common.models import Preferences
from shared.utils import get_float_or_zero_from_string, convert_date_to_string
import requests
from functools import cmp_to_key
from shared.yahoo_finance_2 import YahooFinance2
import datetime
from dateutil.relativedelta import relativedelta
import yfinance as yf

# Create your views here.

def markets_home(request):
    template = 'markets/markets_home.html'
    context = {'curr_module_id':'id_markets_module'}
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                            'like Gecko) '
                            'Chrome/80.0.3987.149 Safari/537.36',
            'accept-language': 'en,gu;q=0.9,hi;q=0.8', 'accept-encoding': 'gzip, deflate, br'}
    r = requests.get(headers=headers, timeout=15,
        url='https://www.wsj.com/market-data/stocks/asia/indexes?id=%7B%22application%22%3A%22WSJ%22%2C%22instruments%22%3A%5B%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FGDOW%22%2C%22name%22%3A%22The%20Global%20Dow%20(World)%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FXX%2F%2FDGW2DOWA%22%2C%22name%22%3A%22DJ%20Global%20ex%20U.S.%20(World)%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FXX%2F%2FADOW%22%2C%22name%22%3A%22Asia%20Dow%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FAU%2F%2FXAO%22%2C%22name%22%3A%22Australia%3A%20All%20Ordinaries%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FAU%2F%2FXJO%22%2C%22name%22%3A%22Australia%3A%20S%26P%2FASX%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FCN%2F%2FHSCEI%22%2C%22name%22%3A%22China%3A%20H-Share%20Index%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FCN%2F%2FSHCOMP%22%2C%22name%22%3A%22China%3A%20Shanghai%20Composite%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FCN%2F%2F399106%22%2C%22name%22%3A%22China%3A%20Shenzhen%20Composite%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FHK%2F%2FHSI%22%2C%22name%22%3A%22Hong%20Kong%3A%20Hang%20Seng%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FIN%2F%2F1%22%2C%22name%22%3A%22India%3A%20S%26P%20BSE%20Sensex%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FIN%2F%2FNIFTY50%22%2C%22name%22%3A%22India%3A%20S%26P%20CNX%20Nifty%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FID%2F%2FJAKIDX%22%2C%22name%22%3A%22Indonesia%3A%20JSX%20Index%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FJP%2F%2FNIK%22%2C%22name%22%3A%22Japan%3A%20Nikkei%20225%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FMY%2F%2FFBMKLCI%22%2C%22name%22%3A%22Malaysia%3A%20FTSE%20Bursa%20Malaysia%20KLCI%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FNZ%2F%2FNZ50GR%22%2C%22name%22%3A%22New%20Zealand%3A%20S%26P%2FNZX%2050%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FPH%2F%2FPSEI%22%2C%22name%22%3A%22Philippines%3A%20PSEi%20Index%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FKR%2F%2FSEU%22%2C%22name%22%3A%22S.%20Korea%3A%20KOSPI%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FSG%2F%2FSTI%22%2C%22name%22%3A%22Singapore%3A%20Straits%20Times%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FXX%2F%2FY9999%22%2C%22name%22%3A%22Taiwan%3A%20TAIEX%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FTH%2F%2FSET%22%2C%22name%22%3A%22Thailand%3A%20SET%22%7D%5D%2C%22expanded%22%3Atrue%2C%22refreshInterval%22%3A60000%2C%22serverSideType%22%3A%22mdc_quotes%22%7D&type=mdc_quotes')
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
    
    r = requests.get(headers=headers, timeout=15,
        url='https://www.wsj.com/market-data/stocks/us/indexes?id=%7B%22application%22%3A%22WSJ%22%2C%22instruments%22%3A%5B%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FDJIA%22%2C%22name%22%3A%22Industrial%20Average%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FDJT%22%2C%22name%22%3A%22Transportation%20Average%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FDJU%22%2C%22name%22%3A%22Utility%20Average%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FDJC%22%2C%22name%22%3A%2265%20Composite%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FDWCF%22%2C%22name%22%3A%22Total%20Stock%20Market%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FB400%22%2C%22name%22%3A%22Barron%27s%20400%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FSPX%22%2C%22name%22%3A%22500%20Index%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FSP100%22%2C%22name%22%3A%22100%20Index%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FMID%22%2C%22name%22%3A%22MidCap%20400%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FSML%22%2C%22name%22%3A%22SmallCap%20600%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FXX%2F%2FSP1500%22%2C%22name%22%3A%22SuperComp%201500%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FCOMP%22%2C%22name%22%3A%22Composite%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FNDX%22%2C%22name%22%3A%22Nasdaq%20100%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FNBI%22%2C%22name%22%3A%22Biotech%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FNYA%22%2C%22name%22%3A%22NYSE%20Composite%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FRUI%22%2C%22name%22%3A%22Russell%201000%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FRUT%22%2C%22name%22%3A%22Russell%202000%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FRUA%22%2C%22name%22%3A%22Russell%203000%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FXAU%22%2C%22name%22%3A%22PHLX%20Gold%2FSilver%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FOSX%22%2C%22name%22%3A%22PHLX%20Oil%20Service%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FSOX%22%2C%22name%22%3A%22PHLX%20Semiconductor%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FVIX%22%2C%22name%22%3A%22CBOE%20Volatility%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FBKX%22%2C%22name%22%3A%22KBW%20Bank%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FVALUG%22%2C%22name%22%3A%22Value%20Line%20(Geometric)%22%7D%2C%7B%22symbol%22%3A%22INDEX%2FUS%2F%2FAMZ%22%2C%22name%22%3A%22Alerian%20MLP%22%7D%5D%2C%22headers%22%3A%5B%7B%22label%22%3A%22Dow%20Jones%22%2C%22length%22%3A6%7D%2C%7B%22label%22%3A%22S%26P%22%2C%22length%22%3A5%7D%2C%7B%22label%22%3A%22Nasdaq%20Stock%20Market%22%2C%22length%22%3A3%7D%2C%7B%22label%22%3A%22Other%20U.S.%20Indexes%22%2C%22length%22%3A11%7D%5D%2C%22expanded%22%3Atrue%2C%22refreshInterval%22%3A60000%2C%22serverSideType%22%3A%22mdc_quotes%22%7D&type=mdc_quotes')
    if r.status_code==200:
        #print(r)
        #print(r.json())
        for k,v in r.json().items():
            print(k)
        json_data = r.json()
        print(json_data)
        for ins in json_data['data']['instrumentSets']:
            for item in ins['instruments']:
                if item['ticker'] in ['DJIA','SPX','COMP']:
                    inst = dict()
                    inst['country'] = item['country']
                    inst['name'] = item['name']
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
        today = datetime.date.today()
        vals = list()
        for index in ['^GSPC', '^DJI', '^IXIC']:
            inst = dict()
            
            last_trade_dt, last_trade_val = get_index_on(index, today)
            if last_trade_dt:
                inst['country'] = 'US'
                tickers = yf.Tickers(index)
                print(tickers.tickers[index].info)
                inst['timestamp'] = last_trade_dt.strftime("%Y-%m-%d")
                inst['name'] = tickers.tickers[index].info.get('longName', None)
                if not inst['name']:
                    inst['name'] = tickers.tickers[index].info.get('shortName', index)
                inst['oneYearHigh'] = tickers.tickers[index].info['fiftyTwoWeekHigh']
                inst['oneYearLow'] = tickers.tickers[index].info['fiftyTwoWeekLow']
                
                oneday_dt, oneday_val = get_index_on(index, last_trade_dt+relativedelta(days=-1))
                inst['1dPriceChange'] = round(last_trade_val-oneday_val, 2)
                inst['1dPercentChange'] = round((last_trade_val-oneday_val)*100/oneday_val, 2)

                onewk_dt, onewk_val = get_index_on(index, last_trade_dt+relativedelta(days=-7))
                inst['1wPriceChange'] = round(last_trade_val-onewk_val, 2)
                inst['1wPercentChange'] = round((last_trade_val-onewk_val)*100/onewk_val, 2)

                oneyr_dt, oneyr_val = get_index_on(index, last_trade_dt+relativedelta(years=-1))
                inst['1yearPriceChange'] = round(last_trade_val-oneyr_val, 2)
                inst['1yearPercentChange'] = round((last_trade_val-oneyr_val)*100/oneyr_val, 2)

                ytd_dt, ytd_val = get_index_on(index, datetime.date(year=today.year, month=1, day=1))
                inst['1dPriceChange'] = last_trade_val-ytd_val
                inst['ytdPercentageChange'] = round((last_trade_val-ytd_val)*100/ytd_val, 2)

                context['instruments'].append(inst)
    
        print(vals)
    context['curr_module_id'] = 'id_markets_module'
    print(context)
    return render(request, template, context)

def get_index_on(index, date):
    yf = YahooFinance2(index)
    response = yf.get_historical_value(date+relativedelta(days=-5), date)
    yf.close()
    if response:
        val_date = None
        val = None
        for k,v in response.items():
            if not val:
                val = v
                val_date = k
            else:
                if val_date > k:
                    val_date = k
                    val = v
        if val:
            return val_date, val
    return None, None

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

def returns_view(request):
    template = 'markets/returns_view.html'
    c =['India', 'USA']
    roll_ret = IndexRollingReturns.objects.filter(country__in=c)
    yrly_ret = IndexYearlyReturns.objects.filter(country__in=c)
    monthly_ret = IndexMonthlyReturns.objects.filter(country__in=c)
    qtrly_ret = IndexQuarterlyReturns.objects.filter(country__in=c)
    
    years = dict()
    for yr in yrly_ret:
        years[yr.year] = None
    ys = sorted(years.keys(),reverse=True)
    y_ret = list()
    for y in yrly_ret:
        found = False
        for e in y_ret:
            if e['country'] == y.country and e['name'] == y.name:
                found = True
                e[y.year] = y.ret
                break
        if not found:
            y_ret.append({'country':y.country, 'name':y.name, y.year:y.ret, 'as_on_date':y.as_on_date})

    qtrs = dict()
    for qtr in qtrly_ret:
        qtrs[qtr.quarter] = None
    qs = sorted(qtrs.keys(),reverse=True, key=cmp_to_key(month_compare))
    q_ret = list()
    for q in qtrly_ret:
        found = False
        for e in q_ret:
            if e['country'] == q.country and e['name'] == q.name:
                found = True
                e[q.quarter] = q.ret
                break
        if not found:
            q_ret.append({'country':q.country, 'name':q.name, q.quarter:q.ret, 'as_on_date':q.as_on_date})

    months = dict()
    for month in monthly_ret:
        months[month.month] = None
    ms = sorted(months.keys(),reverse=True, key=cmp_to_key(month_compare))
    m_ret = list()
    for m in monthly_ret:
        found = False
        for e in m_ret:
            if e['country'] == m.country and e['name'] == m.name:
                found = True
                e[m.month] = m.ret
                break
        if not found:
            m_ret.append({'country':m.country, 'name':m.name, m.month:m.ret, 'as_on_date':m.as_on_date})

    context = {
        'roll_ret':roll_ret, 
        'yrly_ret':y_ret, 'years':ys,
        'monthly_ret':m_ret, 'months':ms,
        'qtrly_ret':q_ret, 'quarters':qs,
        'curr_module_id': 'id_markets_module'}
    #print(context)
    return render(request, template, context)

def month_compare(item1, item2):
    i1 = item1.split('-')[1]
    i2 = item2.split('-')[1]
    if i1 < i2:
        return -1
    if i1 > i2:
        return 1
    mn = {
        'Jan':1,'Feb':2,'Mar':3,'Apr':4,
        'May':5,'Jun':6,'Jul':7,'Aug':8,
        'Sep':9,'Oct':10,'Nov':11,'Dec':12
    }
    i1 = mn[item1.split('-')[0]]
    i2 = mn[item2.split('-')[0]]
    if i1 < i2:
        return -1
    if i1 > i2:
        return 1
    return 0