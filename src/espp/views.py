from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import (
    CreateView,
    ListView,
    DetailView,
    UpdateView
)

from shared.utils import get_date_or_none_from_string, get_float_or_none_from_string
from .models import Espp, EsppSellTransactions
from .espp_helper import update_latest_vals
from django.http import HttpResponseRedirect
from shared.handle_get import *
from shared.handle_create import add_common_stock
from rest_framework.views import APIView
from rest_framework.response import Response
from shared.financial import xirr
from django.db import IntegrityError
import random
from tools.stock_reconcile import Trans, reconcile_event_based
from shared.handle_real_time_data import get_conversion_rate, get_historical_stock_price_based_on_symbol, get_in_preferred_currency
from dateutil.relativedelta import relativedelta
from common.index_helpers import get_comp_index_values
from common.models import Stock
from common.helper import get_preferred_currency_symbol
from decimal import Decimal
from goal.goal_helper import get_goal_id_name_mapping_for_user


def add_espp(request):
    template = 'espps/espp_create.html'
    message = ''
    message_color = 'ignore'
    if request.method == 'POST':
        try:
            purchase_date = request.POST['purchase_date']
            user = request.POST['user']
            goal = request.POST.get('goal', '')
            if goal != '':
                goal_id = Decimal(goal)
            else:
                goal_id = None
            #notes = request.POST['notes']
            purchase_price = Decimal(request.POST['purchase_price'])
            shares_purchased = Decimal(request.POST['shares_purchased'])
            purchase_conversion_rate = Decimal(request.POST['purchase_conversion_rate'])
            exchange = request.POST['exchange']
            symbol = request.POST['symbol']
            total_purchase_price = float(purchase_price*shares_purchased*purchase_conversion_rate)
            shares_avail_for_sale = shares_purchased
            purchase_fmv = Decimal(request.POST['purchase_fmv'])
            subscription_fmv = Decimal(request.POST['subscription_fmv'])
            
            Espp.objects.create(
                exchange=exchange,
                symbol=symbol,
                purchase_date=purchase_date,
                shares_avail_for_sale=shares_avail_for_sale,
                total_purchase_price=total_purchase_price,
                subscription_fmv=subscription_fmv,
                purchase_fmv=purchase_fmv,
                purchase_price=purchase_price,
                shares_purchased=shares_purchased,
                purchase_conversion_rate=purchase_conversion_rate,
                user=user,
                goal=goal_id
            )
            add_common_stock(exchange, symbol, purchase_date)
            message_color = 'green'
            message = 'New ESPP addition successful'
        except Exception as ex:
            print(f'exception {ex} when adding ESPP')
            message_color = 'red'
            message = 'New ESPP addition failed'
    users = get_all_users()
    context = {'users':users, 'operation': 'Add ESPP', 'curr_module_id': 'id_espp_module', 'message':message, 'message_color':message_color}
    return render(request, template, context)

class EsppListView(ListView):
    template_name = 'espps/espp_list.html'
    queryset = Espp.objects.all() # <blog>/<modelname>_list.html
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
        data['user_name_mapping'] = get_all_users()
        current_investment = 0
        latest_value = 0
        unrealised_gain = 0
        realised_gain = 0
        total_investment = 0
        for obj in self.queryset:
            total_investment += obj.total_purchase_price
            if obj.latest_value:
                latest_value += obj.latest_value
                current_investment += float(obj.shares_avail_for_sale*obj.purchase_price*obj.purchase_conversion_rate)
            unrealised_gain += obj.unrealised_gain
            realised_gain += obj.realised_gain
        data['total_investment'] = total_investment
        data['current_investment'] = round(current_investment, 2)
        data['latest_value'] = latest_value
        data['unrealised_gain'] = unrealised_gain
        data['realised_gain'] = realised_gain
        data['preferred_currency'] = get_preferred_currency_symbol()
        data['curr_module_id'] = 'id_espp_module'
        print(data)
        return data

def delete_espp(request, id):
    try:
        e = Espp.objects.get(id=id)
        e.delete()
    except Espp.DoesNotExist:
        print(f'ESPP with id {id} does not exist')
    return HttpResponseRedirect(reverse('espps:espp-list'))

