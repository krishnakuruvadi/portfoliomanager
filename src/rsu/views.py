from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import (
    DetailView,
    ListView
)
from .models import RSUAward, RestrictedStockUnits, RSUSellTransactions
from .rsu_helper import update_latest_vals, get_rsu_award_latest_vals
from django.http import HttpResponseRedirect
from shared.handle_get import *
from django.shortcuts import redirect
from shared.utils import *
from rest_framework.views import APIView
from rest_framework.response import Response
from tasks.tasks import update_rsu
from shared.handle_real_time_data import get_conversion_rate, get_historical_stock_price_based_on_symbol, get_in_preferred_currency
import random
from tools.stock_reconcile import Trans, reconcile_event_based
from common.index_helpers import get_comp_index_values
from common.models import Stock
from common.helper import get_currency_symbol, get_preferred_currency_symbol

def create_rsu(request):
    template = "rsus/rsu_create.html"
    message = ''
    message_color = 'ignore'
    if request.method == 'POST':
        print(request.POST)
        #'award_date': ['2019-06-05'], 'exchange': ['NASDAQ'], 'symbol': ['CSCO'], 'award_id': ['1434877'], 'user': ['1'], 'goal': ['2'], 'shares_awarded': ['279']
        
        award_date = get_date_or_none_from_string(request.POST.get('award_date'))
        award_id = request.POST.get('award_id')
        exchange = request.POST.get('exchange')
        symbol = request.POST.get('symbol')
        user = request.POST.get('user')
        goal = get_int_or_none_from_string(request.POST.get('goal'))
        shares_awarded = get_int_or_none_from_string(request.POST.get('shares_awarded'))
        RSUAward.objects.create(
            award_date=award_date,
            award_id=award_id,
            user=user,
            exchange=exchange,
            symbol=symbol,
            goal=goal,
            shares_awarded=shares_awarded
        )
        message_color = 'green'
        message = 'New RSU award addition successful'
    users = get_all_users()
    context = {'users':users, 'operation': 'Add RSU Award', 'curr_module_id': 'id_rsu_module', 'message':message, 'message_color':message_color}
    return render(request, template, context)


def view_update_rsu(request, id):
    template = "rsus/rsu_update.html"
    obj = RSUAward.objects.get(id=id)

    if request.method == 'POST':
        award_date = get_date_or_none_from_string(request.POST.get('award_date'))
        award_id = request.POST.get('award_id')
        goal = get_int_or_none_from_string(request.POST.get('goal'))
        shares_awarded = get_int_or_none_from_string(request.POST.get('shares_awarded'))

        obj.award_date=award_date
        obj.award_id=award_id
        obj.shares_awarded = shares_awarded
        obj.goal = goal
        obj.save()
        return HttpResponseRedirect(reverse('rsus:rsu-list'))

    context = {
        'id':obj.id,
        'symbol':obj.symbol,
        'exchange':obj.exchange,
        'award_date':obj.award_date.strftime("%Y-%m-%d"), 
        'award_id': obj.award_id, 
        'goal':obj.goal, 
        'shares_awarded':obj.shares_awarded,
        'user':obj.user,
        'curr_module_id': 'id_rsu_module'
        }
    print(context)
    return render(request, template, context)

