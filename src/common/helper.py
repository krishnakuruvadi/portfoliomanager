from mftool import Mftool
import datetime
from common.models import MutualFund


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