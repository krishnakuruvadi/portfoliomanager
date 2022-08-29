from .models import Stock
from shared.yahoo_finance_2 import YahooFinance2
from alerts.alert_helper import create_alert_today_if_not_exist, Severity
from common.shares_helper import is_exchange_open, get_start_time, get_end_time


def check_stock_price_change_alerts():
    ss = dict()
    for stock in Stock.objects.exclude(trading_status='Delisted').exclude(trading_status='Suspended'):
        symbol = stock.symbol
        if stock.exchange in ss:
            if not ss[stock.exchange]:
                continue
        else:
            if not is_exchange_open(stock.exchange):
                ss[stock.exchange] = False
                print(f'{stock.exchange} not open')
                continue
            else:
                print(f'{stock.exchange} open')
                ss[stock.exchange] = True
        if stock.exchange == 'NSE' or stock.exchange == 'NSE/BSE':
            symbol += '.NS'
        if stock.exchange == 'BSE':
            symbol += '.BO'
        start_time = get_start_time(stock.exchange)
        end_time = get_end_time(stock.exchange)
        y = YahooFinance2(symbol)
        v = y.get_live_price(symbol)
        if v:
            if v['pChange'] > 5:
                search_str = f"{stock.exchange} {stock.symbol} is up by"
                str = f"{search_str} {v['pChange']} %"
                print(str)

                create_alert_today_if_not_exist(
                    search_str=search_str,
                    summary=str,
                    content=str,
                    severity=Severity.info,
                    alert_type="Notification",
                    start_time=start_time,
                    end_time=end_time
                )
            elif v['pChange'] < -5:
                search_str = f"{stock.exchange} {stock.symbol} is down by"
                str = f"{search_str} {v['pChange']} %"
                print(str)

                create_alert_today_if_not_exist(
                    search_str=search_str,
                    summary=str,
                    content= str,
                    severity=Severity.info,
                    alert_type="Notification",
                    start_time=start_time,
                    end_time=end_time
                )
            else:
                print(f'{stock.exchange} {stock.symbol} change {v["pChange"]}%')

            if v['version'] == 'v2':
                if v['52wHigh'] == v['dayHigh']:
                    search_str = f"{stock.exchange} {stock.symbol} hit 52 Week high of"
                    str = f"{search_str} {v['dayHigh']}"
                    print(str)

                    create_alert_today_if_not_exist(
                        search_str=search_str,
                        summary=str,
                        content= str,
                        severity=Severity.info,
                        alert_type="Notification",
                        start_time=start_time,
                        end_time=end_time
                    )
                if v['52wLow'] == v['dayLow']:
                    search_str = f"{stock.exchange} {stock.symbol} hit 52 Week low of"
                    str = f"{search_str} {v['dayLow']}"
                    print(str)

                    create_alert_today_if_not_exist(
                        search_str=search_str,
                        summary=str,
                        content= str,
                        severity=Severity.info,
                        alert_type="Notification",
                        start_time=start_time,
                        end_time=end_time
                    )
                if v['prevClose'] > v['200dAvg'] and v['lastPrice'] < v['200dAvg']:
                    search_str = f"{stock.exchange} {stock.symbol} below 200 day average of"
                    str = f"{search_str} {v['200dAvg']}"
                    print(str)

                    create_alert_today_if_not_exist(
                        search_str=search_str,
                        summary=str,
                        content= str,
                        severity=Severity.info,
                        alert_type="Notification",
                        start_time=start_time,
                        end_time=end_time
                    )
                if v['prevClose'] < v['200dAvg'] and v['lastPrice'] > v['200dAvg']:
                    search_str = f"{stock.exchange} {stock.symbol} above 200 day average of "
                    str = f"{search_str} {v['200dAvg']}"
                    print(str)

                    create_alert_today_if_not_exist(
                        search_str=search_str,
                        summary=str,
                        content= str,
                        severity=Severity.info,
                        alert_type="Notification",
                        start_time=start_time,
                        end_time=end_time
                    )
        else:
            print(f'failed to get live price for {symbol} {stock.exchange}')
        y.close()
