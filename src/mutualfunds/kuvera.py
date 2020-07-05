import csv
from os.path import isfile
from shared.utils import *
from common.models import MutualFund
from .models import Folio

class Kuvera:
    def __init__(self, filename):
        self.filename = filename
        self.broker = 'KUVERA'
    
    def get_transactions(self):
        if isfile(self.filename):
            with open(self.filename, mode='r', encoding='utf-8-sig') as csv_file:
                print("opened file as csv:", self.filename)
                csv_reader = csv.DictReader(csv_file, delimiter=",")
                for row in csv_reader:
                    print(row)
                    folio = row['Folio Number']
                    trans_date = get_date_or_none_from_string(row['Date'])
                    fund_name = row['Name of the Fund']
                    trans_type = 'Buy' if row['Order']=='buy' else 'Sell'
                    units = get_float_or_none_from_string(row['Units'])
                    nav = get_float_or_none_from_string(row['NAV'])
                    trans_value = get_float_or_none_from_string(row['Amount (INR)'])
    
    def _get_folio(self, folio, fund_name):
        folio_obj = None
        try:
            folio_obj = Folio.objects.get(folio=folio)
        except Folio.DoesNotExist:
            pass
        return folio_obj