class RsuListView(ListView):
    template_name = 'rsus/rsu_list.html'
    queryset = RSUAward.objects.all() # <blog>/<modelname>_list.html
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
        data['user_name_mapping'] = get_all_users()
        data['award_latest_vals'] = get_rsu_award_latest_vals()
        data['curr_module_id'] = 'id_rsu_module'
        today = datetime.date.today()
        aq_price = 0
        aq_price_incl_tax = 0
        unrealised_gain = 0
        realised_gain = 0
        latest_value = 0
        current_aq_price = 0
        tax_at_vest = 0
        current_tax_at_vest = 0
        current_aq_price_excl_tax = 0
        as_on_date = None
        for rsu in RestrictedStockUnits.objects.all():
            aq_price_excl_tax = float(rsu.shares_for_sale*rsu.aquisition_price*rsu.conversion_rate)
            aq_price += aq_price_excl_tax
            aq_price_incl_tax += float(rsu.total_aquisition_price)
            unrealised_gain += float(rsu.unrealised_gain)
            realised_gain += float(rsu.realised_gain)
            latest_value += float(rsu.latest_value)
            tax_at_vest += float(rsu.tax_at_vest)
            if rsu.unsold_shares > 0:
                current_aq_price_excl_tax += float(rsu.unsold_shares*rsu.aquisition_price*rsu.conversion_rate)
            current_aq_price += float(rsu.total_aquisition_price)
            current_tax_at_vest += float(rsu.tax_at_vest*rsu.unsold_shares/rsu.shares_for_sale)
            as_on_date = get_max(as_on_date, rsu.as_on_date)
        data['aq_price'] = round(aq_price, 2)
        data['aq_price_incl_tax'] = round(aq_price_incl_tax, 2)
        data['realised_gain'] = round(realised_gain, 2)
        data['unrealised_gain'] = round(unrealised_gain, 2)
        data['latest_value'] = round(latest_value, 2)
        data['current_aq_price'] = round(current_aq_price, 2)
        data['tax_at_vest'] = round(tax_at_vest, 2)
        data['current_aq_price_excl_tax'] = round(current_aq_price_excl_tax, 2)
        data['current_tax_at_vest'] = round(current_tax_at_vest, 2)
        data['preferred_currency'] = get_preferred_currency_symbol()
        data['as_on_date'] = get_min(as_on_date, today)
        print(data)
        return data

def delete_award(request, id):
    try:
        a = RSUAward.objects.get(id=id)
        a.delete()
    except RSUAward.DoesNotExist:
        print(f'RSUAward with id {id} does not exist')
    return HttpResponseRedirect(reverse('rsus:rsu-list'))

