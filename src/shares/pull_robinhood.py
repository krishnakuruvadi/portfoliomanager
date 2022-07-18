import pathlib
import os
from robin_stocks.robinhood.authentication import generate_device_token, logout
from robin_stocks.robinhood import helper
from robin_stocks.robinhood.urls import *
from robin_stocks.robinhood.authentication import respond_to_challenge
from robin_stocks.robinhood.stocks import get_symbol_by_url
from django.conf import settings
import time
import datetime
from robin_stocks.robinhood.orders import *
from shared.utils import get_date_or_none_from_string, get_float_or_none_from_string
from shared.handle_real_time_data import get_conversion_rate, get_in_preferred_currency


class Robinhood:
    def __init__(self, email_id, passwd, challenge_type, mfa, file_to_read_challenge):
        self.email_id = email_id
        self.passwd = passwd
        self.logged_in = False
        self.login_info = None
        self.challenge_type = challenge_type
        self.mfa_token = mfa
        self.challenge_answer_file = file_to_read_challenge

    def remove_old_challenge(self):
        if os.path.exists(self.challenge_answer_file):
            os.remove(self.challenge_answer_file)

    def login(self, expiresIn=86400, scope='internal'):
        if not self.logged_in:
            self.remove_old_challenge()
            #self.login_info = r.login(self.email_id,self.passwd)
            device_token = generate_device_token()
            dload_path = pathlib.Path(__file__).parent.parent.absolute()
            dload_path = os.path.join(dload_path, 'media')
            if self.challenge_type == 'by_sms':
                challenge_type = "sms"
            else:
                challenge_type = "email"
            url = login_url()
            payload = {
                'client_id': 'c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS',
                'expires_in': expiresIn,
                'grant_type': 'password',
                'password': self.passwd,
                'scope': scope,
                'username': self.email_id,
                'challenge_type': challenge_type,
                'device_token': device_token
            }
            data = helper.request_post(url, payload)
            if data:
                if 'mfa_required' in data:
                    #mfa_token = input("Please type in the MFA code: ")
                    payload['mfa_code'] = self.mfa_token
                    res = helper.request_post(url, payload, jsonify_data=False)
                    if res.status_code != 200:
                        mfa_token = input(
                            "That MFA code was not correct. Please type in another MFA code: ")
                        payload['mfa_code'] = mfa_token
                        res = helper.request_post(url, payload, jsonify_data=False)
                    data = res.json()
                elif 'challenge' in data:
                    with open(self.challenge_answer_file, 'w') as ans_file:
                        ans_file.write('')
                    challenge_id = data['challenge']['id']
                    #sms_code = input('Enter Robinhood code for validation: ')
                    attempts = 0
                    while attempts < 5:
                        print(f'{datetime.datetime.now()} file {self.challenge_answer_file} attempt {str(attempts)}')
                        if os.path.exists(self.challenge_answer_file):
                            with open(self.challenge_answer_file) as ans_file:
                                sms_code = ans_file.read()
                                if sms_code and sms_code != '':
                                    break
                        attempts += 1
                        time.sleep(12)
                    if not os.path.exists(self.challenge_answer_file):
                        raise Exception('challenge answer file %s not found' %self.challenge_answer_file)
                    sms_code = None
                    with open(self.challenge_answer_file) as ans_file:
                        sms_code = ans_file.read()
                    if not sms_code or sms_code == '':
                        raise Exception('challenge answer file %s empty' %self.challenge_answer_file)

                    res = respond_to_challenge(challenge_id, sms_code)
                    
                    if 'challenge' in res:
                        raise Exception('challenge code not correct')
                    helper.update_session(
                        'X-ROBINHOOD-CHALLENGE-RESPONSE-ID', challenge_id)
                    data = helper.request_post(url, payload)
                # Update Session data with authorization or raise exception with the information present in data.
                if 'access_token' in data:
                    token = '{0} {1}'.format(data['token_type'], data['access_token'])
                    helper.update_session('Authorization', token)
                    helper.set_login_state(True)
                    data['detail'] = "logged in with brand new authentication code."

                else:
                    raise Exception(data['detail'])
            else:
                raise Exception('Error: Trouble connecting to robinhood API. Check internet connection.')
            self.logged_in = True

            return(data)
        return self.login_info
    
    def logout(self):
        if self.logged_in:
            logout()
    
    #"2021-03-08T19:48:32.059256Z"
    def get_date_from_string(self, st):
        dt = get_date_or_none_from_string(st[0:10])
        return dt


    def get_orders(self):
        if self.logged_in:
            ret = dict()
            order_list = get_all_stock_orders()
            for order in order_list:
                ot = get_symbol_by_url(order['instrument'])
                if order['state'] == 'filled':
                    try:
                        if ot not in ret:
                            ret[ot] = list()
                        o = dict()
                        o['type'] = order['side']
                        o['date'] = self.get_date_from_string(order['last_transaction_at'])
                        o['quantity'] = get_float_or_none_from_string(order['cumulative_quantity'])
                        o['div_reinv'] = False
                        if 'drip_dividend_id' in order:
                            o['div_reinv'] = True if order['drip_dividend_id'] else False
                        o['price'] = get_float_or_none_from_string(order['average_price'])
                        o['conv_price'] = get_in_preferred_currency(1, 'USD', o['date'])
                        o['trans_price'] = o['quantity'] * o['price'] * o['conv_price']
                        ret[ot].append(o)
                    except Exception as ex:
                        print(f'Exception parsing order {order}: {ex}')
            return ret
        else:
            raise Exception('not logged in')