class EsppDetailView(DetailView):
    template_name = 'espps/espp_detail.html'
    #queryset = Ppf.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Espp, id=id_)
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_str'] = get_goal_name_from_id(data['object'].goal)
        data['user_str'] = get_user_name_from_id(data['object'].user)
        obj = data['object']
        cash_flows = list()
        cash_flows.append((obj.purchase_date, -1*float(obj.total_purchase_price)))
        for st in EsppSellTransactions.objects.filter(espp=data['object']):
            cash_flows.append((st.trans_date, float(st.trans_price)))
        if float(obj.latest_value) > 0:
            cash_flows.append((obj.as_on_date, float(obj.latest_value)))
        roi = xirr(cash_flows, 0.1)*100
        roi = round(roi, 2)
        data['roi'] = roi
        data['curr_module_id'] = 'id_espp_module'
        '''
        data['transactions'] = list()
        for st in EsppSellTransactions.objects.filter(espp=data['object']):
            data['transactions'].append({
                'id':st.id,
                'trans_date':st.trans_date,
                'price':st.price,
                'units':st.units,
                'conversion_rate':st.conversion_rate,
                'trans_price':st.trans_price,
                'realised_gain':st.realised_gain,
                'notes':st.notes
            })
        '''
        std = obj.purchase_date
        today = datetime.date.today()
        r = lambda: random.randint(0,255)
        color = '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
        color2 = '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
        ret = list()
        ret.append({
            'label':'Value',
            'data': list(),
            'fill': 'false',
            'borderColor':color
        })
        ret.append({
            'label':'Investment',
            'data': list(),
            'fill': 'false',
            'borderColor':color2
        })
        tpp = round(float(obj.total_purchase_price),2)
        pfmv = round(float(obj.purchase_fmv*obj.shares_purchased*obj.purchase_conversion_rate),2)
        ret[0]['data'].append({'x': obj.purchase_date.strftime('%Y-%m-%d'), 'y':pfmv})
        ret[1]['data'].append({'x': obj.purchase_date.strftime('%Y-%m-%d'), 'y':tpp})

        std = std+relativedelta(months=1)
        if std > today:
            std = today
        else:
            std = std.replace(day=1)
        reset_to_zero = False
        while True:
            val = 0
            trans = list()
            trans.append(Trans(obj.shares_purchased, obj.purchase_date, 'buy', obj.total_purchase_price))
            for st in EsppSellTransactions.objects.filter(espp=obj, trans_date__lte=std):
                trans.append(Trans(st.units, st.trans_date, 'sell', st.trans_price))
            q, _,_,_,_ = reconcile_event_based(trans, list(), list())
            lv = get_historical_stock_price_based_on_symbol(obj.symbol, obj.exchange, std+relativedelta(days=-5), std)
            if lv:
                print(lv)
                conv_rate = 1
                if obj.exchange in ['NASDAQ', 'NYSE']:
                    conv_val = get_in_preferred_currency(1, 'USD', std)
                    if conv_val:
                        conv_rate = conv_val
                elif obj.exchange in ['NSE', 'BSE', 'NSE/BSE']:
                    conv_val = get_in_preferred_currency(1, 'INR', std)
                    if conv_val:
                        conv_rate = conv_val
                for k,v in lv.items():
                    val += float(v)*float(conv_rate)*float(q)
                    break
            else:
                print(f'failed to get value of {obj.exchange}:{obj.symbol} on {std}')
            if val > 0 or reset_to_zero:
                x = std.strftime('%Y-%m-%d')
                ret[0]['data'].append({'x': x, 'y':round(val,2)})
                ret[1]['data'].append({'x': x, 'y':tpp})
                if val > 0:
                    reset_to_zero = True
                else:
                    reset_to_zero = False
            
            if std == today:
                break   
            std = std+relativedelta(months=1)
            if std > today:
                std = today
        data['progress_data'] = ret
        try:
            s = Stock.objects.get(symbol=obj.symbol, exchange=obj.exchange)
            last_date = datetime.date.today()
            if obj.shares_avail_for_sale == 0:
                all_sell = EsppSellTransactions.objects.filter(espp=obj).order_by('trans_date')
                last_date = all_sell[len(all_sell)-1].trans_date

            res = get_comp_index_values(s, obj.purchase_date, last_date)
            if 'chart_labels' in res and len(res['chart_labels']) > 0:
                for k, v in res.items():
                    data[k] = v 
        except Stock.DoesNotExist:
            print(f'trying to get stock that does not exist {obj.symbol} {obj.exchange}')
        
        return data

