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
from .forms import EpfModelForm
from .models import Epf, EpfEntry
import datetime
from dateutil.relativedelta import relativedelta
from shared.handle_get import *
from rest_framework.views import APIView
from rest_framework.response import Response
from shared.utils import get_date_or_none_from_string
from .epf_helper import get_summary_for_range
from decimal import Decimal
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from goal.goal_helper import get_goal_id_name_mapping_for_user

# Create your views here.

def create_epf(request):
    template_name = 'epfs/epf_create.html'
    if request.method == 'POST':
        print(request.POST)
        number = request.POST['number']
        end_date = get_date_or_none_from_string(request.POST['end_date'])
        start_date = get_date_or_none_from_string(request.POST['start_date'])
        company = request.POST['company']
        notes = request.POST['notes']
        user = request.POST['user']
        goal = request.POST['goal']
        if goal != '':
            goal_id = Decimal(goal)
        else:
            goal_id = None
        try:
            Epf.objects.create(
                number=number,
                end_date=end_date,
                start_date=start_date,
                company=company,
                user=user,
                goal=goal_id,
                notes=notes
            )
        except IntegrityError:
            print('EPF already exists')
    users = get_all_users()
    context = {'users':users, 'operation': 'Create EPF', 'curr_module_id': 'id_epf_module'}
    return render(request, template_name, context)

class EpfListView(ListView):
    template_name = 'epfs/epf_list.html'
    queryset = Epf.objects.all() # <blog>/<modelname>_list.html

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
        data['user_name_mapping'] = get_all_users()
        data[ 'curr_module_id'] = 'id_epf_module'
        return data

class EpfDeleteView(DeleteView):
    template_name = 'epfs/epf_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Epf, id=id_)

    def get_success_url(self):
        return reverse('epfs:epf-list')

class EpfDetailView(DetailView):
    template_name = 'epfs/epf_detail.html'
    #queryset = Ppf.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Epf, id=id_)
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_str'] = get_goal_name_from_id(data['object'].goal)
        data['user_str'] = get_user_name_from_id(data['object'].user)
        data['curr_module_id'] = 'id_epf_module'
        contribs = EpfEntry.objects.filter(epf_id=data['object']).order_by('trans_date')
        e = 0
        em = 0
        t = 0
        i = 0
        t_list = list()
        e_list = list()
        em_list = list()
        i_list = list()
        for c in contribs:
            e += int(c.employee_contribution)
            em += int(c.employer_contribution)
            i += int(c.interest_contribution)
            t += int(c.employee_contribution) + int(c.interest_contribution) + int(c.employer_contribution) - int(c.withdrawl)
            dt = c.trans_date.strftime('%Y-%m-%d')
            t_list.append({'x':dt, 'y':t})
            em_list.append({'x':dt, 'y':em})
            e_list.append({'x':dt, 'y':e})
            i_list.append({'x':dt, 'y':i})
        dt = datetime.date.today().strftime('%Y-%m-%d')
        t_list.append({'x':dt, 'y':t})
        em_list.append({'x':dt, 'y':em})
        e_list.append({'x':dt, 'y':e})
        i_list.append({'x':dt, 'y':i})
        data['chart_data'] = dict()
        data['chart_data']['employee'] = e_list
        data['chart_data']['employer'] = em_list
        data['chart_data']['total'] = t_list
        data['chart_data']['interest'] = i_list

        return data

def update_epf(request, id):
    template_name = 'epfs/epf_create.html'
    
    try:
        epf_obj = Epf.objects.get(id=id)
        if request.method == 'POST':
            print(request.POST)
            number = request.POST['number']
            end_date = get_date_or_none_from_string(request.POST['end_date'])
            start_date = get_date_or_none_from_string(request.POST['start_date'])
            company = request.POST['company']
            notes = request.POST['notes']
            user = request.POST['user']
            goal = request.POST['goal']
            if goal != '':
                goal_id = Decimal(goal)
            else:
                goal_id = None
            epf_obj.number=number
            epf_obj.end_date=end_date
            epf_obj.start_date=start_date
            epf_obj.company=company
            epf_obj.user=user
            epf_obj.goal=goal_id
            epf_obj.notes=notes
            epf_obj.save()
            return HttpResponseRedirect("../")
        else:
            users = get_all_users()
            goals = get_goal_id_name_mapping_for_user(epf_obj.user)
            context = {'goals':goals, 'users':users, 'user':epf_obj.user, 'number':epf_obj.number, 'start_date':epf_obj.start_date.strftime("%Y-%m-%d"),
                    'notes':epf_obj.notes, 'goal':epf_obj.goal, 'end_date':epf_obj.end_date.strftime("%Y-%m-%d") if epf_obj.end_date else None,
                    'operation': 'Edit EPF', 'company':epf_obj.company, 'curr_module_id': 'id_epf_module'}

    except Epf.DoesNotExist:
        return HttpResponseRedirect("../")
    
    return render(request, template_name, context)

