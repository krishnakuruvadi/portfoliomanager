from mftool import Mftool
import csv
import datetime
from common.models import MutualFund, MFCategoryReturns, Preferences, Passwords
from shared.utils import get_float_or_none_from_string, k_decode
import requests
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json
from django.conf import settings


def get_or_add_mf_obj(amfi_code):
    try:
        mf_obj = MutualFund.objects.get(code=amfi_code)
        return mf_obj
    except MutualFund.DoesNotExist:
        mf = Mftool()
        mf_schemes = get_scheme_codes(mf, False)

        for code, details in mf_schemes.items():
            if amfi_code == code:
                isin2 = None
                if details['isin2'] and details['isin2'] != '' and details['isin2'] != '-':
                    isin2 = details['isin2']
                mf_obj = MutualFund.objects.create(code=code,
                                                name=details['name'],
                                                isin=details['isin1'],
                                                isin2=isin2,
                                                fund_house=details['fund_house'],
                                                collection_start_date=datetime.date.today())
                return mf_obj
    mf_details = get_mf_details_from_gist(amfi_code)
    if mf_details:
        mf_obj = MutualFund.objects.create(code=amfi_code,
                                            name=details['name'],
                                            isin=details.get('isin1', None),
                                            isin2=details.get('isin2', None),
                                            fund_house=details['fund_house'],
                                            collection_start_date=datetime.date.today())
        return mf_obj
    return None

def get_kuv_name_from_gist(code):
    url = b'\x03\x11\r\x07\x1cHKD\x02\x10\x04\x1b\\\x03\x02\x11\x11\x02\r\\\x07\x04\x08V\x1c\x1d\x1b\x17\x03\x0b\x18\x1c\x1a\x00\x11\x1d\x04\x1d\x1e@\x17SYRHG[A\x01Y\\\x1bC\x0bKTSVIN[\x14\x06X\x04\x1c\x11\nK\x01]VV\x05\x0e\x05K\t\x00A\x14ZG\x00\\T\x1aB_KPZ\x06MB\rBQYRH\x14\\\x10QS\\I\x13WJ\x00\tWO\x12Z]\x0f\x1e\x13\x1c\x05\x0e\\\x07\x18\x13'
    url = k_decode(url)
            
    r = requests.get(url, timeout=15)
    if r.status_code==200:
        decoded_content = r.content.decode('utf-8')
        csv_reader = csv.DictReader(decoded_content.splitlines(), delimiter=',')
        for row in csv_reader:
            #print(row)
            if row['code'] == code:
                return row['kuvera_name']
    else:
        print(f'failed to get mf from gist for kuvera {r.status_code}')
        return None

def get_mf_details_from_gist(code):
    url = b'\x03\x11\r\x07\x1cHKD\x02\x10\x04\x1b\\\x03\x02\x11\x11\x02\r\\\x07\x04\x08V\x1c\x1d\x1b\x17\x03\x0b\x18\x1c\x1a\x00\x11\x1d\x04\x1d\x1e@\x17SYRHG[A\x01Y\\\x1bC\x0bKTSVIN[\x14\x06X\x04\x1c\x11\nK\x01]VV\x05\x0e\x05K\x0eUME[GU[W\x1cA\x0e\x14V\tVA\x14\x0b\x17V\r\\MB]\x16SZ\x01@A\r@\x05\rWMO\\]\t\rK\x1a\x04\x19'
    url = k_decode(url)
            
    r = requests.get(url, timeout=15)
    if r.status_code==200:
        decoded_content = r.content.decode('utf-8')
        csv_reader = csv.DictReader(decoded_content.splitlines(), delimiter=',')
        for row in csv_reader:
            #print(row)
            if row['code'] == code:
                ret = {
                    'name': row['name'],
                    'fund_house':row['fund_house']
                }
                if row['isin'] != '':
                    ret ['isin'] = row['isin']
                if row['isin2'] != '':
                    ret ['isin2'] = row['isin2']
                return ret
    else:
        print(f'failed to get mf from gist for kuvera {r.status_code}')
        return None

