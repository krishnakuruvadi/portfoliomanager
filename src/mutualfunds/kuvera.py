import csv
from os.path import isfile
from shared.utils import *
from common.models import MutualFund
from .models import Folio
import enum
from alerts.alert_helper import create_alert, Severity
from shared.handle_real_time_data import get_mf_vals
from common.helper import get_or_add_mf_obj
import requests

class FundType(enum.Enum):
    growth = 1
    div_payout = 2
    div_reinvest = 3

class Kuvera:
    def __init__(self, filename):
        self.filename = filename
        self.broker = 'KUVERA'
    
    def get_transactions(self):
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
                            trans_date = get_datetime_or_none_from_string(v.strip()) #2020-03-19
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
                        fund = self._get_match_from_fund_nav(folio, fund_name, trans_date, nav)
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
            code = self.get_code_from_kuv_gist(fund_name)
            if code:
                mf_obj = get_or_add_mf_obj(code)
                if mf_obj:
                    mf_obj.kuvera_name = fund_name
                    mf_obj.save()
                    return code
                else:
                    print(f'couldnt find mf object for {code}')
            else:
                print('couldnt get mf code from gist')
            
            for mf_obj in MutualFund.objects.all():
                if mf_obj.bse_star_name and self._matches_bsestar(fund_name, mf_obj.bse_star_name):
                    mf_obj.kuvera_name = fund_name
                    mf_obj.save()
                    return mf_obj.code
        print('couldnt find match with bse star name for fund:', fund_name)
        return None

    def get_code_from_kuv_gist(self, kuv_name):
        url = b'\x03\x11\r\x07\x1cHKD\x02\x10\x04\x1b\\\x03\x02\x11\x11\x02\r\\\x07\x04\x08V\x1c\x1d\x1b\x17\x03\x0b\x18\x1c\x1a\x00\x11\x1d\x04\x1d\x1e@\x17SYRHG[A\x01Y\\\x1bC\x0bKTSVIN[\x14\x06X\x04\x1c\x11\nK\x01]VV\x05\x0e\x05K\t\x00A\x14ZG\x00\\T\x1aB_KPZ\x06MB\rBQYRH\x14\\\x10QS\\I\x13WJ\x00\tWO\x12Z]\x0f\x1e\x13\x1c\x05\x0e\\\x07\x18\x13'
        url = k_decode(url)
            
        r = requests.get(url, timeout=15)
        if r.status_code==200:
            decoded_content = r.content.decode('utf-8')
            csv_reader = csv.DictReader(decoded_content.splitlines(), delimiter=',')
            for row in csv_reader:
                #print(row)
                if row['kuvera_name'] == kuv_name:
                    return row['code']
        else:
            print(f'failed to get mf from gist for kuvera {r.status_code}')
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

    def _get_match_from_fund_nav(self, folio, fund_name, trans_date, nav):
        print('Getting fund bse star name using nav and transaction date')
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
        
        for mf_obj in MutualFund.objects.all():
            if not mf_obj.bse_star_name:
                continue
            bse_star_name = mf_obj.bse_star_name
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
            if b_direct == k_direct:
                if b_fund_type and b_fund_type == k_fund_type:
                    if bse_star_name.split(' ')[0].lower() == fund_name.split(' ')[0].lower():
                        vals = get_mf_vals(mf_obj.code, datetime.date(trans_date.year, trans_date.month, trans_date.day), datetime.date(trans_date.year, trans_date.month, trans_date.day))
                        if vals:
                            for k,v in vals.items():
                                print(k,':',v, 'compare nav:',nav)
                                if v == nav:
                                    create_alert(
                                        summary='Folio:' + folio + ' Guess to add transaction',
                                        content= 'Not able to find a exact matching entry between Kuvera name and BSE STaR name. Made a guess with the name.  If incorrect, delete the folio, update the mf_mapping.json and retry upload',
                                        severity=Severity.warning
                                    )
                                    mf_obj.kuvera_name = fund_name
                                    mf_obj.save()
                                    return mf_obj.code
        print(f'no match found. returning none')
        return None
