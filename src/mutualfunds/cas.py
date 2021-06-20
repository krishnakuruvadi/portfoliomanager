
from os.path import isfile
import casparser
from shared.utils import *
from common.models import MutualFund
from alerts.alert_helper import create_alert, Severity
from django.db.models import Q

class CAS:
    def __init__(self, filename, passwd):
        self.filename = filename
        self.passwd = passwd
    
    def get_transactions(self):
        if isfile(self.filename):
            data = casparser.read_cas_pdf(self.filename, self.passwd)
            print(data)
            if data['cas_type'] != 'DETAILED':
                print(f'failed to add mutual fund transactions since document is not detailed')
                return list()
            for folio in data['folios']:
                folio_num = folio['folio'].replace(' ','')
                if folio_num.endswith('/0'):
                    folio_num = folio_num.replace('/0','')
                for scheme in folio['schemes']:
                    if scheme['advisor'] == 'INA200005166' or scheme['advisor'] == '000000-0':
                        broker = 'KUVERA'
                    elif scheme['advisor'] == 'INZ000031633':
                        broker = 'COIN ZERODHA'
                    elif scheme['advisor'] == 'INA200011107':
                        broker = 'SCRIPBOX'
                    elif scheme['advisor'] == 'INA100009859':
                        broker = 'PAYTM MONEY'
                    elif scheme['advisor'] == 'INA000006651':
                        broker = 'NIYO MONEY'
                    elif scheme['advisor'] == 'INZ000208032':
                        broker = 'GROWW'
                    elif scheme['advisor'] == 'INA100006898':
                        broker = 'ET MONEY'
                    else:
                        broker = scheme['advisor']
                    
                    isin = scheme['isin']
                    amfi_code = scheme['amfi']
                    fund, description  = self._get_fund(isin, folio_num)
                    if not fund:
                        create_alert(
                            summary='Folio:' + folio_num + ' Failure to add transactions',
                            content= description,
                            severity=Severity.error
                        )
                        continue
                    for trans in scheme['transactions']:
                        if 'tax' in trans['type'].lower():
                            continue
                        trans_date = trans['date']
                        if 'redemption' in trans['type'].lower():
                            trans_type = 'Sell'
                        elif 'purchase' in trans['type'].lower():
                            trans_type = 'Buy'
                        else:
                            print(f"ignoring transaction of type {trans['type']}")
                        units = trans['units']
                        nav = trans['nav']
                        trans_value = trans['amount']
                        yield {'folio':folio_num,
                            'trans_date':trans_date,
                            'fund':fund,
                            'trans_type':trans_type,
                            'units':float(units),
                            'nav':float(nav),
                            'trans_value':float(trans_value),
                            'broker':broker}

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