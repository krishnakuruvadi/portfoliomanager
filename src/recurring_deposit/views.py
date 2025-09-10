from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import (
    ListView,
    DetailView,
)
from dateutil.relativedelta import relativedelta
from django.http import HttpResponseRedirect
from decimal import Decimal
from .models import RecurringDeposit
from .recurring_deposit_helper import add_rd_entry, get_maturity_value
from shared.handle_get import *
from rest_framework.views import APIView
from rest_framework.response import Response
from goal.goal_helper import get_goal_id_name_mapping_for_user
from common.helper import get_preferred_currency_symbol
from django.db import IntegrityError

# Create your views here.

class RecurringDepositListView(ListView):
    template_name = 'recurring-deposits/recurring_deposit_list.html'
    queryset = RecurringDeposit.objects.all() # <blog>/<modelname>_list.html
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
        data['user_name_mapping'] = get_all_users()
        data['curr_module_id'] = 'id_rd_module'
        maturity_value = 0
        principal = 0
        for rd_obj in RecurringDeposit.objects.all():
            maturity_value += rd_obj.final_val
            principal += rd_obj.principal
            rd_obj.save()
        data['total_maturity'] = maturity_value
        data['total_principal'] = principal
        data['total_interest'] = maturity_value - principal
        data['preferred_currency'] = get_preferred_currency_symbol()

        return data

class RecurringDepositDetailView(DetailView):
    template_name = 'recurring-deposits/recurring_deposit_detail.html'
    #queryset = Ppf.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(RecurringDeposit, id=id_)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_str'] = get_goal_name_from_id(data['object'].goal)
        data['user_str'] = get_user_name_from_id(data['object'].user)
        data['curr_module_id'] = 'id_rd_module'
        return data

def delete_rd(request, id):
    try:
        f = RecurringDeposit.objects.get(id=id)
        f.delete()
    except RecurringDeposit.DoesNotExist:
        print(f'RD with id {id} does not exist')
    return HttpResponseRedirect(reverse('recurring-deposits:recurring-deposit-list'))

def add_recurring_deposit(request):
    template = 'recurring-deposits/add_recurring_deposit.html'
    message = ''
    message_color = 'ignore'
    if request.method == 'POST':
        print(request.POST)
        if "submit" in request.POST:
            print("submit button pressed")
            number = request.POST['number']
            bank_name = request.POST['bank_name']
            start_date = request.POST['start_date']
            user = request.POST['user']
            time_period_months = Decimal(request.POST['time_period_months'])
            roi = Decimal(request.POST['roi'])
            principal = Decimal(request.POST['principal'])
            final_val = Decimal(request.POST['final_val'])
            goal = request.POST.get('goal', '')
            if goal != '':
                goal_id = Decimal(goal)
            else:
                goal_id = None
            notes = request.POST['notes']
            mat_date = request.POST['mat_date']
            try:
                add_rd_entry(number, bank_name, start_date, principal, time_period_months,
                    final_val, user, notes, goal_id, roi, mat_date)
                message_color = 'green'
                message = 'Recurring Deposit addition successful'
            except IntegrityError as e:
                users = get_all_users()
                context = {'users':users, 'message_color': 'red', 'message': 'RD with same number already exists', 'operation': 'Add Recurring Deposit', 'curr_module_id': 'id_rd_module'}
                return render(request, template, context=context)
        else:
            print("calculate button pressed")
            number = request.POST['number']
            bank_name = request.POST['bank_name']
            start_date = request.POST['start_date']
            user = request.POST['user']
            time_period_months = Decimal(request.POST['time_period_months'])
            principal = Decimal(request.POST['principal'])
            roi = Decimal(request.POST['roi'])
            notes = request.POST['notes']
            goal = request.POST.get('goal', '')
            mat_date, val = get_maturity_value(int(principal), start_date, float(roi), int(time_period_months))
            print("calculated value", val)
            users = get_all_users()
            goals = get_goal_id_name_mapping_for_user(user)
            context = {'users':users,'user':user, 'number':number, 'start_date':start_date, 'bank_name': bank_name, 'roi': roi,
                'time_period_months': time_period_months, 'principal': principal, 'final_val':val, 'notes': notes,
                'goal':goal, 'mat_date':mat_date, 'operation': 'Add Recurring Deposit', 'goals':goals, 'curr_module_id': 'id_rd_module'}
            return render(request, template, context=context)
    users = get_all_users()
    context = {'users':users, 'operation': 'Add Recurring Deposit', 'curr_module_id': 'id_rd_module', 'message_color': message_color, 'message': message}
    return render(request, template, context)


