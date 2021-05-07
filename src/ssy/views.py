from django.shortcuts import render

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
from .forms import SsyEntryModelForm
from .models import Ssy, SsyEntry
from .ssy_helper import ssy_add_transactions, get_ssy_details, insert_ssy_trans_entry
from decimal import Decimal
from shared.handle_get import *
from goal.goal_helper import get_goal_id_name_mapping_for_user
from django.http import HttpResponseRedirect
from tasks.tasks import pull_ssy_trans_from_bank


def add_ssy(request):
    template_name = 'ssys/ssy_create.html'
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
        Ssy.objects.create(
            number=number,
            start_date=start_date,
            user=user,
            goal=goal_id
        )

    users = get_all_users()
    context = {'users':users, 'operation': 'Add SSY'}
    return render(request, template_name, context)


def update_ssy(request, id):
    template_name = 'ssys/ssy_update.html'
    if request.method == 'POST':
        try:
            print(request.POST)
            ssy_obj = Ssy.objects.get(number=id)
            ssy_obj.start_date = request.POST['start_date']
            ssy_obj.user = request.POST['user']
            goal = request.POST['goal']
            if goal != '':
                goal_id = Decimal(goal)
            else:
                goal_id = None
            ssy_obj.goal = goal_id
            ssy_obj.save()
            return HttpResponseRedirect("../")
        except Ssy.DoesNotExist:
                pass
    else:
        try:
            ssy_obj = Ssy.objects.get(number=id)
            # Always put date in %Y-%m-%d for chrome to show things properly
            users = get_all_users()
            goals = get_goal_id_name_mapping_for_user(ssy_obj.user)
            context = {'goals':goals, 'users':users,'user':ssy_obj.user, 'number':ssy_obj.number, 'start_date':ssy_obj.start_date.strftime("%Y-%m-%d"),
                    'notes':ssy_obj.notes, 'goal':ssy_obj.goal,
                    'operation': 'Edit SSY'}
        except Ssy.DoesNotExist:
            context = {'operation': 'Edit SSY'}
    print(context)
    return render(request, template_name, context)

class SsyListView(ListView):
    template_name = 'ssys/ssy_list.html'
    queryset = Ssy.objects.all() # <blog>/<modelname>_list.html
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
        data['user_name_mapping'] = get_all_users()
        data['total'] = dict()
        data['principal'] = dict()
        data['interest'] = dict()
        data['roi'] = dict()
        for ssy_obj in Ssy.objects.all():
            data[ssy_obj.number] = dict()
            ssy_details = get_ssy_details(ssy_obj.number)
            data['total'][ssy_obj.number] = ssy_details['total']
            data['principal'][ssy_obj.number] = ssy_details['principal']
            data['interest'][ssy_obj.number] = ssy_details['interest']
            data['roi'][ssy_obj.number] = ssy_details['roi']
        return data

class SsyDetailView(DetailView):
    template_name = 'ssys/ssy_detail.html'
    #queryset = Ssy.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Ssy, number=id_)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_str'] = get_goal_name_from_id(data['object'].goal)
        data['user_str'] = get_user_name_from_id(data['object'].user)
        ssy_details = get_ssy_details(data['object'].number)
        data['total'] = ssy_details['total']
        data['principal'] = ssy_details['principal']
        data['interest'] = ssy_details['interest']
        data['roi'] = ssy_details['roi']
        return data

class SsyDeleteView(DeleteView):
    template_name = 'ssys/ssy_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Ssy, number=id_)

    def get_success_url(self):
        return reverse('ssys:ssy-list')

class SsyEntryListView(ListView):
    template_name = 'ssys/ssy_entry_list.html'

    def get_queryset(self):
        self.number = get_object_or_404(Ssy, number=self.kwargs['id'])
        return SsyEntry.objects.filter(number=self.number).order_by('-trans_date')

def add_trans(request, id):
    template_name = 'ssys/ssy_add_trans.html'
    context = dict()
    context['number'] = id
    if request.method == 'POST':
        try:
            ssy_obj = Ssy.objects.get(number=id)
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
            insert_ssy_trans_entry(id, date, trans_type, amount, notes, reference, interest_component)
            
        except Ssy.DoesNotExist:
            print(f'SSY with number {id} doesnt exist')
        
    return render(request, template_name, context)


