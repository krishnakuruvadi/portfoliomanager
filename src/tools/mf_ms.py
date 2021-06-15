import csv
import os
import pathlib
import requests

from mftool import Mftool

def get_float_or_zero_from_string(input, printout=True):
    if input != None and input != '':
        try:
            res = float(input)
            return res
        except Exception as e:
            if printout:
                print('error converting ', input, ' to float. returning 0')
    return 0

def get_amfi_schemes():
    """
    returns a dictionary with key as scheme code and value as scheme name.
    cache handled internally
    :return: dict / json
    """
    mf = Mftool()
    scheme_info = {}
    url = mf._get_quote_url
    response = mf._session.get(url)
    data = response.text.split("\n")
    for scheme_data in data:
        if ";INF" in scheme_data:
            scheme = scheme_data.rstrip().split(";")
            if get_float_or_zero_from_string(scheme[4]) > 0:
                scheme_info[scheme[0]] = {'isin1': scheme[1],
                                        'isin2':scheme[2],
                                        'name':scheme[3],
                                        }
            else:
                print(f'ignoring {scheme[4]} nav fund {scheme[3]}')
    return scheme_info

def get_funds_details(csv_file):
    data = dict()
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        header = True
        for row in reader:
            if not header:
                data[row[0]] = {'ms_name':row[1], 'ms_category':row[2], 'ms_investment_style':row[3], 'ms_id':row[4]}
            header = False
    added = 0
    modified = 0
    ic = get_investment_categories()
    b = blend_mapping()
    a_schemes = get_amfi_schemes()

    for cat,cat_name in ic.items():
        page = 1
        print("getting a list of funds for: " + cat)
        number_of_loops = None

        while True:

            funds_url = 'https://lt.morningstar.com/api/rest.svc/dk7pkae7kl/security/screener?page=' + str(page) + \
                        '&pageSize=50&sortOrder=LegalName%20asc&outputType=json&version=1&languageId=en-GB&currencyId=INR'+ \
                        '&universeIds=FOIND%24%24ALL%7CFCIND%24%24ALL&securityDataPoints=SecId%7CName%7CPriceCurrency'+ \
                        '%7CTenforeId%7CLegalName%7CClosePrice%7CClosePriceDate%7CYield_M12%7COngoingCharge%7CCategoryName'+ \
                        '%7CAnalystRatingScale%7CStarRatingM255%7CSustainabilityRank%7CGBRReturnD1%7CGBRReturnW1%7CGBRReturnM1'+ \
                        '%7CGBRReturnM3%7CGBRReturnM6%7CHoldingTypeId%7CGBRReturnM0%7CGBRReturnM12%7CGBRReturnM36%7CGBRReturnM60'+ \
                        '%7CGBRReturnM120%7CMaxFrontEndLoad%7CManagerTenure%7CMaxDeferredLoad%7CInitialPurchase%7CExpenseRatio'+ \
                        '%7CFundTNAV%7CEquityStyleBox%7CBondStyleBox%7CAverageMarketCapital%7CAverageCreditQualityCode%7CEffectiveDuration'+ \
                        '%7CMorningstarRiskM255%7CAlphaM36%7CBetaM36%7CR2M36%7CStandardDeviationM36%7CSharpeM36%7CTrackRecordExtension%7CISIN'+ \
                        '&filters=CategoryId%3AIN%3A' + cat + '&term=&subUniverseId='
            
            page_list_funds = requests.get(funds_url)
            page_list_funds_json = page_list_funds.json()
            if not number_of_loops:
                number_of_loops = page_list_funds_json['total'] // page_list_funds_json['pageSize'] + 1
            
            for row in page_list_funds_json['rows']:
                if type(row) is list:
                    for subrow in row:
                        if not 'ISIN' in subrow:
                            continue
                        isin = subrow['ISIN']
                        for code,det in a_schemes.items():
                            if det['isin1'] == isin or det['isin2'] == isin:
                                if code in data:
                                    m = False
                                    if data[code]['ms_name'] != subrow['Name']:
                                        data[code]['ms_name'] = subrow['Name']
                                        m = True
                                    if data[code]['ms_category'] != cat_name:
                                        data[code]['ms_category'] = cat_name
                                        m = True
                                    if 'EquityStyleBox' in subrow:
                                        if data[code]['ms_investment_style'] != b[subrow['EquityStyleBox']]:
                                            data[code]['ms_investment_style'] = b[subrow['EquityStyleBox']]
                                            m = True
                                    if data[code]['ms_id'] != subrow['SecId']:
                                        data[code]['ms_id'] = subrow['SecId']
                                        m = True
                                    if m:
                                        modified += 1
                                else:
                                    mis = ''
                                    if 'EquityStyleBox' in row:
                                        mis = b[subrow['EquityStyleBox']]
                                    data[code] = {'ms_name':subrow['Name'], 'ms_category':cat_name, "ms_investment_style":mis, 'ms_id':subrow['SecId']}
                                    added += 1
                                break
                else:
                    #print(row)
                    if not 'ISIN' in row:
                        continue
                    isin = row['ISIN']
                    for code,det in a_schemes.items():
                        if det['isin1'] == isin or det['isin2'] == isin:
                            if code in data:
                                m = False
                                if data[code]['ms_name'] != row['Name']:
                                    data[code]['ms_name'] = row['Name']
                                    m = True
                                if data[code]['ms_category'] != cat_name:
                                    data[code]['ms_category'] = cat_name
                                    m = True
                                if 'EquityStyleBox' in row:
                                    if data[code]['ms_investment_style'] != b[row['EquityStyleBox']]:
                                        data[code]['ms_investment_style'] = b[row['EquityStyleBox']]
                                        m = True
                                if data[code]['ms_id'] != row['SecId']:
                                    data[code]['ms_id'] = row['SecId']
                                    m = True
                                if m:
                                    modified += 1
                            else:
                                mis = ''
                                if 'EquityStyleBox' in row:
                                    mis = b[row['EquityStyleBox']]
                                data[code] = {'ms_name':row['Name'], 'ms_category':cat_name, "ms_investment_style":mis, 'ms_id':row['SecId']}
                                added += 1
                            break
            
            page += 1
            if page > number_of_loops:
                break
    print(f'added {added} modified {modified}')
    if added >0 or modified > 0:
        fields = ['code','ms_name','ms_category','ms_investment_style','ms_id']
        with open(csv_file, 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(fields)
            for i in sorted (data.keys()) :
                csvwriter.writerow([i, data[i]['ms_name'], data[i]['ms_category'], data[i]['ms_investment_style'], data[i]['ms_id']])

def blend_mapping():
    return {
        1:'Large Value',
        2:'Large Blend',
        3:'Large Growth',
        4:'Mid Value',
        5:'Mid Blend',
        6:'Mid Growth',
        7:'Small Value',
        8:'Small Blend',
        9:'Small Growth'
    }

def get_path_to_ms_csv():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    csv_file = os.path.join(path, 'ms.csv')
    return csv_file

def get_investment_categories():
    return {
        'INCA000008':'10 yr Government Bond',
        'INCA000043':'Aggressive Allocation',
        'INCA000038':'Arbitrage Fund',
        'INCA000012':'Balanced Allocation',
        'INCA000065':'Banking & PSU',
        'INCA000070':'Children',
        'INCA000013':'Conservative Allocation',
        'INCA000057':'Contra',
        'INCA000064':'Corporate Bond',
        'INCA000050':'Credit Risk',
        'INCA000058':'Dynamic Yield',
        'INCA000044':'Dynamic Asset Allocation',
        'INCA000053':'Dynamic Bond',
        'INCA000033':'ELSS',
        'INCA000072':'Equity - Consumption',
        'INCA000076':'Equity - ESG',
        'INCA000051':'Equity - Infrastructure',
        'INCA000031':'Equity - Other',
        'INCA000068':'Equity - Savings',
        'INCA000049':'Fixed Maturity Intermediate-Term Bond',
        'INCA000016':'Fixed Maturity Short-Term Bond',
        'INCA000017':'Fixed Maturity Ultrashort-Term Bond',
        'INCA000077':'Flexi Cap',
        'INCA000066':'Floating Rate',
        'INCA000059':'Focused Fund',
        'INCA000071':'Fund of Funds',
        'INCA000037':'Global - Other',
        'INCA000009':'Government Bond',
        'INCA000060':'Index Funds',
        'INCA000055':'Large & Mid-Cap',
        'INCA000001':'Large-Cap',
        'INCA000011':'Liquid',
        'INCA000042':'Long Duration',
        'INCA000061':'Low Duration',
        'INCA000063':'Medium Duration',
        'INCA000034':'Medium to Long Duration',
        'INCA000002':'Mid-Cap',
        'INCA000062':'Money Market',
        'INCA000052':'Multi Asset Allocation',
        'INCA000048':'Multi-Cap',
        'INCA000046':'Other Bond',
        'INCA000067':'Overnight',
        'INCA000069':'Retirement',
        'INCA000030':'Sector - Financial Services',
        'INCA000028':'Sector - FMCG',
        'INCA000003':'Sector - Healthcare',
        'INCA000032':'Sector - Precious Metals',
        'INCA000004':'Sector - Technology',
        'INCA000006':'Short Duration',
        'INCA000054':'Small-Cap',
        'INCA000007':'Ulta Short Duration',
        'INCA000056':'Value'
    }

if __name__ == "__main__":
    csv_file = get_path_to_ms_csv()
    get_funds_details(csv_file)