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
from .models import RSUAward, RestrictedStockUnits
from .rsu_helper import update_latest_vals, get_rsu_award_latest_vals
from django.http import HttpResponseRedirect
from shared.handle_get import *
from shared.handle_create import add_common_stock
from django.shortcuts import redirect
from shared.utils import *

class RsuCreateView(CreateView):
    template_name = 'rsus/rsu_create.html'
    form_class = RsuModelForm
    queryset = RSUAward.objects.all() # <blog>/<modelname>_list.html
    #success_url = '/'

    '''
    def form_valid(self, form):
        print(form.cleaned_data)
        return super().form_valid(form)
    '''

    def get_success_url(self):
        return reverse('rsus:rsu-list')
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        #self.object.total_purchase_price = self.object.purchase_price*self.object.shares_purchased*self.object.purchase_conversion_rate
        self.object.save()
        form.save_m2m()
        # TODO: Fix me
        #add_common_stock(self.object.exchange, self.object.symbol, self.object.purchase_date)
        return HttpResponseRedirect(self.get_success_url())

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

class RsuVestDeleteView(DeleteView):
    template_name = 'rsus/rsu_delete_vest.html'
    
    def get_object(self):
        id_ = self.kwargs.get("vestid")
        print('deleting RestrictedStockUnits with id', id_)
        return get_object_or_404(RestrictedStockUnits, id=id_)

    def get_success_url(self):
        return reverse('rsus:rsu-vest-list')

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
    #queryset = Ppf.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(RestrictedStockUnits, id=id_)
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        return data

class RsuUpdateView(UpdateView):
    template_name = 'rsus/rsu_create.html'
    form_class = RsuModelForm

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(RSUAward, id=id_)
    '''
    def form_valid(self, form):
        print(form.cleaned_data)
        return super().form_valid(form)
    '''
    def form_valid(self, form):
        self.object = form.save(commit=False)
        #self.object.total_purchase_price = self.object.purchase_price*self.object.shares_purchased*self.object.purchase_conversion_rate
        self.object.save()
        form.save_m2m()
        return HttpResponseRedirect(self.get_success_url())

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
        entry['sell_date'] = rsu_obj.sell_date
        entry['sell_price'] = rsu_obj.sell_price
        entry['sell_conversion_rate'] = rsu_obj.sell_conversion_rate
        entry['total_sell_price'] = rsu_obj.total_sell_price
        entry['latest_conversion_rate'] = rsu_obj.latest_conversion_rate
        entry['latest_price'] = rsu_obj.latest_price
        entry['latest_value'] = rsu_obj.latest_value
        entry['as_on_date'] = rsu_obj.as_on_date
        entry['notes'] = rsu_obj.notes
        vest_list.append(entry)
     
    context = {'vest_list':vest_list, 'award_id':rsu_award.award_id, 'symbol':rsu_award.symbol, 'award_date':rsu_award.award_date}
    
    return render(request, template, context)

def add_vest(request,id):
    template = 'rsus/rsu_add_vest.html'
    rsu_obj = get_object_or_404(RSUAward, id=id)
    
    if request.method == 'POST':
        print(request.POST)
        if "submit" in request.POST:
            vest_date = get_date_or_none_from_string(request.POST.get('vest_date'))
            fmv = get_float_or_none_from_string(request.POST.get('fmv'))
            aquisition_price = get_float_or_none_from_string(request.POST.get('aquisition_price'))
            shares_vested = get_int_or_none_from_string(request.POST.get('shares_vested'))
            shares_for_sale = get_int_or_none_from_string(request.POST.get('shares_for_sale'))
            total_aquisition_price = get_float_or_none_from_string(request.POST.get('total_aquisition_price'))
            sell_date = get_date_or_none_from_string(request.POST.get('sell_date'))
            sell_price = get_float_or_none_from_string(request.POST.get('sell_price'))
            sell_conversion_rate = get_float_or_none_from_string(request.POST.get('sell_conversion_rate'))
            total_sell_price = get_float_or_none_from_string(request.POST.get('total_sell_price'))
            notes = request.POST.get('notes')
            rsu = RestrictedStockUnits.objects.create(award=rsu_obj,
                                                      vest_date=vest_date,
                                                      fmv=fmv,
                                                      aquisition_price=aquisition_price,
                                                      shares_vested=shares_vested,
                                                      shares_for_sale=shares_for_sale,
                                                      total_aquisition_price=total_aquisition_price,
                                                      sell_date=sell_date,
                                                      sell_price=sell_price,
                                                      sell_conversion_rate=sell_conversion_rate,
                                                      notes=notes)
            rsu.save()
            return redirect('rsus:rsu-vest-list', id=id)

    context = {'award_id':rsu_obj.award_id, 'symbol':rsu_obj.symbol, 'award_date':rsu_obj.award_date}
    
    return render(request, template, context)

def update_vest(request,id,vestid):
    template = 'rsus/rsu_add_vest.html'
    award_obj = get_object_or_404(RSUAward, id=id)
    rsu_obj = get_object_or_404(RestrictedStockUnits, id=vestid)
    
    if request.method == 'POST':
        print(request.POST)
        if "submit" in request.POST:
            rsu_obj.vest_date = get_date_or_none_from_string(request.POST.get('vest_date'))
            rsu_obj.fmv = get_float_or_none_from_string(request.POST.get('fmv'))
            rsu_obj.aquisition_price = get_float_or_none_from_string(request.POST.get('aquisition_price'))
            rsu_obj.shares_vested = get_int_or_none_from_string(request.POST.get('shares_vested'))
            rsu_obj.shares_for_sale = get_int_or_none_from_string(request.POST.get('shares_for_sale'))
            rsu_obj.total_aquisition_price = get_float_or_none_from_string(request.POST.get('total_aquisition_price'))
            rsu_obj.sell_date = get_date_or_none_from_string(request.POST.get('sell_date'))
            rsu_obj.sell_price = get_float_or_none_from_string(request.POST.get('sell_price'))
            rsu_obj.sell_conversion_rate = get_float_or_none_from_string(request.POST.get('sell_conversion_rate'))
            rsu_obj.total_sell_price = get_float_or_none_from_string(request.POST.get('total_sell_price'))
            rsu_obj.notes = request.POST.get('notes')
            rsu_obj.save()
            return redirect('rsus:rsu-vest-list', id=id)
    else:
        context = {'award_id':award_obj.award_id, 'symbol':award_obj.symbol, 'award_date':award_obj.award_date}
        context['vest_date'] = convert_date_to_string(rsu_obj.vest_date)
        context['fmv'] = rsu_obj.fmv
        context['aquisition_price'] = rsu_obj.aquisition_price
        context['shares_vested'] = rsu_obj.shares_vested
        context['shares_for_sale'] = rsu_obj.shares_for_sale
        context['total_aquisition_price'] = rsu_obj.total_aquisition_price
        if rsu_obj.sell_date:
            context['sell_date'] = convert_date_to_string(rsu_obj.sell_date)
            context['sell_price'] = rsu_obj.sell_price
            context['sell_conversion_rate'] = rsu_obj.sell_conversion_rate
        context['notes'] = rsu_obj.notes
        return render(request, template, context)

    context = {'award_id':award_obj.award_id, 'symbol':award_obj.symbol, 'award_date':award_obj.award_date}
    
    return render(request, template, context)