def upload_ssy_trans(request, id):
    # https://www.youtube.com/watch?v=Zx09vcYq1oc&list=PLLxk3TkuAYnpm24Ma1XenNeq1oxxRcYFT
    if request.method == 'POST':
        if "pull-submit" in request.POST:
            bank = request.POST.get('pullBankControlSelect')
            user_id = request.POST.get('pull-user-id')
            passwd = request.POST.get('pull-passwd')
            pull_ssy_trans_from_bank(id, bank, user_id, passwd)
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
            ssy_add_transactions(request.POST.get('bankFormControlSelect'), full_file_path)
            fs.delete(file_locn)
    return render(request, 'ssys/ssy_add_entries.html')

class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, id=None):
        try:
            ssy_details = Ssy.objects.get(number=id)
            projected_rate = 8
            years_completed = relativedelta(datetime.date.today(), ssy_details.start_date).years
            if years_completed == 0:
                years_completed = 1
            print("completed years", years_completed)
            years_remaining = 15-years_completed-1
            ssy_data_principal = list()
            ssy_data_interest = list()
            ssy_data_bal = list()
            interest = 0
            principal = 0
            first_date = datetime.date.today()
            for entry in SsyEntry.objects.filter(number=id).order_by('trans_date'):
                #ssy_data_dates.append(entry.trans_date)
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
                ssy_data_principal.append(prin)
                ssy_data_interest.append(inter)
                ssy_data_bal.append(bal)
            
            avg_principal = int(principal/years_completed)
            print(f" total paid {principal} over {years_completed} years with average payment {avg_principal}")
            ssy_exp_bal = list()
            ssy_exp_interest = list()
            ssy_exp_principal = list()
            first_entry_prin = dict()
            first_entry_prin['x'] = first_date.strftime("%Y-%m-%d")
            first_entry_prin['y'] = principal
            ssy_exp_principal.append(first_entry_prin)
            first_entry_int = dict()
            first_entry_int['x'] = first_date.strftime("%Y-%m-%d")
            first_entry_int['y'] = interest
            ssy_exp_interest.append(first_entry_int)
            first_entry_bal = dict()
            first_entry_bal['x'] = first_date.strftime("%Y-%m-%d")
            first_entry_bal['y'] = principal+interest
            ssy_exp_bal.append(first_entry_bal)

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
                ssy_exp_principal.append(prin)
                ssy_exp_interest.append(inter)
                ssy_exp_bal.append(bal)

            data = {
                "id": id,
                "ssy_trans_principal": ssy_data_principal,
                "ssy_trans_interest": ssy_data_interest,
                "ssy_trans_bal": ssy_data_bal,
                "ssy_exp_principal": ssy_exp_principal,
                "ssy_exp_interest": ssy_exp_interest,
                "ssy_exp_bal": ssy_exp_bal,
            }
            print(data)
        except Ssy.DoesNotExist:
            data = {}
        return Response(data)

def get_contrib_values(ssy_id):
    principal = 0
    interest = 0
    try:
        ssy = Ssy.objects.get(number=ssy_id)
        for trans in SsyEntry.objects.filter(number=ssy):
            if trans.interest_component:
                interest += trans.amount
            else:
                principal += trans.amount
    except Ssy.DoesNotExist:
        pass
    total = principal + interest
    contribs = {'principal': principal, 'interest':interest, 'total':total}
    return contribs

class CurrentSsys(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, user_id=None):
        print("inside CurrentSsys")
        ssys = list()
        if user_id:
            ssy_objs = Ssy.objects.filter(user=user_id)
        else:
            ssy_objs = Ssy.objects.all()
        for ssy in ssy_objs:
            data = dict()
            data['number'] = ssy.number
            data['start_date'] = ssy.start_date
            data['user_id'] = ssy.user
            data['user'] = get_user_name_from_id(ssy.user)
            data['notes'] = ssy.notes
            vals = get_contrib_values(ssy.number)
            data['principal'] = vals['principal']
            data['interest'] = vals['interest']
            data['total'] = vals['total']
            ssys.append(data)
        return Response(ssys)