class RsuDetailView(DetailView):
    template_name = 'rsus/rsu_detail.html'

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(RSUAward, id=id_)
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        award = data['object']
        data['goal_str'] = get_goal_name_from_id(award.goal)
        data['user_str'] = get_user_name_from_id(award.user)
        data['curr_module_id'] = 'id_rsu_module'
        total_aquisition_price = 0
        unsold_shares = 0
        latest_conversion_rate = 0
        latest_price = 0
        latest_value = 0
        as_on_date = None
        realised_gain = 0
        unrealised_gain = 0
        tax_at_vest = 0
        shares_for_sale = 0
        unvested_shares = 0
        vested_shares = 0
        for rsu in RestrictedStockUnits.objects.filter(award=award):
            total_aquisition_price += rsu.total_aquisition_price
            unsold_shares += rsu.unsold_shares
            latest_value += rsu.latest_value
            if not as_on_date or as_on_date < rsu.as_on_date:
                as_on_date = rsu.as_on_date
                latest_price = rsu.latest_price
                latest_conversion_rate = rsu.latest_conversion_rate
            realised_gain += rsu.realised_gain
            unrealised_gain += rsu.unrealised_gain
            tax_at_vest += rsu.tax_at_vest
            shares_for_sale += rsu.shares_for_sale
            vested_shares += rsu.shares_vested
        unvested_shares = data['object'].shares_awarded - vested_shares
        data['total_aquisition_price'] = total_aquisition_price
        data['unsold_shares'] = unsold_shares
        data['latest_conversion_rate'] = latest_conversion_rate
        data['latest_price'] = latest_price
        data['latest_value'] = latest_value
        data['as_on_date'] = as_on_date
        data['realised_gain'] = realised_gain
        data['unrealised_gain'] = unrealised_gain
        data['tax_at_vest'] = tax_at_vest
        data['shares_for_sale'] = shares_for_sale
        data['unvested_shares'] = unvested_shares
        data['vested_shares'] = vested_shares
        if data['object'].exchange in ['NSE', 'BSE']:
            data['currency'] = get_currency_symbol('INR')
        elif data['object'].exchange in ['NYSE', 'NASDAQ']:
            data['currency'] = get_currency_symbol('USD')
        data['preferred_currency'] = get_preferred_currency_symbol()

        today = datetime.date.today()
        r = lambda: random.randint(0,255)
        color = '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
        color2 = '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
        color3 = '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
        ret = list()
        ret.append({
            'label':'Value',
            'data': list(),
            'fill': 'false',
            'borderColor':color
        })
        ret.append({
            'label':'Aquisition Price (excluding tax)',
            'data': list(),
            'fill': 'false',
            'borderColor':color2
        })
        ret.append({
            'label':'Aquisition Price (including tax)',
            'data': list(),
            'fill': 'false',
            'borderColor':color3
        })
        #from award date to today or until unsold shares are available
        st_dt = award.award_date.replace(day=1)
        unsold_shares = award.shares_awarded
        trans = list()
        aq_price = 0
        aq_price_incl_tax = 0
        while st_dt <= today and unsold_shares > 0:
            end_dt = st_dt + relativedelta(months=1)
            if end_dt > today:
                end_dt = today
            print(f'end_dt: {end_dt}')
            for rsu in RestrictedStockUnits.objects.filter(award=data['object'], vest_date__lte=end_dt).order_by('vest_date'):
                if rsu.vest_date >= st_dt and rsu.vest_date <= end_dt:
                    trans.append(Trans(rsu.shares_for_sale, rsu.vest_date, 'buy', rsu.shares_for_sale*rsu.aquisition_price*rsu.conversion_rate))
                    aq_price += float(rsu.shares_for_sale*rsu.aquisition_price*rsu.conversion_rate)
                    aq_price_incl_tax += float(rsu.total_aquisition_price)
                for st in RSUSellTransactions.objects.filter(rsu_vest=rsu, trans_date__gte=st_dt, trans_date__lte=end_dt):
                    trans.append(Trans(st.units, st.trans_date, 'sell', st.trans_price))
                    unsold_shares -= st.units
                    aq_price -= float(st.units*rsu.aquisition_price*rsu.conversion_rate)
                    aq_price_incl_tax -= float(st.units*rsu.aquisition_price*rsu.conversion_rate)
            q, _,_,_,_ = reconcile_event_based(trans, list(), list())
            if q > 0:
                lv = get_historical_stock_price_based_on_symbol(award.symbol, award.exchange, end_dt+relativedelta(days=-5), end_dt)
                val = 0
                if lv:
                    print(lv)
                    conv_rate = 1
                    if award.exchange in ['NASDAQ', 'NYSE']:
                        conv_val = get_in_preferred_currency(1, 'USD', end_dt)
                        if conv_val:
                            conv_rate = conv_val
                    elif award.exchange in ['NSE', 'BSE', 'NSE/BSE']:
                        conv_val = get_in_preferred_currency(1, 'INR', end_dt)
                        if conv_val:
                            conv_rate = conv_val
                    for k,v in lv.items():
                        val += float(v)*float(conv_rate)*float(q)
                        break
                else:
                    print(f'failed to get value of {rsu.award.exchange}:{rsu.award.symbol} on {end_dt}')
                if val > 0:
                    x = end_dt.strftime('%Y-%m-%d')
                    ret[0]['data'].append({'x': x, 'y':round(val,2)})
                    ret[1]['data'].append({'x': x, 'y':round(aq_price,2)})
                    ret[2]['data'].append({'x': x, 'y':round(aq_price_incl_tax,2)})
            st_dt = st_dt + relativedelta(months=1)
        
        data['progress_data'] = ret
        try:
            s = Stock.objects.get(symbol=award.symbol, exchange=award.exchange)
            if st_dt > today:
                st_dt = datetime.date.today()
            res = get_comp_index_values(s, award.award_date.replace(day=1), st_dt)
            if 'chart_labels' in res and len(res['chart_labels']) > 0:
                for k, v in res.items():
                    data[k] = v 
        except Stock.DoesNotExist:
            print(f'trying to get stock that does not exist {award.symbol} {award.exchange}')
        print(f'returning data {data}')
        return data

