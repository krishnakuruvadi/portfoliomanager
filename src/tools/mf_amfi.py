import csv
import os
import pathlib
from mftool import Mftool


def mf_update_csv(csv_file):
    print('inside mf_update_csv')
    
    mf_schemes, ignored = get_schemes(False)
    data = dict()
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        header = True
        for row in reader:
            if not header:
                data[row[0]] = {'name':row[1], 'isin':row[2], 'isin2':row[3], 'fund_house':row[4]}
            header = False
    added = 0
    modified = 0
    for code, details in mf_schemes.items():
        isin2 = ''
        if details['isin2'] and details['isin2'] != '' and details['isin2'] != '-':
            isin2 = details['isin2']
        if code not in data:
            data[code] = {'name':details['name'], 'isin':details['isin1'], 'isin2':isin2, 'fund_house':details['fund_house']}
            added += 1
        else:
            changed = False
            if data[code]['name'] != details['name']:
                data[code]['name'] = details['name']
                changed = True
            if data[code]['isin'] != details['isin1']:
                data[code]['isin'] = details['isin1']
                changed = True
            if data[code]['isin2'] != isin2:
                data[code]['isin2'] = isin2
                changed = True
            if data[code]['fund_house'] != details['fund_house']:
                data[code]['fund_house'] = details['fund_house']
                changed = True
            if changed:
                modified += 1
    print(f'added {added} modified {modified} ignored {ignored}')
    if added >0 or modified > 0:
        fields = ['code','name','isin','isin2','fund_house']
        with open(csv_file, 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(fields)
            for i in sorted (data.keys()) :
                csvwriter.writerow([i, data[i]['name'], data[i]['isin'], data[i]['isin2'], data[i]['fund_house']])

def get_schemes(as_json=False):
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
    fund_house = ""
    ignored = 0
    for scheme_data in data:
        if ";INF" in scheme_data:
            scheme = scheme_data.rstrip().split(";")
            if get_float_or_zero_from_string(scheme[4]) > 0:
                #print(scheme[1],', ',scheme[2])
                scheme_info[scheme[0]] = {'isin1': scheme[1],
                                        'isin2':scheme[2],
                                        'name':scheme[3],
                                        'nav':scheme[4],
                                        'date':scheme[5],
                                        'fund_house':fund_house}
            else:
                print(f'ignoring {scheme[4]} nav fund {scheme[3]}')
                ignored += 1
        elif scheme_data.strip() != "":
            if ';' not in scheme_data:
                fund_house = scheme_data.strip()
            else:
                print(f'ignoring fund with no isin: {scheme_data}')
                ignored += 1

    return mf.render_response(scheme_info, as_json), ignored

def get_float_or_zero_from_string(input):
    if input != None and input != '':
        try:
            res = float(input)
            return res
        except Exception as e:
            print('error converting ', input, ' to float. returning 0')
    return 0

def get_path_to_amfi_csv():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    csv_file = os.path.join(path, 'mf.csv')
    return csv_file

if __name__ == "__main__":
    csv_file = get_path_to_amfi_csv()
    mf_update_csv(csv_file)