def get_fy_details(epf_obj, fy):
    print('retrieving data for fy', fy)
    month_abbr = ['apr_', 'may_', 'jun_', 'jul_', 'aug_', 'sep_', 'oct_', 'nov_', 'dec_', 'jan_', 'feb_', 'mar_']
    datetime_str = '04/01/' + fy
    datetime_object = datetime.datetime.strptime(datetime_str, '%m/%d/%Y')
    ret = dict()
    for i in range(len(month_abbr)):
        date = datetime_object+relativedelta(months=i)
        try:
            contrib = EpfEntry.objects.get(epf_id=epf_obj, trans_date=date)
            ret[month_abbr[i] + 'int'] = int(contrib.interest_contribution)
            ret[month_abbr[i] + 'er'] = int(contrib.employer_contribution)
            ret[month_abbr[i] + 'em'] = int(contrib.employee_contribution)
        except EpfEntry.DoesNotExist:
            pass
    return ret

def show_contributions(request, id, year=None):
    template = 'epfs/epf_show_contrib.html'
    epf_obj = get_object_or_404(Epf, id=id)
    epf_start_year = epf_obj.start_date.year
    if epf_obj.start_date.month < 4:
        epf_start_year -= 1
    this_year = datetime.date.today().year if datetime.date.today().month < 4 else datetime.date.today().year+1

    print(epf_start_year)
    if not year:
        year = epf_start_year
    else:
        year = epf_start_year+int(year)
        if year > this_year:
            year = this_year
    start_date = str(year) + "-04-01"
    end_date = str(year+1) + "-03-31"
    fy = str(year) + '-' + str(year+1)[2:]
     # inclusive. SQL equivalent: SELECT ... WHERE pub_date BETWEEN '2005-01-01' and '2005-03-31';
    contribs = EpfEntry.objects.filter(epf_id=epf_obj, trans_date__range=[start_date, end_date])
    fy_trans = list()
    for contrib in contribs:
        entry = dict()
        entry['period'] = contrib.trans_date
        entry['em_contrib'] = contrib.employee_contribution
        entry['er_contrib'] = contrib.employer_contribution
        entry['interest'] = contrib.interest_contribution
        entry['withdrawl'] = contrib.withdrawl
        fy_trans.append(entry)
    summ = get_summary_for_range(epf_obj, get_date_or_none_from_string(start_date), get_date_or_none_from_string(end_date))
    context = {'fy_trans':fy_trans, 
                'object': {'number':epf_obj.number, 'id':epf_obj.id, 'company':epf_obj.company, 'fy':fy},
                'start_amount': summ['start_amt'], 'end_amount': summ['end_amount'], 'employee_contribution': summ['employee_contrib'],
                'employer_contribution': summ['employer_contrib'], 'interest_contribution':summ['interest_contrib'], 'curr_module_id':'id_epf_module'
                }
    if epf_start_year < year:
        context['prev_link'] = '../transactions/'+str(year-epf_start_year-1)
    else:
        context['prev_link'] = 'disabled'
    context['curr_link'] = '../transactions/'+str(year-epf_start_year)
    if year < this_year-1:
        context['next_link'] = '../transactions/'+str(year-epf_start_year+1)
    else:
        context['next_link'] = 'disabled'
    return render(request, template, context)