class RsuVestDetailView(DetailView):
    template_name = 'rsus/rsu_vest_detail.html'

    def get_object(self):
        id_ = self.kwargs.get("vestid")
        return get_object_or_404(RestrictedStockUnits, id=id_)
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        rsu = data['object']
        data['sell_trans'] = RSUSellTransactions.objects.filter(rsu_vest=rsu)
        data['curr_module_id'] = 'id_rsu_module'
        std = rsu.vest_date
        today = datetime.date.today()
        r = lambda: random.randint(0,255)
        color = '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
        ret = list()
        ret.append({
            'label':'',
            'data': list(),
            'fill': 'false',
            'borderColor':color
        })
        ret[0]['data'].append({'x': rsu.vest_date.strftime('%Y-%m-%d'), 'y':round(float(rsu.shares_for_sale*rsu.aquisition_price*rsu.conversion_rate),2)})

        std = std+relativedelta(months=1)
        if std > today:
            std = today
        else:
            std = std.replace(day=1)
            
        while True:
            val = 0
            trans = list()
            trans.append(Trans(rsu.shares_for_sale, rsu.vest_date, 'buy', rsu.shares_for_sale*rsu.aquisition_price*rsu.conversion_rate))
            for st in RSUSellTransactions.objects.filter(rsu_vest=rsu, trans_date__lte=std):
                trans.append(Trans(st.units, st.trans_date, 'sell', st.trans_price))
            q, _,_,_,_ = reconcile_event_based(trans, list(), list())
            lv = get_historical_stock_price_based_on_symbol(rsu.award.symbol, rsu.award.exchange, std+relativedelta(days=-5), std)
            if lv:
                print(lv)
                conv_rate = 1
                if rsu.award.exchange in ['NASDAQ', 'NYSE']:
                    conv_val = get_in_preferred_currency(1, 'USD', std)
                    if conv_val:
                        conv_rate = conv_val
                elif rsu.award.exchange in ['NSE', 'BSE', 'NSE/BSE']:
                    conv_val = get_in_preferred_currency(1, 'INR', std)
                    if conv_val:
                        conv_rate = conv_val
                for k,v in lv.items():
                    val += float(v)*float(conv_rate)*float(q)
                    break
            else:
                print(f'failed to get value of {rsu.award.exchange}:{rsu.award.symbol} on {std}')
            if val > 0:
                x = std.strftime('%Y-%m-%d')
                ret[0]['data'].append({'x': x, 'y':round(val,2)})
            if std == today:
                break   
            std = std+relativedelta(months=1)
            if std > today:
                std = today
        data['progress_data'] = ret
        try:
            s = Stock.objects.get(symbol=rsu.award.symbol, exchange=rsu.award.exchange)
            last_date = datetime.date.today()
            if rsu.unsold_shares == 0:
                all_sell = RSUSellTransactions.objects.filter(rsu_vest=rsu).order_by('trans_date')
                last_date = all_sell[len(all_sell)-1].trans_date

            res = get_comp_index_values(s, rsu.vest_date, last_date)
            if 'chart_labels' in res and len(res['chart_labels']) > 0:
                for k, v in res.items():
                    data[k] = v 
        except Stock.DoesNotExist:
            print(f'trying to get stock that does not exist {rsu.award.symbol} {rsu.award.exchange}')
        return data