def update_mf_details():
    url = b'\x03\x11\r\x07\x1cHKD\x02\x10\x04\x1b\\\x03\x02\x11\x11\x02\r\x07\x17\x0e\x17\x1a\x18\x01\x06\x01\x05\x11W\x14\x00\x1fK\x00\x17\x10\x04\x07\x1c\x05\x00\x10\x0b\x02\x19\x13\x00\x02JMG\x0bF\x00\tWI\x16ZJP\x0fU\x1bE\x0c@\x07[P\x18N_B\x00\x0fP\x1c\x15^\x16K\x19\x04\x0eX\\FR\x0e]\x1dD\rC\x06\rP\x1f\x14W\x17P_\x07\x1c\x14\x0b\x13S[\x07\x1a\x11Z\x17RSTNB\nFSYQV\x1a\x1c\\\x07\x18\x13'
    url = k_decode(url)        
    r = requests.get(url, timeout=15)
    if r.status_code==200:
        decoded_content = r.content.decode('utf-8')
        csv_reader = csv.DictReader(decoded_content.splitlines(), delimiter=',')
        for mf_obj in MutualFund.objects.all():
            for row in csv_reader:
                #print(row)
                if row['code'] == mf_obj.code:
                    if row['ms_name'] != '':
                        mf_obj.ms_name = row['ms_name']
                        mf_obj.ms_id = row['ms_id']
                        mf_obj.category = row['ms_category']
                        mf_obj.investment_style = row['ms_investment_style']
                        mf_obj.save()
                    break

def update_mf_scheme_codes():
    print("inside update_mf_scheme_codes")
    mf = Mftool()
    mf_schemes = get_scheme_codes(mf, False)
    #print(mf_schemes)
    changed = 0
    added = 0
    for code, details in mf_schemes.items():
        isin2 = None
        if details['isin2'] and details['isin2'] != '' and details['isin2'] != '-':
            isin2 = details['isin2']
        mf_obj = None
        try:
            mf_obj = MutualFund.objects.get(code=code)
        except MutualFund.DoesNotExist:
            mf_obj = MutualFund.objects.create(code=code,
                                               name=details['name'],
                                               isin=details['isin1'],
                                               isin2=isin2,
                                               fund_house=details['fund_house'],
                                               collection_start_date=datetime.date.today())
            print('added mutual fund with code', code)
            added = added + 1
        details_changed = False
        if mf_obj.isin != details['isin1']:
            mf_obj.isin = details['isin1']
            details_changed = True
        if mf_obj.isin2 != isin2:
            mf_obj.isin2 = isin2
            details_changed = True
        if mf_obj.name != details['name']:
            mf_obj.name = details['name']
            details_changed = True
        if details_changed:
            changed = changed + 1
            mf_obj.save()
    if added or changed:
        print('Addition to schemes:', added,'. Changed scheme details:', changed)
    else:
        print('No addition or changes detected in mutual fund schemes')

def get_fund_houses():
    print("inside get_fund_houses")
    mf = Mftool()
    ret = set()
    '''
    data = mf.get_all_amc_profiles(False)

    if data:
        for e in data:
            ret.add(e['Name of the Mutual Fund'])
        return ret
    '''
    url = mf._get_quote_url
    response = mf._session.get(url)
    data = response.text.split("\n")
    probable_fh = ''
    for scheme_data in data:
        if not ";" in scheme_data and scheme_data.strip() != "":
            probable_fh = scheme_data.strip()
        elif ";" in scheme_data:
            if probable_fh != "":
                ret.add(probable_fh)
            probable_fh = ''
    return ret