def update_espp(request, id):
    template = "espps/espp_update.html"
    context = dict()
    context['curr_module_id'] = 'id_espp_module'
    message = ''
    message_color = 'ignore'
    try:
        espp = Espp.objects.get(id=id)
        if request.method == 'POST':
            try:
                goal = request.POST.get('goal', '')
                if goal != '':
                    goal_id = Decimal(goal)
                else:
                    goal_id = None
                #notes = request.POST['notes']
                purchase_price = Decimal(request.POST['purchase_price'])
                shares_purchased = Decimal(request.POST['shares_purchased'])
                purchase_conversion_rate = Decimal(request.POST['purchase_conversion_rate'])
                total_purchase_price = float(purchase_price*shares_purchased*purchase_conversion_rate)
                shares_avail_for_sale = shares_purchased
                purchase_fmv = Decimal(request.POST['purchase_fmv'])
                subscription_fmv = Decimal(request.POST['subscription_fmv'])

                espp.goal = goal_id
                espp.shares_avail_for_sale = shares_avail_for_sale
                espp.subscription_fmv = subscription_fmv
                espp.purchase_fmv = purchase_fmv
                espp.purchase_price = purchase_price
                espp.shares_purchased = shares_purchased
                espp.purchase_conversion_rate = purchase_conversion_rate
                espp.total_purchase_price = total_purchase_price
                espp.save()
                message = 'ESPP update successful'
                message_color = 'green'
            except Exception as ex:
                print(f'{ex} when updating ESPP {id}')
                message = 'ESPP update failed'
                message_color = 'red'
        context['exchange'] = espp.exchange
        context['symbol'] = espp.symbol
        context['user_str'] = get_user_name_from_id(espp.user)
        context['user'] = espp.user
        context['goal'] = espp.goal
        context['goals'] = {'goal_list':get_goal_id_name_mapping_for_user(espp.user)}
        context['purchase_date'] = espp.purchase_date
        context['shares_avail_for_sale'] = espp.shares_avail_for_sale
        context['subscription_fmv'] = espp.subscription_fmv
        context['purchase_price'] = espp.purchase_price
        context['shares_purchased'] = espp.shares_purchased
        context['purchase_fmv'] = espp.purchase_fmv
        context['purchase_conversion_rate'] = espp.purchase_conversion_rate
        context['total_purchase_price'] = espp.total_purchase_price
        context['users'] = get_all_users()
        context['message'] = message
        context['message_color'] = message_color
        return render(request, template, context)
    except Espp.DoesNotExist:
        print(f"ESPP with id {id} does not exist")
        return HttpResponseRedirect(reverse('espps:espp-list'))

def refresh_espp_trans(request):
    template = '../../espp/'
    for espp_obj in Espp.objects.all():
        print("looping through espp " + str(espp_obj.id))
        update_latest_vals(espp_obj)
    return HttpResponseRedirect(template)

def get_sell_trans(request, id):
    template = "espps/sell_transactions.html"
    context = dict()
    context['espp_id'] = id
    context['transactions'] = list()
    try:
        espp_obj = Espp.objects.get(id=id)
        context['purchase_date'] = espp_obj.purchase_date
        context['symbol'] = espp_obj.symbol
        total_realised_gain = 0
        for st in EsppSellTransactions.objects.filter(espp=espp_obj):
            context['transactions'].append({
                'id':st.id,
                'trans_date':st.trans_date,
                'price':st.price,
                'units':st.units,
                'conversion_rate':st.conversion_rate,
                'trans_price':st.trans_price,
                'realised_gain':st.realised_gain,
                'notes':st.notes
            })
            total_realised_gain += float(st.realised_gain)
        context['total_realised_gain'] = total_realised_gain
        context['curr_module_id'] = 'id_espp_module'
    except Espp.DoesNotExist:
        print(f"ESPP with id {id} does not exist")
    return render(request, template, context)

def delete_sell_trans(request, id):
    try:
        espp_sel_trans = EsppSellTransactions.objects.get(id=id)
        espp_id = espp_sel_trans.espp.id
        espp_sel_trans.delete()
        return HttpResponseRedirect(reverse('espps:espp-sell-trans-list',kwargs={'id':espp_id}))
    except EsppSellTransactions.DoesNotExist:
        print(f'EsppSellTransactions with id {id} does not exist')
        pass
    return HttpResponseRedirect(reverse('espps:espp-list'))