def refresh_rsu_trans(request):
    template = '../../rsu/'
    for rsu_award in RSUAward.objects.all():
        for rsu_obj in RestrictedStockUnits.objects.filter(award=rsu_award):
            print("looping through rsu " + str(rsu_obj.id))
            update_latest_vals(rsu_obj)
    return HttpResponseRedirect(template)

def refresh_rsu_vest_trans(request, id):
    template = '../'
    try:
        rsu_award = RSUAward.objects.get(id=id)
        for rsu_obj in RestrictedStockUnits.objects.filter(award=rsu_award):
            print("looping through rsu " + str(rsu_obj.id))
            update_latest_vals(rsu_obj)
    except RSUAward.DoesNotExist:
        print("RSUAward object with id ", id, " does not exist")
    return HttpResponseRedirect(template)

def show_vest_list(request,id):
    template = 'rsus/rsu_vest_list.html'
    rsu_award = get_object_or_404(RSUAward, id=id)
    
    rsu_objs = RestrictedStockUnits.objects.filter(award=rsu_award)
    vest_list = list()
    for rsu_obj in rsu_objs:
        entry = dict()
        entry['id'] = rsu_obj.id
        entry['vest_date'] = rsu_obj.vest_date
        entry['fmv'] = rsu_obj.fmv
        entry['aquisition_price'] = rsu_obj.aquisition_price
        entry['shares_vested'] = rsu_obj.shares_vested
        entry['shares_for_sale'] = rsu_obj.shares_for_sale
        entry['total_aquisition_price'] = rsu_obj.total_aquisition_price
        entry['latest_conversion_rate'] = rsu_obj.latest_conversion_rate
        entry['latest_price'] = rsu_obj.latest_price
        entry['latest_value'] = rsu_obj.latest_value
        entry['as_on_date'] = rsu_obj.as_on_date
        entry['realised_gain'] = rsu_obj.realised_gain
        entry['unrealised_gain'] = rsu_obj.unrealised_gain
        entry['notes'] = rsu_obj.notes
        entry['unsold_shares'] = rsu_obj.unsold_shares
        vest_list.append(entry)
     
    context = {'vest_list':vest_list, 'award_id':rsu_award.award_id, 'symbol':rsu_award.symbol, 'award_date':rsu_award.award_date, 'id':rsu_award.id}
    context['curr_module_id'] = 'id_rsu_module'
    return render(request, template, context)

def show_vest_sell_trans(request, id, vestid):
    template = 'rsus/rsu_vest_sell_trans.html'
    print(f'id {id} vest_id {vestid}')
    try:
        rsu_vest = RestrictedStockUnits.objects.get(id=vestid)
        vest_sell_list = list()
        for st in RSUSellTransactions.objects.filter(rsu_vest=rsu_vest):
            vs = {
                'id':st.id,
                'sell_date':st.trans_date,
                'units':st.units,
                'sell_price':st.price,
                'sell_conversion_rate':st.conversion_rate,
                'total_sell_price':st.trans_price,
                'realised_gain':st.realised_gain,
                'notes':st.notes
            }
            vest_sell_list.append(vs)
        context = {'vest_sell_list':vest_sell_list, 'vest_date':rsu_vest.vest_date, 'award_date':rsu_vest.award.award_date, 'symbol':rsu_vest.award.symbol, 'award_id':rsu_vest.award.award_id}
        context['curr_module_id'] = 'id_rsu_module'
        return render(request, template, context)
    except Exception as ex:
        print(f'exception getting sell transactions  {ex}')
        return HttpResponseRedirect(reverse('rsus:rsu-list'))