def get_scheme_codes(mf, as_json=False):
    """
    returns a dictionary with key as scheme code and value as scheme name.
    cache handled internally
    :return: dict / json
    """
    scheme_info = {}
    url = mf._get_quote_url
    response = mf._session.get(url)
    data = response.text.split("\n")
    fund_house = ""
    for scheme_data in data:
        if ";INF" in scheme_data:
            scheme = scheme_data.rstrip().split(";")
            #print(scheme[1],', ',scheme[2])
            scheme_info[scheme[0]] = {'isin1': scheme[1],
                                      'isin2':scheme[2],
                                      'name':scheme[3],
                                      'nav':scheme[4],
                                      'date':scheme[5],
                                      'fund_house':fund_house}
        elif scheme_data.strip() != "":
            fund_house = scheme_data.strip()

    return mf.render_response(scheme_info, as_json)

def update_category_returns(json_input):
    for k,v in json_input.items():
        cat_row = None
        try:
            cat_row = MFCategoryReturns.objects.get(category=k)
        except MFCategoryReturns.DoesNotExist:
            cat_row = MFCategoryReturns.objects.create(category=k)
        if cat_row:
            cat_row.return_1d_avg = get_float_or_none_from_string(v['1D']['avg'])
            cat_row.return_1d_top = get_float_or_none_from_string(v['1D']['top'])
            cat_row.return_1d_bot = get_float_or_none_from_string(v['1D']['bottom'])
            cat_row.return_1w_avg = get_float_or_none_from_string(v['1W']['avg'])
            cat_row.return_1w_top = get_float_or_none_from_string(v['1W']['top'])
            cat_row.return_1w_bot = get_float_or_none_from_string(v['1W']['bottom'])
            cat_row.return_1m_avg = get_float_or_none_from_string(v['1M']['avg'])
            cat_row.return_1m_top = get_float_or_none_from_string(v['1M']['top'])
            cat_row.return_1m_bot = get_float_or_none_from_string(v['1M']['bottom'])
            cat_row.return_3m_avg = get_float_or_none_from_string(v['3M']['avg'])
            cat_row.return_3m_top = get_float_or_none_from_string(v['3M']['top'])
            cat_row.return_3m_bot = get_float_or_none_from_string(v['3M']['bottom'])
            cat_row.return_6m_avg = get_float_or_none_from_string(v['6M']['avg'])
            cat_row.return_6m_top = get_float_or_none_from_string(v['6M']['top'])
            cat_row.return_6m_bot = get_float_or_none_from_string(v['6M']['bottom'])
            cat_row.return_1y_avg = get_float_or_none_from_string(v['1Y']['avg'])
            cat_row.return_1y_top = get_float_or_none_from_string(v['1Y']['top'])
            cat_row.return_1y_bot = get_float_or_none_from_string(v['1Y']['bottom'])
            cat_row.return_3y_avg = get_float_or_none_from_string(v['3Y']['avg'])
            cat_row.return_3y_top = get_float_or_none_from_string(v['3Y']['top'])
            cat_row.return_3y_bot = get_float_or_none_from_string(v['3Y']['bottom'])
            cat_row.return_5y_avg = get_float_or_none_from_string(v['5Y']['avg'])
            cat_row.return_5y_top = get_float_or_none_from_string(v['5Y']['top'])
            cat_row.return_5y_bot = get_float_or_none_from_string(v['5Y']['bottom'])
            cat_row.return_10y_avg = get_float_or_none_from_string(v['10Y']['avg'])
            cat_row.return_10y_top = get_float_or_none_from_string(v['10Y']['top'])
            cat_row.return_10y_bot = get_float_or_none_from_string(v['10Y']['bottom'])
            cat_row.return_ytd_avg = get_float_or_none_from_string(v['YTD']['avg'])
            cat_row.return_ytd_top = get_float_or_none_from_string(v['YTD']['top'])
            cat_row.return_ytd_bot = get_float_or_none_from_string(v['YTD']['bottom'])
            cat_row.return_inception_avg = get_float_or_none_from_string(v['Inception']['avg'])
            cat_row.return_inception_top = get_float_or_none_from_string(v['Inception']['top'])
            cat_row.return_inception_bot = get_float_or_none_from_string(v['Inception']['bottom'])
            cat_row.save()

def get_preferences(key):
    config = Preferences.get_solo()
    if hasattr(config, key):
        return getattr(config, key)
    return None

