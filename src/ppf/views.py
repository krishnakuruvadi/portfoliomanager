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
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response

from dateutil.relativedelta import relativedelta
import datetime
from .forms import PpfModelForm, PpfEntryModelForm
from .models import Ppf, PpfEntry
from .ppf_helper import ppf_add_transactions
import decimal
from shared.handle_get import get_goal_name_from_id, get_all_goals_id_to_name_mapping

class PpfCreateView(CreateView):
    template_name = 'ppfs/ppf_create.html'
    form_class = PpfModelForm
    queryset = Ppf.objects.all() # <blog>/<modelname>_list.html
    #success_url = '/'

    def form_valid(self, form):
        print(form.cleaned_data)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('ppfs:ppf-list')

class PpfListView(ListView):
    template_name = 'ppfs/ppf_list.html'
    queryset = Ppf.objects.all() # <blog>/<modelname>_list.html
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
        return data

class PpfDetailView(DetailView):
    template_name = 'ppfs/ppf_detail.html'
    #queryset = Ppf.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Ppf, number=id_)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_str'] = get_goal_name_from_id(data['object'].goal)
        return data

class PpfUpdateView(UpdateView):
    template_name = 'ppfs/ppf_create.html'
    form_class = PpfModelForm

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Ppf, number=id_)

    def form_valid(self, form):
        print(form.cleaned_data)
        return super().form_valid(form)


class PpfDeleteView(DeleteView):
    template_name = 'ppfs/ppf_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Ppf, number=id_)

    def get_success_url(self):
        return reverse('ppfs:ppf-list')

class PpfEntryListView(ListView):
    template_name = 'ppfs/ppf_entry_list.html'

    def get_queryset(self):
        self.number = get_object_or_404(Ppf, number=self.kwargs['id'])
        return PpfEntry.objects.filter(number=self.number)

class PpfAddEntryView(CreateView):
    template_name = 'ppfs/ppf_add_trans.html'
    form_class = PpfEntryModelForm
    queryset = Ppf.objects.all() # <blog>/<modelname>_list.html
    #success_url = '/'

    def form_valid(self, form):
        print(form.cleaned_data)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('ppfs:ppf-list')
    
    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """
        initial = super().get_initial()

        initial['number'] = self.kwargs['id']
        print(initial)
        print(self.kwargs['id'])

        return initial

def upload_ppf_trans(request, id):
    # https://www.youtube.com/watch?v=Zx09vcYq1oc&list=PLLxk3TkuAYnpm24Ma1XenNeq1oxxRcYFT
    if request.method == 'POST':
        uploaded_file = request.FILES['document']
        print(uploaded_file)
        print(request.POST.get('bankFormControlSelect'))
        print(id)
        fs = FileSystemStorage()
        file_locn = fs.save(uploaded_file.name, uploaded_file)
        print(file_locn)
        print(settings.MEDIA_ROOT)
        full_file_path = settings.MEDIA_ROOT + '/' + file_locn
        ppf_add_transactions(request.POST.get('bankFormControlSelect'), full_file_path)
        fs.delete(file_locn)
    return render(request, 'ppfs/ppf_add_entries.html')

class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, id=None):
        try:
            ppf_details = Ppf.objects.get(number=id)
            projected_rate = 8
            years_completed = relativedelta(datetime.date.today(), ppf_details.start_date).years
            print("completed years", years_completed)
            years_remaining = 15-years_completed-1
            ppf_data_principal = list()
            ppf_data_interest = list()
            ppf_data_bal = list()
            interest = 0
            principal = 0
            first_date = datetime.date.today()
            for entry in PpfEntry.objects.filter(number=id):
                #ppf_data_dates.append(entry.trans_date)
                if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                    if entry.interest_component:
                        interest += entry.amount
                    else:
                        principal += entry.amount
                else:
                    principal -= entry.amount
                    if principal < 0:
                        interest += principal
                        principal = 0
                prin = dict()
                inter = dict()
                bal = dict()
                prin['x'] = entry.trans_date.strftime("%Y-%m-%d")
                prin['y'] = principal
                inter['x'] = entry.trans_date.strftime("%Y-%m-%d")
                inter['y'] = interest
                bal['x'] = entry.trans_date.strftime("%Y-%m-%d")
                bal['y'] = principal+interest
                first_date = entry.trans_date
                ppf_data_principal.append(prin)
                ppf_data_interest.append(inter)
                ppf_data_bal.append(bal)
            
            avg_principal = int(principal/years_completed)
            print("average payment", avg_principal)
            ppf_exp_bal = list()
            ppf_exp_interest = list()
            ppf_exp_principal = list()
            first_entry_prin = dict()
            first_entry_prin['x'] = first_date.strftime("%Y-%m-%d")
            first_entry_prin['y'] = principal
            ppf_exp_principal.append(first_entry_prin)
            first_entry_int = dict()
            first_entry_int['x'] = first_date.strftime("%Y-%m-%d")
            first_entry_int['y'] = interest
            ppf_exp_interest.append(first_entry_int)
            first_entry_bal = dict()
            first_entry_bal['x'] = first_date.strftime("%Y-%m-%d")
            first_entry_bal['y'] = principal+interest
            ppf_exp_bal.append(first_entry_bal)

            #new_date = datetime.date.today()
            for i in range(years_remaining):
                prin = dict()
                inter = dict()
                bal = dict()
                first_date = first_date+relativedelta(years=+1)
                prin['x'] = first_date.strftime("%Y-%m-%d")
                inter['x'] = prin['x']
                bal['x'] = prin['x']
                principal = principal + avg_principal
                prin['y'] = principal
                interest = interest + int((prin['y'] + interest) *decimal.Decimal(projected_rate/100))
                inter['y'] = interest
                bal['y'] = prin['y'] + inter['y']
                print("on ", prin['x'], prin['y'], inter['y'], bal['y'])
                ppf_exp_principal.append(prin)
                ppf_exp_interest.append(inter)
                ppf_exp_bal.append(bal)

            data = {
                "id": id,
                "ppf_trans_principal": ppf_data_principal,
                "ppf_trans_interest": ppf_data_interest,
                "ppf_trans_bal": ppf_data_bal,
                "ppf_exp_principal": ppf_exp_principal,
                "ppf_exp_interest": ppf_exp_interest,
                "ppf_exp_bal": ppf_exp_bal,
            }
            print(data)
        except Ppf.DoesNotExist:
            data = {}
        return Response(data)