from pdfminer.high_level import extract_text
import pandas as pd
from tika import parser
import datetime

def get_date_or_none_from_string(input, format='%Y-%m-%d', printout=False):
    if input != None and input != '':
        try:
            res = datetime.datetime.strptime(input, format).date()
            return res
        except Exception as e:
            if printout:
                print('error converting ', input, ' to date. returning none' + str(e))
    return None

def get_float_or_none_from_string(input, printout=False):
    if input != None and input != '':
        try:
            res = float(input)
            return res
        except Exception as e:
            if printout:
                print('error converting ', input, ' to float. returning none')
    return None

class ICICIPruLife:
    def __init__(self, full_file_path):
        self.doc_path = full_file_path
    
    def get_transactions(self):
        parsed = parser.from_file(self.doc_path)
        #print(parsed["content"])
        prev = None
        fund = None
        last_dt_trans = list()
        transactions = dict()
        for l in parsed['content'].splitlines():
            if l.strip() == '':
                continue
            if 'TransactionDate' in l and prev:
                fund = prev.replace('TRANSACTION SUMMARY FOR ', '')
            elif 'Opening Balance' in l:
                continue
            elif 'Closing Balance' in l:
                ldt = get_date_or_none_from_string(l.split(' ')[0], '%d-%b-%Y')
                for t in last_dt_trans:
                    t['date'] = ldt
                    transactions[fund].append(t)
                last_dt_trans.clear()
                fund = None
            elif fund:
                tran = dict()
                description = ''
                field = 0
                for i, token in enumerate(l.split(' ')):
                    if i == 0:
                        dt = get_date_or_none_from_string(token, '%d-%b-%Y')
                        if dt:
                            tran['date'] = dt
                            field = 1
                        else:
                            if description == '':
                                description = token
                            else:
                                description += ' ' + token
                            field = 1
                    else:
                        temp = get_float_or_none_from_string(token)
                        if not temp and temp != 0:
                            if description == '':
                                description = token
                            else:
                                description += ' ' + token
                        else:
                            if field == 1:
                                tran['units'] = temp
                                tran['description'] = description
                            elif field == 2:
                                tran['nav'] = temp
                            elif field == 3:
                                tran['trans_amount'] = temp
                            field += 1
                if not fund in transactions:
                    transactions[fund] = list()
                if 'date' in tran:
                    transactions[fund].append(tran)
                else:
                    last_dt_trans.append(tran)
            else:
                print(f'ignore {l}')
            prev = l
        return transactions