def delete_vest_sell_trans(request, id, vestid, selltransid):
    try:
        award_obj = RSUAward.objects.get(id)
        try:
            vest = RestrictedStockUnits.objects.get(award=award_obj, id=vestid)
            try:
                trans = RSUSellTransactions.objects.get(rsu_vest=vest, id=selltransid)
                trans.delete()
                update_rsu()
            except RSUSellTransactions.DoesNotExist:
                print(f'{selltransid} RSUSellTransaction does not exist')
            return HttpResponseRedirect(reverse('rsus:rsu-sell-vest',kwargs={'id':id,'vestid':vestid}))
        except RestrictedStockUnits.DoesNotExist:
            print(f'{vestid} RestrictedStockUnits does not exist')
        return HttpResponseRedirect(reverse('rsus:rsu-vest-list',kwargs={'id':id}))
    except RSUAward.DoesNotExist:
        print(f'{id} RSUAward does not exist')
        return HttpResponseRedirect(reverse('rsus:rsu-list'))

def delete_vest(request, id, vestid):
    try:
        award_obj = RSUAward.objects.get(id)
        try:
            vest = RestrictedStockUnits.objects.get(award=award_obj, id=vestid)
            vest.delete()
            update_rsu()
        except RestrictedStockUnits.DoesNotExist:
            print(f'{vestid} RestrictedStockUnits does not exist')
        return HttpResponseRedirect(reverse('rsus:rsu-vest-list',kwargs={'id':id}))
    except RSUAward.DoesNotExist:
        print(f'{id} RSUAward does not exist')
        return HttpResponseRedirect(reverse('rsus:rsu-list'))

def add_vest_sell_trans(request, id, vestid):
    template = 'rsus/rsu_add_sell_trans.html'
    print(f'id {id} vest_id {vestid}')
    try:
        award_obj = get_object_or_404(RSUAward, id=id)
        rsu_vest = RestrictedStockUnits.objects.get(id=vestid)

        if request.method == 'POST':
            sell_date = get_date_or_none_from_string(request.POST.get('sell_date'))
            units = get_float_or_none_from_string(request.POST.get('units'))
            sell_price = get_float_or_none_from_string(request.POST.get('sell_price'))
            sell_conv_rate = get_float_or_none_from_string(request.POST.get('sell_conversion_rate'))
            total_sell_price = get_float_or_none_from_string(request.POST.get('total_sell_price'))
            notes = request.POST.get('notes')
            st = RSUSellTransactions.objects.create(
                rsu_vest=rsu_vest,
                trans_date=sell_date,
                price=sell_price,
                units=units,
                conversion_rate=sell_conv_rate,
                trans_price=total_sell_price,
                notes=notes
            )
            st.realised_gain = float(st.trans_price) - float(rsu_vest.aquisition_price)*float(st.units)*float(rsu_vest.conversion_rate)
            st.save()
            update_rsu()
            return HttpResponseRedirect(reverse('rsus:rsu-sell-vest',kwargs={'id':id,'vestid':vestid}))
        else:
            context = {'award_date':award_obj.award_date, 'symbol':award_obj.symbol, 'award_id':award_obj.award_id,
             'vest_date':rsu_vest.vest_date, 'unsold_shares':rsu_vest.unsold_shares, 'aquisition_price':rsu_vest.aquisition_price, 'exchange':award_obj.exchange}
            context['curr_module_id'] = 'id_rsu_module'
            return render(request, template, context)
    except Exception as ex:
        print(f'exception adding sell transaction {ex}')
        return HttpResponseRedirect(reverse('rsus:rsu-list'))


