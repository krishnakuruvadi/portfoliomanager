from .models import Index, HistoricalIndexPoints, HistoricalStockPrice
from shared.yahoo_finance_2 import YahooFinance2
from django.db import IntegrityError
from tasks.tasks import update_index_points
import datetime

def get_comp_index(exchange):
    if exchange == 'NASDAQ':
        return '^IXIC', 'USA'
    elif exchange == 'NYSE':
        return '^NYA', 'USA'
    elif exchange == 'BSE':
        return '^BSESN', 'India'
    elif exchange in ['NSE', 'NSE/BSE']:
        return '^NSEI', 'India'
    return None, None

def get_comp_index_vals(exchange, start_date, end_date, chart_format=True):
    symbol, country = get_comp_index(exchange)
    if chart_format:
        ret = list()
    else:
        ret = dict()
    if symbol:
        try:
            index = Index.objects.get(country=country, yahoo_symbol=symbol)
            for hip in HistoricalIndexPoints.objects.filter(index=index, date__gte=start_date, date__lte=end_date):
                if chart_format:
                    ret.append({'x':hip.date.strftime('%Y-%m-%d'), 'y':float(hip.points)})
            return index.name, ret
        except Index.DoesNotExist:
            return None, None
    return None, None

def update_indexes(start_date, end_date):
    today = datetime.date.today()
    for index in Index.objects.all():
        try:
            yf = YahooFinance2(index.yahoo_symbol)
            response = yf.get_historical_value(start_date, end_date)
            yf.close()
            last_val = 0
            for k,v in response.items():
                if (today - k).days <=5 or k.day in [25, 26, 27, 28, 29, 30, 31, 1, 2, 3, 4, 5]:
                    add_hip(index, k, v)
                elif abs((v-last_val)*100/(last_val+1)) > 1:
                        add_hip(index, k, v)
                last_val = v
        except Exception as ex:
            print(f'exception {ex} when updating index {index.country}/{index.name}')

def update_index(exchange, start_date, end_date):
    symbol, country = get_comp_index(exchange)
    if symbol:
        try:
            index = Index.objects.get(country=country, yahoo_symbol=symbol)
        except Index.DoesNotExist:
            index = Index.objects.create(
                country=country,
                name=get_name_of_index(symbol),
                yahoo_symbol=symbol
            )    
        yf = YahooFinance2(symbol)
        response = yf.get_historical_value(start_date, end_date)
        yf.close()
        last_val = 0
        for k,v in response.items():
            if k.day in [25, 26, 27, 28, 29, 30, 31, 1, 2, 3, 4, 5]:
                add_hip(index, k, v)
            elif abs((v-last_val)*100/(last_val+1)) > 1:
                    add_hip(index, k, v)
            last_val = v

def add_hip(index, date, points):
    try:
        HistoricalIndexPoints.objects.create(
            index=index,
            date = date,
            points=points
        )
    except IntegrityError as ie:
        pass

def get_name_of_index(yahoo_symbol):
    if yahoo_symbol == '^IXIC':
        return 'NASDAQ Composite'
    elif yahoo_symbol == '^BSESN':
        return 'BSE SENSEX'
    elif yahoo_symbol == 'NIFTY100_EQL_WGT.NS':
        return 'NIFTY 100 Equal Weight'
    elif yahoo_symbol == '^NYA':
        return 'NYSE Composite'
    elif yahoo_symbol == '^NSEI':
        return 'NIFTY 50'

def get_comp_index_values(stock, start_date, last_date):
    data = dict()
    data['my_name'] = stock.symbol

    start_date = start_date.replace(day=1)
    symbol, country = get_comp_index(stock.exchange)            
    if not symbol:
        return data
    try:
        index = Index.objects.get(country=country, yahoo_symbol=symbol)
        first_missing = None
        last_missing = None
        first_found = None
        last_found = None
        data['my_vals'] = list()
        data['comp_vals'] = list()
        data['comp_name'] = index.name
        data['chart_labels'] = list()
        for hsp in HistoricalStockPrice.objects.filter(symbol=stock, date__gte=start_date).order_by('date'):
            try:
                t = HistoricalIndexPoints.objects.get(index=index, date=hsp.date)
                if not first_found:
                    first_found = hsp.date
                last_found = hsp.date
                dt = hsp.date.strftime('%Y-%m-%d')
                data['comp_vals'].append({'x':dt, 'y':float(t.points)})
                data['my_vals'].append({'x':dt, 'y':float(hsp.price)})
                data['chart_labels'].append(dt)
            except HistoricalIndexPoints.DoesNotExist:
                if not first_missing:
                    first_missing = hsp.date
                last_missing = hsp.date

        if first_missing and first_found and (first_found - first_missing).days > 15:
            print(f'from get_comp_index_values: first_missing {first_missing} first_found {first_found}')
            update_index_points(stock.exchange, first_missing, first_found)
                    
        if last_missing and last_found and (last_missing - last_found).days > 15:
            print(f'from get_comp_index_values: last_missing {last_missing} last_found {last_found}')
            update_index_points(stock.exchange, last_missing, last_found)
                    
        if not first_found and not last_found:
            print(f'from get_comp_index_values: first_found {first_found} last_found {last_found}')
            update_index_points(stock.exchange, start_date, last_date)

        print(f'first_missing:{first_missing} first_found:{first_found} last_missing:{last_missing}  last_found:{last_found}')
            
    except Index.DoesNotExist:
        update_index_points(stock.exchange, start_date, last_date)
    return data
