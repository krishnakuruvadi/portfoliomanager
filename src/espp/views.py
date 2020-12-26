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
from .forms import EsppModelForm
from .models import Espp
from .espp_helper import update_latest_vals
from django.http import HttpResponseRedirect
from shared.handle_get import *
from shared.handle_create import add_common_stock
from rest_framework.views import APIView
from rest_framework.response import Response

class EsppCreateView(CreateView):
    template_name = 'espps/espp_create.html'
    form_class = EsppModelForm
    queryset = Espp.objects.all() # <blog>/<modelname>_list.html
    #success_url = '/'

    '''
    def form_valid(self, form):
        print(form.cleaned_data)
        return super().form_valid(form)
    '''

    def get_success_url(self):
        return reverse('espps:espp-list')
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.total_purchase_price = self.object.purchase_price*self.object.shares_purchased*self.object.purchase_conversion_rate
        if self.object.sell_price and self.object.sell_conversion_rate:
            self.object.total_sell_price = self.object.sell_price*self.object.shares_purchased*self.object.sell_conversion_rate
        self.object.save()
        form.save_m2m()
        add_common_stock(self.object.exchange, self.object.symbol, self.object.purchase_date)
        return HttpResponseRedirect(self.get_success_url())

class EsppListView(ListView):
    template_name = 'espps/espp_list.html'
    queryset = Espp.objects.all() # <blog>/<modelname>_list.html
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
        data['user_name_mapping'] = get_all_users()
        return data

class EsppDeleteView(DeleteView):
    template_name = 'espps/espp_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Espp, id=id_)

    def get_success_url(self):
        return reverse('espps:espp-list')

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
        return data

class EsppUpdateView(UpdateView):
    template_name = 'espps/espp_create.html'
    form_class = EsppModelForm

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Espp, id=id_)
    '''
    def form_valid(self, form):
        print(form.cleaned_data)
        return super().form_valid(form)
    '''
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.total_purchase_price = self.object.purchase_price*self.object.shares_purchased*self.object.purchase_conversion_rate
        self.object.total_sell_price = self.object.sell_price*self.object.shares_purchased*self.object.sell_conversion_rate
        self.object.save()
        form.save_m2m()
        return HttpResponseRedirect(self.get_success_url())

def refresh_espp_trans(request):
    template = '../../espp/'
    for espp_obj in Espp.objects.all():
        print("looping through espp " + str(espp_obj.id))
        update_latest_vals(espp_obj)
    return HttpResponseRedirect(template)

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