def add_vest(request,id):
    template = 'rsus/rsu_add_vest.html'
    award_obj = get_object_or_404(RSUAward, id=id)
    
    if request.method == 'POST':
        print(request.POST)
        if "submit" in request.POST:
            vest_date = get_datetime_or_none_from_string(request.POST.get('vest_date'))
            fmv = get_float_or_none_from_string(request.POST.get('fmv'))
            aquisition_price = get_float_or_none_from_string(request.POST.get('aquisition_price'))
            shares_vested = get_int_or_none_from_string(request.POST.get('shares_vested'))
            shares_for_sale = get_int_or_none_from_string(request.POST.get('shares_for_sale'))
            total_aquisition_price = get_float_or_none_from_string(request.POST.get('total_aquisition_price'))
            conversion_rate = get_float_or_none_from_string(request.POST.get('conversion_rate'))
            notes = request.POST.get('notes')
            rsu = RestrictedStockUnits.objects.create(award=award_obj,
                                                      vest_date=vest_date,
                                                      fmv=fmv,
                                                      aquisition_price=aquisition_price,
                                                      shares_vested=shares_vested,
                                                      shares_for_sale=shares_for_sale,
                                                      unsold_shares=shares_for_sale,
                                                      total_aquisition_price=total_aquisition_price,
                                                      conversion_rate=conversion_rate,
                                                      notes=notes)
            rsu.save()
            update_rsu()
            return redirect('rsus:rsu-vest-list', id=id)

    context = {'award_id':award_obj.award_id, 'exchange':award_obj.exchange, 'symbol':award_obj.symbol, 'award_date':award_obj.award_date}
    context['curr_module_id'] = 'id_rsu_module'
    return render(request, template, context)

def update_vest(request,id,vestid):
    template = 'rsus/rsu_add_vest.html'
    award_obj = get_object_or_404(RSUAward, id=id)
    rsu_obj = get_object_or_404(RestrictedStockUnits, id=vestid)
    
    if request.method == 'POST':
        print(request.POST)
        if "submit" in request.POST:
            rsu_obj.vest_date = get_datetime_or_none_from_string(request.POST.get('vest_date'))
            rsu_obj.fmv = get_float_or_none_from_string(request.POST.get('fmv'))
            rsu_obj.aquisition_price = get_float_or_none_from_string(request.POST.get('aquisition_price'))
            rsu_obj.shares_vested = get_int_or_none_from_string(request.POST.get('shares_vested'))
            rsu_obj.shares_for_sale = get_int_or_none_from_string(request.POST.get('shares_for_sale'))
            rsu_obj.conversion_rate = get_float_or_none_from_string(request.POST.get('conversion_rate'))
            rsu_obj.total_aquisition_price = get_float_or_none_from_string(request.POST.get('total_aquisition_price'))
            rsu_obj.notes = request.POST.get('notes')
            rsu_obj.unsold_shares = rsu_obj.shares_for_sale
            rsu_obj.save()
            update_rsu()
            return redirect('rsus:rsu-vest-list', id=id)
    else:
        context = {'award_id':award_obj.award_id, 'exchange':award_obj.exchange, 'symbol':award_obj.symbol, 'award_date':award_obj.award_date}
        context['vest_date'] = convert_date_to_string(rsu_obj.vest_date)
        context['fmv'] = rsu_obj.fmv
        context['aquisition_price'] = rsu_obj.aquisition_price
        context['shares_vested'] = rsu_obj.shares_vested
        context['shares_for_sale'] = rsu_obj.shares_for_sale
        context['total_aquisition_price'] = rsu_obj.total_aquisition_price
        context['conversion_rate'] = rsu_obj.conversion_rate
        context['notes'] = rsu_obj.notes
        context['curr_module_id'] = 'id_rsu_module'
        print(context)
        return render(request, template, context)

    context = {'award_id':award_obj.award_id, 'exchange':award_obj.exchange, 'symbol':award_obj.symbol, 'award_date':award_obj.award_date}
    context['curr_module_id'] = 'id_rsu_module'
    return render(request, template, context)

