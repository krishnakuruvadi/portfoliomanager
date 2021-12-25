from .models import Index, HistoricalIndexPoints
from shared.yahoo_finance_2 import YahooFinance2
from django.db import IntegrityError


def get_comp_index(exchange):
    if exchange == 'NASDAQ':
        return '^IXIC', 'USA'
    elif exchange == 'NYSE':
        return '^NYA', 'USA'
    elif exchange == 'BSE':
        return '^BSESN', 'India'
    elif exchange in ['NSE', 'NSE/BSE']:
        return 'NIFTY100_EQL_WGT.NS', 'India'
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
        response = YahooFinance2(symbol).get_historical_value(start_date, end_date)
        
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