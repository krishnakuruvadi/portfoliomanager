from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    ListView,
    DeleteView
)
from .forms import RsuModelForm
from .models import RSUAward, RestrictedStockUnits, RSUSellTransactions
from .rsu_helper import update_latest_vals, get_rsu_award_latest_vals
from django.http import HttpResponseRedirect
from shared.handle_get import *
from shared.handle_create import add_common_stock
from django.shortcuts import redirect
from shared.utils import *
from rest_framework.views import APIView
from rest_framework.response import Response


def create_rsu(request):
    template = "rsus/rsu_create.html"
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
    users = get_all_users()
    context = {'users':users, 'operation': 'Add RSU Award'}
    return render(request, template, context)


def update_rsu(request, id):
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
        'user':obj.user
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
        print(data)
        return data

class RsuDeleteView(DeleteView):
    template_name = 'rsus/rsu_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(RSUAward, id=id_)

    def get_success_url(self):
        return reverse('rsus:rsu-list')

class RsuDetailView(DetailView):
    template_name = 'rsus/rsu_detail.html'
    #queryset = Ppf.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(RSUAward, id=id_)
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_str'] = get_goal_name_from_id(data['object'].goal)
        data['user_str'] = get_user_name_from_id(data['object'].user)
        return data

class RsuVestDetailView(DetailView):
    template_name = 'rsus/rsu_vest_detail.html'

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(RestrictedStockUnits, id=id_)
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['sell_trans'] = RSUSellTransactions.objects.filter(rsu_vest=data['object'])
        print(data)
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
     
    context = {'vest_list':vest_list, 'award_id':rsu_award.award_id, 'symbol':rsu_award.symbol, 'award_date':rsu_award.award_date}
    
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
        return render(request, template, context)
    except Exception as ex:
        print(f'exception getting sell transactions  {ex}')
        return HttpResponseRedirect(reverse('rsus:rsu-list'))

def delete_vest_sell_trans(request, id, vestid, selltransid):
    try:
        trans = RSUSellTransactions.objects.get(id=selltransid)
        trans.delete()
    except RSUSellTransactions.DoesNotExist:
        print(f'{selltransid} RSUSellTransaction does not exist')
    return HttpResponseRedirect(reverse('rsus:rsu-sell-vest',kwargs={'id':id,'vestid':vestid}))

def delete_vest(request, id, vestid):
    try:
        vest = RestrictedStockUnits.objects.get(id=vestid)
        vest.delete()
    except RestrictedStockUnits.DoesNotExist:
        print(f'{vestid} RestrictedStockUnits does not exist')
    return HttpResponseRedirect(reverse('rsus:rsu-vest-list',kwargs={'id':id}))

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
            return HttpResponseRedirect(reverse('rsus:rsu-sell-vest',kwargs={'id':id,'vestid':vestid}))
        else:
            context = {'award_date':award_obj.award_date, 'symbol':award_obj.symbol, 'award_id':award_obj.award_id,
             'vest_date':rsu_vest.vest_date, 'unsold_shares':rsu_vest.unsold_shares, 'aquisition_price':rsu_vest.aquisition_price, 'exchange':award_obj.exchange}
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
            notes = request.POST.get('notes')
            rsu = RestrictedStockUnits.objects.create(award=award_obj,
                                                      vest_date=vest_date,
                                                      fmv=fmv,
                                                      aquisition_price=aquisition_price,
                                                      shares_vested=shares_vested,
                                                      shares_for_sale=shares_for_sale,
                                                      unsold_shares=shares_for_sale,
                                                      total_aquisition_price=total_aquisition_price,
                                                      notes=notes)
            rsu.save()
            return redirect('rsus:rsu-vest-list', id=id)

    context = {'award_id':award_obj.award_id, 'exchange':award_obj.exchange, 'symbol':award_obj.symbol, 'award_date':award_obj.award_date}
    
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
        print(context)
        return render(request, template, context)

    context = {'award_id':award_obj.award_id, 'exchange':award_obj.exchange, 'symbol':award_obj.symbol, 'award_date':award_obj.award_date}
    
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