import csv
from os.path import isfile
from shared.utils import *
from common.models import MutualFund
from alerts.alert_helper import create_alert, Severity
from django.db.models import Q


class Coin:
    def __init__(self, filename):
        self.filename = filename
        self.broker = 'COIN ZERODHA'
    
    def get_transactions(self):
        if isfile(self.filename):
            ignored_folios = set()
            with open(self.filename, mode='r', encoding='utf-8-sig') as csv_file:
                print("opened file as csv:", self.filename)
                csv_reader = csv.DictReader(csv_file, delimiter=",")
                for row in csv_reader:
                    #client_id	isin	scheme_name	plan	transaction_mode	trade_date	ordered_at	folio_number	amount	units	nav	status	remarks
                    for k,v in row.items():
                        if 'isin' in k:
                            isin = v.strip()
                        if 'folio_number'in k:
                            folio = v.strip()
                        elif 'trade_date'in k:
                            trans_date = get_datetime_or_none_from_string(v.strip()) #2020-03-19
                        elif 'transaction_mode'in k:
                            trans_type = 'Buy' if 'BUY' in v else 'Sell'
                        elif 'units'in k:
                            units = get_float_or_none_from_string(v.strip())
                        elif 'nav'in k:
                            nav = get_float_or_none_from_string(v.strip())
                        elif 'amount'in k:
                            trans_value = get_float_or_none_from_string(v.strip())
                    fund, description = self._get_fund(isin, folio)
                    if fund:
                        yield {'folio':folio,
                            'trans_date':trans_date, 
                            'fund':fund,
                            'trans_type':trans_type,
                            'units':units,
                            'nav':nav,
                            'trans_value':trans_value}
                    else:
                        create_alert(
                            summary='Folio:' + folio + ' Failure to add transactions',
                            content= description,
                            severity=Severity.error
                        )
        else:
            print(f'{self.filename} is not a file or doesnt exist')

    def _get_fund(self, isin, folio):
        fund = MutualFund.objects.filter(Q(isin=isin) | Q(isin2=isin))
        if len(fund) == 1:
            return fund[0].code, ''
        elif len(fund) > 1:
            print(f'too many matching values for isin {isin}')
            return None, 'too many matching values for isin '+ isin + ' for folio:'+ folio
        print(f'couldnt find match with isin for fund: {isin}')
        return None, 'couldnt find match with isin ' + isin + ' for folio:'+ folio
    