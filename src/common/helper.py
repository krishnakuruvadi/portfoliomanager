from mftool import Mftool
import datetime
from common.models import MutualFund, MFCategoryReturns
from shared.utils import get_float_or_none_from_string

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
        '''
        try:
            HistoricalMFPrice.objects.create(code=mf_obj,
                                             date=datetime.datetime.strptime(details['date'],'%d-%b-%Y').date(),
                                             nav=float(details['nav']))
        except Exception as ex:
            print(ex)
        '''
    '''
    mf_objs = MutualFund.objects.all()
    for mf in mf_objs:
        collection_start_date = datetime.date.today()+relativedelta(days=-5)       
        _ = get_historical_mf_nav(mf.code, collection_start_date, datetime.date.today())
    '''
    if added or changed:
        print('Addition to schemes:', added,'. Changed scheme details:', changed)
    else:
        print('No addition or changes detected in mutual fund schemes')

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
    for scheme_data in data:
        if ";INF" in scheme_data:
            scheme = scheme_data.rstrip().split(";")
            #print(scheme[1],', ',scheme[2])
            scheme_info[scheme[0]] = {'isin1': scheme[1],
                                      'isin2':scheme[2],
                                      'name':scheme[3],
                                      'nav':scheme[4],
                                      'date':scheme[5]}

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
