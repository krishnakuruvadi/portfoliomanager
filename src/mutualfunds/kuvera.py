import csv
from os.path import isfile
from shared.utils import *
from common.models import MutualFund
from .models import Folio
import enum
from alerts.alert_helper import create_alert, Severity

class FundType(enum.Enum):
    growth = 1
    div_payout = 2
    div_reinvest = 3

class Kuvera:
    def __init__(self, filename):
        self.filename = filename
        self.broker = 'KUVERA'
    
    def get_transactions(self):
        transactions = dict()
        if isfile(self.filename):
            ignored_folios = set()
            with open(self.filename, mode='r', encoding='utf-8-sig') as csv_file:
                print("opened file as csv:", self.filename)
                csv_reader = csv.DictReader(csv_file, delimiter=",")
                for row in csv_reader:
                    #OrderedDict([('Date', '    2020-03-19'), (' Folio Number', '91011317175'), (' Name of the Fund', 'Motilal Oswal Focused 25 Growth Direct Plan'), (' Order', 'buy'), (' Units', '257.375'), (' NAV', '19.4269'), (' Current Nav', '20.3781'), (' Amount (INR)', '5000.0')])
                    for k,v in row.items():
                        if 'Folio Number'in k:
                            folio = v.strip()
                        elif 'Date'in k:
                            trans_date = get_date_or_none_from_string(v.strip()) #2020-03-19
                        elif 'Name of the Fund'in k:
                            fund_name = v.strip()
                        elif 'Order'in k:
                            trans_type = 'Buy' if 'buy' in v else 'Sell'
                        elif 'Units'in k:
                            units = get_float_or_none_from_string(v.strip())
                        elif 'NAV'in k:
                            nav = get_float_or_none_from_string(v.strip())
                        elif 'Amount (INR)'in k:
                            trans_value = get_float_or_none_from_string(v.strip())
                    fund = self._get_fund(fund_name)
                    if fund:
                        yield {'folio':folio,
                            'trans_date':trans_date, 
                            'fund':fund,
                            'trans_type':trans_type,
                            'units':units,
                            'nav':nav,
                            'trans_value':trans_value}
                    else:
                        ignored_folios.add(folio)
            for fol in ignored_folios:
                create_alert(
                    summary='Folio:' + fol + ' Failure to add transactions',
                    content= 'Not able to find a matching entry between Kuvera name and BSE STaR name. Edit the mf_mapping.json to process this folio',
                    severity=Severity.error
                )

    def _get_fund(self, fund_name):
        try:
            fund = MutualFund.objects.get(kuvera_name__contains=fund_name)
            return fund.code
        except MutualFund.DoesNotExist:
            for mf_obj in MutualFund.objects.all():
                if mf_obj.bse_star_name and self._matches_bsestar(fund_name, mf_obj.bse_star_name):
                    return mf_obj.code
        print('couldnt find match with bse star name for fund:', fund_name)
        return None
    
    # compare DSP Equal Nifty 50 Growth Direct Plan with DSP EQUAL NIFTY 50 FUND - DIR - GROWTH
    def _matches_bsestar(self, fund_name, bse_star_name):
        k_fund_name_lower = fund_name.lower().replace(' plan','')
        
        if 'direct' in fund_name.lower():
            k_direct = True
            k_fund_name_lower = k_fund_name_lower.replace(' direct', '')
        else:
            k_direct = False
            k_fund_name_lower = k_fund_name_lower.replace(' regular', '')
        k_fund_type = None
        if 'growth' in fund_name.lower():
            k_fund_type = FundType.growth
            k_fund_name_lower = k_fund_name_lower.replace(' growth', '')
        elif 'dividend reinvest' in fund_name.lower():
            k_fund_type = FundType.div_reinvest
            k_fund_name_lower = k_fund_name_lower.replace(' dividend reinvest', '')
        elif 'dividend payout' in fund_name.lower():
            k_fund_type = FundType.div_payout
            k_fund_name_lower = k_fund_name_lower.replace(' dividend payout', '')
        k_fund_name_lower = k_fund_name_lower.replace('&','and')
        
        bse_star_parts = list()
        bse_star_parts.append(bse_star_name[0:bse_star_name.find('-')])
        other_part = bse_star_name[bse_star_name.find('-')+1:]
        other_part = other_part.replace('-','')
        bse_star_parts.append(other_part)
        if 'growth' in bse_star_parts[1].lower():
            b_fund_type = FundType.growth
        elif 'div' in bse_star_parts[1].lower() and 'rein' in bse_star_parts[1].lower():
            b_fund_type = FundType.div_reinvest
        elif 'div' in bse_star_parts[1].lower() and 'pay' in bse_star_parts[1].lower():
            b_fund_type = FundType.div_payout
        else:
            b_fund_type = None
            
        if 'dir' in bse_star_parts[1].lower():
            b_direct = True
        else:
            b_direct = False
        b_fund_name_lower = bse_star_parts[0].lower()
        if k_fund_name_lower in b_fund_name_lower:
            if b_direct == k_direct:
                if b_fund_type and b_fund_type == k_fund_type:
                    return True
        return False