def get_password(id, token):
    pass_file = get_password_file()
    if not os.path.exists(pass_file):
        return None
    data = None
    with open(pass_file) as f:
        data = json.load(f)
    if not data:
        return None
    key = load_key(id)
    if not key:
        return None
    f = Fernet(key)
    decrypted_passwd = f.decrypt(token)
    passwd = decrypted_passwd.decode()
    return passwd

def add_or_edit_password(user, source, user_id, passwd, additional_passwd, input_additional_field, notes):
    pass_file = get_password_file()
    if not os.path.exists(pass_file):
        return 'ERROR: Password file not found'
    data = None
    with open(pass_file) as f:
        data = json.load(f)
    try:
        existing_password = Passwords.objects.get(user=user, user_id=user_id, source=source)
        token, token2, _ = encrypt_password(passwd, additional_passwd, existing_password.id)
        existing_password.password = token
        existing_password.additional_password = token2
        existing_password.additional_input = input_additional_field
        existing_password.notes = notes
        existing_password.last_updated=datetime.date.today()
        existing_password.save()
    except Passwords.DoesNotExist:
        token, token2, f = encrypt_password(passwd, additional_passwd, None)

        passwd_obj = Passwords.objects.create(
            user=user,
            user_id=user_id,
            password=token,
            additional_password=token2,
            additional_input=input_additional_field,
            source=source,
            notes=notes,
            last_updated=datetime.date.today()
        )
        write_key(passwd_obj.id, f)

def get_secrets_path():
    path = os.path.join(settings.MEDIA_ROOT, "secrets")
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def get_password_file():
    password_file = "passwords.json"
    path = os.path.join(get_secrets_path(), password_file)
    return path

def add_master_password(password):
    data = dict()
    data['masterPassword'] = password
    pass_file = get_password_file()
    if not os.path.exists(pass_file):
        with open(pass_file, 'w') as json_file:
            json.dump(data, json_file)
    else:
        print('Password file exists.  Cant change master password')

def get_master_password():
    pass_file = get_password_file()
    if not os.path.exists(pass_file):
        return None
    data = None
    with open(pass_file) as f:
        data = json.load(f)
    
    if 'masterPassword' in data:
        return data['masterPassword']
    return None

def encrypt_password(passwd, additional_passwd, id):
    master_passwd = get_master_password().encode()
    password = passwd.encode()
    if not id:
        salt = os.urandom(16)
        kdf = PBKDF2HMAC (
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_passwd))
        f = Fernet(key)
    else:
        f = load_key(id)
    if not f:
        return None, None, None
    token = f.encrypt(password)
    #token = token.encode('base64')
    token2 = None
    if additional_passwd and additional_passwd != '':
        additional_password = additional_passwd.encode('utf_8')
        token2 = f.encrypt(additional_password)
        #token2 = token2.encode('base64')
    return token, token2, key

def write_key(id, f):
    key_path = os.path.join(get_secrets_path(), str(id)+'.key')
    with open(key_path, "wb") as key_file:
        key_file.write(f)

def load_key(id):
    """
    Load the previously generated key
    """
    key_path = os.path.join(get_secrets_path(), str(id)+'.key')
    if not os.path.exists(key_path):
        return None

    return open(key_path, "rb").read()

def get_supported_mf_brokers():
    brokers = list()
    brokers.append('KUVERA')
    brokers.append('COIN ZERODHA')
    return brokers

'''
returns list of dicts containing details of passwords
'''
def get_mf_passwords():
    passwords = list()
    brokers = get_supported_mf_brokers()
    password_objs = Passwords.objects.all()
    for po in password_objs:
        if po.source in brokers:
            pw = dict()
            pw['broker'] = po.source
            pw['user'] = po.user
            pw['user_id'] = po.user_id
            pw['password'] = get_password(po.id, po.password)
            if po.additional_password:
                pw['password2'] = get_password(po.id, po.additional_password)
            pw['additional_field'] = po.additional_input
            passwords.append(pw)
    return passwords