def add_sell_trans(request, id):
    template = "espps/add_sell_transaction.html"
    context = dict()
    context['espp_id'] = id
    context['curr_module_id'] = 'id_espp_module'
    try:
        espp_obj = Espp.objects.get(id=id)
        if request.method == 'POST':
            trans_date = get_date_or_none_from_string(request.POST['trans_date'])
            price = get_float_or_none_from_string(request.POST['price'])
            units = get_float_or_none_from_string(request.POST['units'])
            conversion_rate = get_float_or_none_from_string(request.POST['conversion_rate'])
            trans_price = get_float_or_none_from_string(request.POST['trans_price'])
            realised_gain = trans_price - (float(espp_obj.purchase_price) * float(espp_obj.purchase_conversion_rate) * float(units))
            notes = request.POST['notes']
            try:
                EsppSellTransactions.objects.create(espp=espp_obj, trans_date=trans_date, price=price, units=units, conversion_rate=conversion_rate,
                    trans_price=trans_price, realised_gain=realised_gain, notes=notes)
                update_latest_vals(espp_obj)
            except IntegrityError:
                print('transaction already exists')            
    except Espp.DoesNotExist:
        print(f"ESPP with id {id} does not exist")
        return HttpResponseRedirect(reverse('espps:espp-list'))
    return render(request, template, context)

class CurrentEspps(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, user_id=None):
        print("inside CurrentEspps")
        espps = dict()
        total = 0
        if user_id:
            espp_objs = Espp.objects.filter(sell_date__isnull=True).filter(user=user_id)
        else:
            espp_objs = Espp.objects.filter(sell_date__isnull=True)
        for espp in espp_objs:
            key = espp.symbol+espp.exchange+str(espp.user)
            if key in espps:
                espps[key]['total_purchase_price'] += espp.total_purchase_price
                espps[key]['shares_purchased'] += espp.shares_purchased
                if espp.latest_value:
                    espps[key]['latest_value'] += espp.latest_value
                if espp.gain:
                    espps[key]['gain'] += espp.gain
            else:
                espps[key] = dict()
                espps[key]['exchange'] = espp.exchange
                espps[key]['symbol'] = espp.symbol
                espps[key]['user_id'] = espp.user
                espps[key]['user'] = get_user_name_from_id(espp.user)
                espps[key]['total_purchase_price'] = espp.total_purchase_price
                espps[key]['shares_purchased'] = espp.shares_purchased
                if espp.latest_value:
                    espps[key]['latest_value'] = espp.latest_value
                if espp.gain:
                    espps[key]['gain'] = espp.gain
            if espp.as_on_date:
                espps[key]['as_on_date'] = espp.as_on_date
            if espp.latest_value:
                total += espp.latest_value
        data = dict()
        data['entry'] = list()
        for _,v in espps.items():
            data['entry'].append(v)
        data['total'] = total    
        return Response(data)


def espp_insights(request):
    template = 'espps/espp_insights.html'
    ret = list()
    today = datetime.date.today()
    total = dict()
    
    for i, espp in enumerate(Espp.objects.all()):
        print(f'{i} {espp.symbol} {espp.exchange} {espp.user} {espp.purchase_date}')
        std = espp.purchase_date
        r = lambda: random.randint(0,255)
        color = '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
        ret.append({
            'label':espp.purchase_date.strftime('%Y-%m-%d'),
            'data': list(),
            'fill': 'false',
            'borderColor':color
        })
        std = std+relativedelta(months=1)
        std = std.replace(day=1)
        reset_to_zero = False

        while True:
            val = 0
            trans = list()
            trans.append(Trans(espp.shares_purchased, espp.purchase_date, 'buy', espp.total_purchase_price))
            for st in EsppSellTransactions.objects.filter(espp=espp, trans_date__lte=std):
                trans.append(Trans(st.units, st.trans_date, 'sell', st.trans_price))
            q, _,_,_,_ = reconcile_event_based(trans, list(), list())
            lv = get_historical_stock_price_based_on_symbol(espp.symbol, espp.exchange, std+relativedelta(days=-5), std)
            if lv:
                print(lv)
                conv_rate = 1
                if espp.exchange in ['NASDAQ', 'NYSE']:
                    conv_val = get_in_preferred_currency(1, 'USD', std)
                    if conv_val:
                        conv_rate = conv_val
                elif espp.exchange in ['NSE', 'BSE', 'NSE/BSE']:
                    conv_val = get_in_preferred_currency(1, 'INR', std)
                    if conv_val:
                        conv_rate = conv_val
                for k,v in lv.items():
                    val += float(v)*float(conv_rate)*float(q)
                    break
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
            else:
                print(f'failed to get value of {espp.exchange}:{espp.symbol} on {std}')
    print(ret)
    if len(ret) > 0:
        d = list()
        for k,v in sorted(total.items()):
            d.append({'x':k, 'y':round(v,2)})
        r = lambda: random.randint(0,255)
        color = '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
        ret.append({
                    'label':'total',
                    'data': d,
                    'fill': 'false',
                    'borderColor':color,
                    'spanGaps': 'false'
                })
    context = dict()
    context['progress_data'] = ret
    print(context)
    return render(request, template, context)