def update_recurring_deposit(request, id):
    template = 'recurring-deposits/add_recurring_deposit.html'
    if request.method == 'POST':
        print(request.POST)
        if "submit" in request.POST:
            print("submit button pressed")
            try:
                rd_obj = RecurringDeposit.objects.get(id=id)
                rd_obj.number = request.POST['number']
                rd_obj.bank_name = request.POST['bank_name']
                rd_obj.start_date = request.POST['start_date']
                rd_obj.user = request.POST['user']
                rd_obj.time_period = Decimal(request.POST['time_period_months'])
                rd_obj.roi = Decimal(request.POST['roi'])
                rd_obj.principal = Decimal(request.POST['principal'])
                rd_obj.final_val = Decimal(request.POST['final_val'])
                goal = request.POST.get('goal', '')
                if goal != '':
                    rd_obj.goal = Decimal(goal)
                else:
                    rd_obj.goal = None
                rd_obj.notes = request.POST['notes']
                rd_obj.mat_date = request.POST['mat_date']
                rd_obj.save()
            except RecurringDeposit.DoesNotExist:
                pass
        else:
            print("calculate button pressed")
            number = request.POST['number']
            bank_name = request.POST['bank_name']
            start_date = request.POST['start_date']
            user = request.POST['user']
            time_period_months = Decimal(request.POST['time_period_months'])
            principal = Decimal(request.POST['principal'])
            roi = Decimal(request.POST['roi'])
            notes = request.POST['notes']
            goal = request.POST.get('goal', '')
            mat_date, val = get_maturity_value(int(principal), start_date, float(roi), int(time_period_months))
            print("calculated value", val)
            users = get_all_users()
            goals = get_goal_id_name_mapping_for_user(user)
            context = {'goals':goals, 'users':users,'user':user, 'number':number, 'start_date':start_date, 'bank_name': bank_name, 'roi': roi,
                'time_period_months': time_period_months, 'principal': principal, 'final_val':val, 'notes': notes,
                'goal':goal, 'mat_date':mat_date, 'operation': 'Edit Recurring Deposit', 'curr_module_id': 'id_rd_module'}
            return render(request, template, context=context)
        return HttpResponseRedirect("../")
    else:
        try:
            rd_obj = RecurringDeposit.objects.get(id=id)
            # Always put date in %Y-%m-%d for chrome to show things properly
            users = get_all_users()
            goals = get_goal_id_name_mapping_for_user(rd_obj.user)
            context = {'goals':goals, 'users':users,'user':rd_obj.user, 'number':rd_obj.number, 'start_date':rd_obj.start_date.strftime("%Y-%m-%d"), 'bank_name':rd_obj.bank_name,
                    'roi':rd_obj.roi, 'time_period_months': rd_obj.time_period, 'principal': rd_obj.principal, 'final_val':rd_obj.final_val,
                    'notes':rd_obj.notes, 'goal':rd_obj.goal, 'mat_date':rd_obj.mat_date.strftime("%Y-%m-%d"),
                    'operation': 'Edit Recurring Deposit', 'curr_module_id': 'id_rd_module'}
        except RecurringDeposit.DoesNotExist:
            context = {'operation': 'Edit Recurring Deposit'}
        return render(request, template, context=context)

class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, id=None):
        try:
            rd_obj = RecurringDeposit.objects.get(id=id)
            amount_values= list()
            exp_amount_values = list()
            today = datetime.date.today()
            curr_date = rd_obj.start_date
            if today > rd_obj.start_date+relativedelta(days=-1):
                amount_values.append(dict({'x':(rd_obj.start_date+relativedelta(days=-1)).strftime("%Y-%m-%d"), 'y':0  }))
            else:
                exp_amount_values.append(dict({'x':(rd_obj.start_date+relativedelta(days=-1)).strftime("%Y-%m-%d"), 'y':0  }))

            if today > rd_obj.start_date:
                amount_values.append(dict({'x':rd_obj.start_date.strftime("%Y-%m-%d"), 'y':rd_obj.principal }))
            else:
                exp_amount_values.append(dict({'x':rd_obj.start_date.strftime("%Y-%m-%d"), 'y':rd_obj.principal  }))

            
            while curr_date < rd_obj.mat_date:
                curr_date = curr_date +relativedelta(months=1)
                time_period_months = (curr_date - rd_obj.start_date).months
                mat_date, val = get_maturity_value(int(rd_obj.principal), rd_obj.start_date.strftime("%Y-%m-%d"), float(rd_obj.roi), int(time_period_months))
                if today > curr_date:
                    amount_values.append(dict({'x':curr_date.strftime("%Y-%m-%d"), 'y':val }))
                else:
                    exp_amount_values.append(dict({'x':curr_date.strftime("%Y-%m-%d"), 'y':val }))
            if today > rd_obj.mat_date:
                amount_values.append(dict({'x':rd_obj.mat_date.strftime("%Y-%m-%d"), 'y':rd_obj.final_val }))
            else:
                exp_amount_values.append(dict({'x':rd_obj.mat_date.strftime("%Y-%m-%d"), 'y':rd_obj.final_val  }))

            if today > rd_obj.mat_date+relativedelta(days=1):
                amount_values.append(dict({'x':(rd_obj.mat_date+relativedelta(days=1)).strftime("%Y-%m-%d"), 'y':0 }))
            else:
                exp_amount_values.append(dict({'x':(rd_obj.mat_date+relativedelta(days=1)).strftime("%Y-%m-%d"), 'y':0  }))

            data = {
                "id":id,
                "exp_amount_values":exp_amount_values,
                "amount_values":amount_values
            }
            #mat_date, val = get_maturity_value(int(rd_obj.principal), rd_obj.start_date, float(rd_obj.roi), int(time_period_days))
        except RecurringDeposit.DoesNotExist:
            data = {}
        return Response(data)

class CurrentRds(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, user_id=None):
        print("inside CurrentRds")
        rds = list()
        if user_id:
            rd_objs = RecurringDeposit.objects.filter(mat_date__gte=datetime.date.today()).filter(user=user_id)
        else:
            rd_objs = RecurringDeposit.objects.filter(mat_date__gte=datetime.date.today())
        for rd in rd_objs:
            data = dict()
            data['number'] = rd.number
            data['bank_name'] = rd.bank_name
            data['start_date'] = rd.start_date
            data['principal'] = rd.principal
            data['roi'] = rd.roi
            data['final_val'] = rd.final_val
            data['user_id'] = rd.user
            data['user'] = get_user_name_from_id(rd.user)
            data['notes'] = rd.notes
            data['mat_date'] = rd.mat_date
            rds.append(data)
        return Response(rds)