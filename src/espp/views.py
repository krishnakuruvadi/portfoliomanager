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
from .espp_helper import get_latest_vals
from django.http import HttpResponseRedirect

class EsppCreateView(CreateView):
    template_name = 'espps/espp_create.html'
    form_class = EsppModelForm
    queryset = Espp.objects.all() # <blog>/<modelname>_list.html
    #success_url = '/'

    def form_valid(self, form):
        print(form.cleaned_data)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('espps:espp-list')
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.total_purchase_price = self.object.purchase_price*self.object.shares_purchased*self.object.purchase_conversion_rate
        self.object.save()
        form.save_m2m()
        return HttpResponseRedirect(self.get_success_url())

class EsppListView(ListView):
    template_name = 'espps/espp_list.html'
    queryset = Espp.objects.all() # <blog>/<modelname>_list.html

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

class EsppUpdateView(UpdateView):
    template_name = 'espps/espp_create.html'
    form_class = EsppModelForm

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Espp, id=id_)

    def form_valid(self, form):
        print(form.cleaned_data)
        return super().form_valid(form)

def refresh_espp_trans(request):
    template = '../../espp/'
    for espp_obj in Espp.objects.all():
        print("looping through espp " + str(espp_obj.id))
        get_latest_vals(espp_obj)
    return HttpResponseRedirect(template)
