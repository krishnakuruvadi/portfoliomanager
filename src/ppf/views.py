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
from .ppf_helper import ppf_add_transactions, get_ppf_details, insert_ppf_trans_entry
from decimal import Decimal
from shared.handle_get import *
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from goal.goal_helper import get_goal_id_name_mapping_for_user
from tasks.tasks import pull_ppf_trans_from_bank


def add_ppf(request):
    template_name = 'ppfs/ppf_create.html'
    if request.method == 'POST':
        print(request.POST)
        number = request.POST['number']
        start_date = request.POST['start_date']
        user = request.POST['user']
        goal = request.POST['goal']
        if goal != '':
            goal_id = Decimal(goal)
        else:
            goal_id = None
        Ppf.objects.create(
            number=number,
            start_date=start_date,
            user=user,
            goal=goal_id
        )

    users = get_all_users()
    context = {'users':users, 'operation': 'Add PPF'}
    return render(request, template_name, context)

class PpfListView(ListView):
    template_name = 'ppfs/ppf_list.html'
    queryset = Ppf.objects.all() # <blog>/<modelname>_list.html
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
        data['user_name_mapping'] = get_all_users()
        data['total'] = dict()
        data['principal'] = dict()
        data['interest'] = dict()
        data['roi'] = dict()
        for ppf_obj in Ppf.objects.all():
            data[ppf_obj.number] = dict()
            ppf_details = get_ppf_details(ppf_obj.number)
            data['total'][ppf_obj.number] = ppf_details['total']
            data['principal'][ppf_obj.number] = ppf_details['principal']
            data['interest'][ppf_obj.number] = ppf_details['interest']
            data['roi'][ppf_obj.number] = ppf_details['roi']
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
        data['user_str'] = get_user_name_from_id(data['object'].user)
        ppf_details = get_ppf_details(data['object'].number)
        data['total'] = ppf_details['total']
        data['principal'] = ppf_details['principal']
        data['interest'] = ppf_details['interest']
        data['roi'] = ppf_details['roi']
        return data

def update_ppf(request, id):
    template_name = 'ppfs/ppf_update.html'
    if request.method == 'POST':
        try:
            print(request.POST)
            ppf_obj = Ppf.objects.get(number=id)
            ppf_obj.start_date = request.POST['start_date']
            ppf_obj.user = request.POST['user']
            goal = request.POST['goal']
            if goal != '':
                goal_id = Decimal(goal)
            else:
                goal_id = None
            ppf_obj.goal = goal_id
            ppf_obj.save()
            return HttpResponseRedirect("../")
        except Ppf.DoesNotExist:
                pass
    else:
        try:
            ppf_obj = Ppf.objects.get(number=id)
            # Always put date in %Y-%m-%d for chrome to show things properly
            users = get_all_users()
            goals = get_goal_id_name_mapping_for_user(ppf_obj.user)
            context = {'goals':goals, 'users':users,'user':ppf_obj.user, 'number':ppf_obj.number, 'start_date':ppf_obj.start_date.strftime("%Y-%m-%d"),
                    'notes':ppf_obj.notes, 'goal':ppf_obj.goal,
                    'operation': 'Edit PPF'}
        except Ppf.DoesNotExist:
            context = {'operation': 'Edit PPF'}
    print(context)
    return render(request, template_name, context)


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
        return PpfEntry.objects.filter(number=self.number).order_by('-trans_date')

def add_trans(request, id):
    template_name = 'ppfs/ppf_add_trans.html'
    context = dict()
    context['number'] = id
    if request.method == 'POST':
        try:
            ppf_obj = Ppf.objects.get(number=id)
            date = request.POST['trans_date']
            trans_type = request.POST['entry_type']
            if trans_type == 'Buy':
                trans_type = 'CR'
            else:
                trans_type = 'DR'
            amount = request.POST['amount']
            notes = request.POST['notes']
            reference = request.POST['reference']
            if 'interest_component' in request.POST:
                interest_component = True
            else:
                interest_component = False
            insert_ppf_trans_entry(id, date, trans_type, amount, notes, reference, interest_component)
            
        except Ppf.DoesNotExist:
            print(f'PPF with number {id} doesnt exist')
        
    return render(request, template_name, context)


def upload_ppf_trans(request, id):
    # https://www.youtube.com/watch?v=Zx09vcYq1oc&list=PLLxk3TkuAYnpm24Ma1XenNeq1oxxRcYFT
    if request.method == 'POST':
        if "pull-submit" in request.POST:
            bank = request.POST.get('pullBankControlSelect')
            user_id = request.POST.get('pull-user-id')
            passwd = request.POST.get('pull-passwd')
            pull_ppf_trans_from_bank(id, bank, user_id, passwd)
        else:
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
            for entry in PpfEntry.objects.filter(number=id).order_by('trans_date'):
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
                interest = interest + int((prin['y'] + interest) * Decimal(projected_rate/100))
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

def get_contrib_values(ppf_id):
    principal = 0
    interest = 0
    try:
        ppf = Ppf.objects.get(number=ppf_id)
        for trans in PpfEntry.objects.filter(number=ppf):
            if trans.interest_component:
                interest += trans.amount
            else:
                principal += trans.amount
    except ppf.DoesNotExist:
        pass
    total = principal + interest
    contribs = {'principal': principal, 'interest':interest, 'total':total}
    return contribs

class CurrentPpfs(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, user_id=None):
        print("inside CurrentPpfs")
        ppfs = list()
        if user_id:
            ppf_objs = Ppf.objects.filter(end_date__isnull=True).filter(user=user_id)
        else:
            ppf_objs = Ppf.objects.filter(end_date__isnull=True)
        for ppf in ppf_objs:
            data = dict()
            data['number'] = ppf.number
            data['start_date'] = ppf.start_date
            data['user_id'] = ppf.user
            data['user'] = get_user_name_from_id(ppf.user)
            data['notes'] = ppf.notes
            vals = get_contrib_values(ppf.number)
            data['principal'] = vals['principal']
            data['interest'] = vals['interest']
            data['total'] = vals['total']
            ppfs.append(data)
        return Response(ppfs)