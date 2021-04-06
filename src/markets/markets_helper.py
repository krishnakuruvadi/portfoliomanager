from shares.shares_helper import get_invested_shares
from .mc import MoneyControl
import datetime
from .models import News
from django.db import IntegrityError

def get_news():
    total_results = 0
    for ish in get_invested_shares():
        print(f"getting news for {ish['exchange']} {ish['symbol']}")
        count = 0
        if ish['exchange'] in ['NSE', 'BSE', 'NSE/BSE']:
            if ish['exchange'] == 'NSE/BSE':
                mc = MoneyControl('ISIN', ish['symbol'])
            else:
                mc = MoneyControl(ish['exchange'], ish['symbol'])
            try:
                results = mc.fetch_ticker_news()
                if results:
                    for res in results:
                        if ((datetime.date.today() - res['date']).days < 30):
                            try:
                                News.objects.create(
                                    exchange=ish['exchange'],
                                    symbol=ish['symbol'],
                                    text=res['text'],
                                    date=res['date'],
                                    link=res['link'],
                                    source='moneycontrol'
                                )
                            except IntegrityError:
                                print('news exists')
                            count += 1
                            total_results += 1
                            if count > 5:
                                break
                        else:
                            print(f'stale news from {res["date"]}')
            except Exception as ex:
                print(f"Exception {ex} while getting news from MC for {ish['exchange']} {ish['symbol']}")