class CurrentRsus(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, user_id=None):
        print("inside CurrentRsus")
        rsus = dict()
        total = 0
        if user_id:
            rsu_objs = RestrictedStockUnits.objects.filter(sell_date__isnull=True).filter(award__user=user_id)
        else:
            rsu_objs = RestrictedStockUnits.objects.filter(sell_date__isnull=True)
        for rsu in rsu_objs:
            key = rsu.award.symbol+rsu.award.exchange+str(rsu.award.user)
            if key in rsus:
                rsus[key]['shares_for_sale'] += rsu.shares_for_sale
                if rsu.latest_value:
                    rsus[key]['latest_value'] += rsu.latest_value

            else:
                rsus[key] = dict()
                rsus[key]['exchange'] = rsu.award.exchange
                rsus[key]['symbol'] = rsu.award.symbol
                rsus[key]['user_id'] = rsu.award.user
                rsus[key]['user'] = get_user_name_from_id(rsu.award.user)
                rsus[key]['shares_for_sale'] = rsu.shares_for_sale
                if rsu.latest_value:
                    rsus[key]['latest_value'] = rsu.latest_value
            if rsu.as_on_date:
                rsus[key]['as_on_date'] = rsu.as_on_date

        data = dict()
        data['entry'] = list()
        for _,v in rsus.items():
            data['entry'].append(v)
        data['total'] = total    
        return Response(data)


def rsu_insights(request):
    template = 'rsus/rsu_insights.html'
    ret = list()
    today = datetime.date.today()
    total = dict()
    
    for i, award in enumerate(RSUAward.objects.all()):
        rsus = RestrictedStockUnits.objects.filter(award=award)
        if len(rsus) > 0:
            std = award.award_date
            r = lambda: random.randint(0,255)
            color = '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
            ret.append({
                'label':str(award.award_id),
                'data': list(),
                'fill': 'false',
                'borderColor':color
            })
            std = std.replace(day=1)
            reset_to_zero = False
            while True:
                val = 0
                for rsu in RestrictedStockUnits.objects.filter(award=award, vest_date__lte=std):
                    trans = list()
                    trans.append(Trans(rsu.shares_for_sale, rsu.vest_date, 'buy', rsu.shares_for_sale*rsu.aquisition_price))
                    for st in RSUSellTransactions.objects.filter(rsu_vest=rsu, trans_date__lte=std):
                        trans.append(Trans(st.units, st.trans_date, 'sell', st.trans_price))
                    q, _,_,_,_ = reconcile_event_based(trans, list(), list())
                    lv = get_historical_stock_price_based_on_symbol(award.symbol, award.exchange, std+relativedelta(days=-5), std)
                    if lv:
                        print(lv)
                        conv_rate = 1
                        if award.exchange in ['NASDAQ', 'NYSE']:
                            conv_val = get_in_preferred_currency(1, 'USD', std)
                            if conv_val:
                                conv_rate = conv_val
                        elif award.exchange in ['NSE', 'BSE', 'NSE/BSE']:
                            conv_val = get_in_preferred_currency(1, 'INR', std)
                            if conv_val:
                                conv_rate = conv_val
                        for k,v in lv.items():
                            val += float(v)*float(conv_rate)*float(q)
                            break
                    else:
                        print(f'failed to get value of {award.award_id} {award.exchange}:{award.symbol} on {std}')
                if val > 0:
                    x = std.strftime('%Y-%m-%d')
                    ret[i]['data'].append({'x': x, 'y':round(val,2)})
                    total[x] = total.get(x, 0) + round(val,2)
                    reset_to_zero = True
                elif reset_to_zero:
                    x = std.strftime('%Y-%m-%d')
                    ret[i]['data'].append({'x': x, 'y':0})
                    reset_to_zero = False
                    total[x] = total.get(x, 0)
                if std == today:
                    break
                std = std+relativedelta(months=1)
                if std > today:
                    std = today
    print(ret)
    if len(ret) > 0:
        d = list()
        for k,v in sorted(total.items()):
            d.append({'x':k, 'y':round(v, 2)})
        r = lambda: random.randint(0,255)
        color = '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
        ret.append({
                    'label':'total',
                    'data': d,
                    'fill': 'false',
                    'borderColor':color
                })
    context = dict()
    context['progress_data'] = ret
    return render(request, template, context)