def add_contribution(request, id):
    template = 'epfs/epf_add_contrib.html'
    epf_obj = get_object_or_404(Epf, id=id)
    epf_start_year = epf_obj.start_date.year
    if epf_obj.start_date.month < 4:
        epf_start_year = epf_start_year - 1
    this_year = datetime.date.today().year if datetime.date.today().month < 4 else datetime.date.today().year+1
    fy_list = ['Select']
    for i in range(epf_start_year, this_year):
        fy_list.append(str(i) + '-' + str(i+1)[2:])
    month_abbr = ['apr_', 'may_', 'jun_', 'jul_', 'aug_', 'sep_', 'oct_', 'nov_', 'dec_', 'jan_', 'feb_', 'mar_']
    if request.method == 'POST':
        print(request.POST)
        print(request.POST.get('fy'))
        
        if "submit" in request.POST:
            print("submit button pressed")
            fy = request.POST.get('fy')
            fy = fy[0:4]
            datetime_str = '04/01/' + fy
            datetime_object = datetime.datetime.strptime(datetime_str, '%m/%d/%Y')
                
            for i in range(len(month_abbr)):
                interest_str = request.POST.get(month_abbr[i] + 'int')
                employee_str = request.POST.get(month_abbr[i] + 'em')
                employer_str = request.POST.get(month_abbr[i] + 'er')
                withdrawl_str = request.POST.get(month_abbr[i] + 'wd')
                print(f'interest_str {interest_str}  employee_str {employee_str} employer_str {employer_str} withdrawl_str {withdrawl_str}')
                interest = int(float(interest_str)) if interest_str != '' else 0
                employee = int(float(employee_str)) if employee_str != '' else 0
                employer = int(float(employer_str)) if employer_str != '' else 0
                withdrawl = int(float(withdrawl_str)) if withdrawl_str != '' else 0
                if (interest + employee + employer) > 0:
                    date = datetime_object+relativedelta(months=i)
                    try:
                        contrib = EpfEntry.objects.get(epf_id=epf_obj, trans_date=date)
                        contrib.employee_contribution = employee
                        contrib.employer_contribution = employer
                        contrib.interest_contribution = interest
                        contrib.withdrawl = withdrawl
                        contrib.save()
                    except EpfEntry.DoesNotExist:
                        EpfEntry.objects.create(epf_id=epf_obj,
                                                trans_date=date,
                                                employee_contribution=employee,
                                                employer_contribution=employer,
                                                interest_contribution=interest,
                                                withdrawl=withdrawl)
        else:
            print("fetch button pressed")
            fy = request.POST.get('fy')
            if fy != 'Select':
                context = get_fy_details(epf_obj, fy[0:4])
                context['fy_list']=fy_list
                context['sel_fy'] = fy
                context['object'] = {'id':epf_obj.id, 'number':epf_obj.number, 'company':epf_obj.company}
                print(context)
                return render(request, template, context)
    
    context = {'fy_list':fy_list, 'curr_module_id':'id_epf_module', 'object': {'id':epf_obj.id, 'number':epf_obj.number, 'company':epf_obj.company, 'sel_fy':'select'}}
    return render(request, template, context)

def get_contrib_values(epf_id):
    employer = 0
    employee = 0
    interest = 0
    try:
        epf = Epf.objects.get(id=epf_id)
        for trans in EpfEntry.objects.filter(epf_id=epf):
            employer += trans.employer_contribution
            employee += trans.employee_contribution
            interest += trans.interest_contribution
    except Epf.DoesNotExist:
        pass
    total = employer + employee + interest
    contribs = {'employer_contribution': employer, 'employee_contribution':employee, 'interest_contribution':interest, 'total':total}
    return contribs

class CurrentEpfs(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, user_id=None):
        print("inside get_current_epfs")
        epfs = list()
        if user_id:
            epf_objs = Epf.objects.filter(end_date__isnull=True).filter(user=user_id)
        else:
            epf_objs = Epf.objects.filter(end_date__isnull=True)
        for epf in epf_objs:
            data = dict()
            data['number'] = epf.number
            data['company'] = epf.company
            data['start_date'] = epf.start_date
            data['user_id'] = epf.user
            data['user'] = get_user_name_from_id(epf.user)
            data['notes'] = epf.notes
            vals = get_contrib_values(epf.id)
            data['employee_contribution'] = vals['employee_contribution']
            data['employer_contribution'] = vals['employer_contribution']
            data['interest_contribution'] = vals['interest_contribution']
            data['total'] = vals['total']
            epfs.append(data)
        return Response(epfs)
