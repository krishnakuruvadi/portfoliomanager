from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import (
    ListView,
    DetailView,
    DeleteView
)
from django.template import Context
from django.http import HttpResponseRedirect
from decimal import Decimal
from .models import Goal
from .goal_helper import one_time_pay_final_val, add_goal_entry, get_corpus_to_be_saved, get_depletion_vals, get_unallocated_amount
from dateutil.relativedelta import relativedelta
from ppf.models import Ppf, PpfEntry

from rest_framework.views import APIView
from rest_framework.response import Response
import json
from shared.handle_delete import delete_goal
from shared.handle_get import *
from shared.handle_chart_data import get_goal_contributions, get_goal_yearly_contrib
from shared.financial import *

# Create your views here.

class GoalListView(ListView):
    template_name = 'goals/goal_list.html'
    queryset = Goal.objects.all()
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['user_name_mapping'] = get_all_users()
        data['total_goals'] = len(self.queryset)
        data['target'] = 0
        data['achieved'] = 0
        for g in self.queryset:
            data['target'] += g.final_val
            data['achieved'] += g.achieved_amt
        if data['target'] > 0:
            data['ach_per'] = round(data['achieved']*100/data['target'],2)
        else:
            data['ach_per'] = 0
        data['unalloc'] = get_unallocated_amount()
        data['curr_module_id'] = 'id_goal_module'
        print(data)
        return data

class GoalDetailView(DetailView):
    template_name = 'goals/goal_detail.html'
    #queryset = Ppf.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Goal, id=id_)
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data['object'])
        data['distribution'] = {'labels':list(), 'vals':list(), 'colors':list()}
        has_data = False
        if data['object'].epf_conitrib > 0:
            data['distribution']['labels'].append('EPF')
            data['distribution']['vals'].append(float(data['object'].epf_conitrib))
            data['distribution']['colors'].append("#f15664")
            has_data = True
        if data['object'].espp_conitrib > 0:
            data['distribution']['labels'].append('ESPP')
            data['distribution']['vals'].append(float(data['object'].espp_conitrib))
            data['distribution']['colors'].append("#DC7633")
            has_data = True
        if data['object'].fd_conitrib > 0:
            data['distribution']['labels'].append('FD')
            data['distribution']['vals'].append(float(data['object'].fd_conitrib))
            data['distribution']['colors'].append("#006f75")
            has_data = True
        if data['object'].ppf_conitrib > 0:
            data['distribution']['labels'].append('PPF')
            data['distribution']['vals'].append(float(data['object'].ppf_conitrib))
            data['distribution']['colors'].append("#92993c")
            has_data = True
        if data['object'].ssy_conitrib > 0:
            data['distribution']['labels'].append('SSY')
            data['distribution']['vals'].append(float(data['object'].ssy_conitrib))
            data['distribution']['colors'].append("#f9c5c6")
            has_data = True
        if data['object'].rsu_conitrib > 0:
            data['distribution']['labels'].append('RSU')
            data['distribution']['vals'].append(float(data['object'].rsu_conitrib))
            data['distribution']['colors'].append("#AA12E8")
            has_data = True
        if data['object'].mf_conitrib > 0:
            data['distribution']['labels'].append('MutualFunds')
            data['distribution']['vals'].append(float(data['object'].mf_conitrib))
            data['distribution']['colors'].append("#bfff00")
            has_data = True
        if data['object'].shares_conitrib > 0:
            data['distribution']['labels'].append('Shares')
            data['distribution']['vals'].append(float(data['object'].shares_conitrib))
            data['distribution']['colors'].append("#e31219")
            has_data = True
        if data['object'].r_401k_contribution > 0:
            data['distribution']['labels'].append('401K')
            data['distribution']['vals'].append(float(data['object'].r_401k_contribution))
            data['distribution']['colors'].append("#617688")
            has_data = True        
        if has_data:
            print(data['distribution'])

        data['user_str'] = get_user_name_from_id(data['object'].user)
        data['target_date'] = data['object'].start_date+relativedelta(months=data['object'].time_period)
        data['progress_data'] = dict()
        id = data['object'].id
        chart_data, ret = get_goal_yearly_contrib(id, None)
        data['progress_data']['chart_data'] = chart_data
        data['progress_data']['avg_growth'] = ret.get('avg_growth', 0)
        data['progress_data']['avg_contrib'] = ret.get('avg_contrib', 0)
        data['final_projection'] = ret.get('final_projection', 0)
        total_contribution = ret.get('total_contribution', 0)
        contrib_percent = int(total_contribution*100/float(data['object'].final_val))
        project_percent = int(data['final_projection']*100/float(data['object'].final_val))
        remaining_percent = 100 - contrib_percent - project_percent
        if remaining_percent < 0:
            remaining_percent = 0
        data['status_line'] = [contrib_percent, project_percent, remaining_percent]
        data['status_text'] = ''
        if ret.get('avg_growth', 0) > 0:
            yrly_investment_reqd = get_required_yrly_investment(total_contribution,ret.get('avg_growth'), data['target_date'], data['object'].final_val)
            data['status_text'] = data['status_text'] + ' If '+str(yrly_investment_reqd) + ' per year is invested at '+ str(ret.get('avg_growth', 0))
            data['status_text'] = data['status_text'] + '% you will reach target.'
        if ret.get('avg_contrib', 0) > 0:
            growth_reqd = get_required_xirr(total_contribution, ret.get('avg_contrib', 0), data['target_date'], data['object'].final_val)
            data['status_text'] = data['status_text'] + ' Current investment of '+ str(ret.get('avg_contrib', 0)) + ' per year should grow at ' + str(growth_reqd) + '% to reach target.'
        if ret.get('last_yr_contrib', 0)>0:
            growth_reqd = get_required_xirr(total_contribution, ret.get('last_yr_contrib', 0), data['target_date'], data['object'].final_val)
            data['status_text'] = data['status_text'] + ' Last year investment of '+ str(ret.get('last_yr_contrib', 0)) + ' per year should grow at ' + str(growth_reqd) + '% to reach target.'
 
        if data['status_text'] == '':
            data['status_text'] = 'Currently investing ' + str(ret.get('avg_contrib', 0)) + ' per year.'
            yrly_investment_reqd = get_required_yrly_investment(0,12, data['target_date'], data['object'].final_val)
            data['status_text'] = data['status_text'] + ' If '+str(yrly_investment_reqd) + ' per year is invested at '+ str(12)
            data['status_text'] = data['status_text'] + '% you will reach target.'
            yrly_investment_reqd = get_required_yrly_investment(0,8, data['target_date'], data['object'].final_val)
            data['status_text'] = data['status_text'] + ' If '+str(yrly_investment_reqd) + ' per year is invested at '+ str(8)
            data['status_text'] = data['status_text'] + '% you will reach target.'
        data['curr_module_id'] = 'id_goal_module'
        print("GoalProgressData - returning:", data)
        print(data)
        return data

class GoalDeleteView(DeleteView):
    template_name = 'goals/goal_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Goal, id=id_)

    def get_success_url(self):
        return reverse('goals:goal-list')

    def delete(self, request, *args, **kwargs):
        delete_goal(kwargs['id'])
        return super(DeleteView, self).delete(request, *args, **kwargs)

def add_goal(request):
    # https://www.youtube.com/watch?v=Zx09vcYq1oc&list=PLLxk3TkuAYnpm24Ma1XenNeq1oxxRcYFT
    template = 'goals/add_goal.html'
    if request.method == 'POST':
        print(request.POST)
        if "submit" in request.POST:
            print("submit button pressed")
            name = request.POST['name']
            start_date = request.POST['startdate']
            user_id = request.POST['user']
            time_period = Decimal(request.POST['time_period'])
            curr_val = Decimal(request.POST['curr_val'])
            inflation = Decimal(request.POST['inflation'])
            final_val = Decimal(request.POST['final_val'])
            recurring_pay_goal = False
            expense_period = 0
            post_returns = 0
            notes = request.POST['notes']
            add_goal_entry(name, start_date, curr_val, time_period, inflation,
                final_val, user_id, recurring_pay_goal, expense_period,
                post_returns, notes)
        else:
            print("calculate button pressed")
            name = request.POST['name']
            start_date = request.POST['startdate']
            user = request.POST['user']
            time_period = Decimal(request.POST['time_period'])
            curr_val = Decimal(request.POST['curr_val'])
            inflation = Decimal(request.POST['inflation'])
            notes = request.POST['notes']

            val = one_time_pay_final_val(curr_val, inflation, time_period)
            print("calculated value", val)
            users = get_all_users()
            context = {'users':users, 'user':user, 'startdate':start_date, 'name': name, 'notes': notes,
                'time_period': time_period, 'curr_val': curr_val, 'inflation':inflation, 'final_val':val,
                'curr_module_id':'id_goal_module'}
            return render(request, template, context=context)
    users = get_all_users()
    context = {'users':users}
    return render(request, template, context=context)

def add_retirement_goal(request):
    # https://www.youtube.com/watch?v=Zx09vcYq1oc&list=PLLxk3TkuAYnpm24Ma1XenNeq1oxxRcYFT
    template = 'goals/add_retirement_goal.html'
    operation = 'Create Retirement Goal'
    if request.method == 'POST':
        print(request.POST)
        if "submit" in request.POST:
            print("submit button pressed")
            name = request.POST['name']
            start_date = request.POST['startdate']
            user_id = request.POST['user']
            time_period = Decimal(request.POST['time_period'])
            curr_val = Decimal(request.POST['curr_val'])
            inflation = Decimal(request.POST['inflation'])
            final_val = Decimal(request.POST['final_val'])
            post_returns = Decimal(request.POST['roi_corpus'])
            recurring_pay_goal = True
            expense_period = Decimal(request.POST['expense_period'])
            post_returns = Decimal(request.POST['roi_corpus'])
            notes = request.POST['notes']
            add_goal_entry(name, start_date, curr_val, time_period*12, inflation,
                    final_val, user_id, recurring_pay_goal, expense_period*12,
                    post_returns, notes)
        else:
            print("calculate button pressed")
            name = request.POST['name']
            start_date = request.POST['startdate']
            user = request.POST['user']
            time_period = Decimal(request.POST['time_period'])
            curr_val = Decimal(request.POST['curr_val'])
            inflation = Decimal(request.POST['inflation'])
            expense_period = Decimal(request.POST['expense_period'])
            post_returns = Decimal(request.POST['roi_corpus'])
            notes = request.POST['notes']
            corpus = get_corpus_to_be_saved(int(curr_val), float(inflation), int(time_period), int(expense_period), float(post_returns))
            print("calculated value", corpus)
            dates, corpus_vals, expense_vals = get_depletion_vals(corpus, int(curr_val), int(time_period), int(expense_period), float(inflation),  float(post_returns), start_date)
            print(json.dumps(dates))
            users = get_all_users()
            context = {'users':users, 'user':user, 'startdate':start_date, 'name': name, 'notes':notes,
                        'time_period': time_period, 'curr_val': curr_val, 'inflation':inflation, 'final_val':corpus,
                        'expense_period': expense_period, 'roi_corpus':post_returns, 'labels':json.dumps(dates), 
                        'corpus_vals': corpus_vals, 'expense_vals': expense_vals, 'operation':operation, 'curr_module_id':'id_goal_module'}
            return render(request, template, context=context)
    users = get_all_users()
    context = {'users':users, "labels":None, "data":None, 'operation':operation}
    return render(request, template, context)

def update_goal(request, id):
    operation = 'Edit Goal'
    try:
        goal_obj = Goal.objects.get(id=id)
        if goal_obj.recurring_pay_goal:
            template = 'goals/add_retirement_goal.html'
            if request.method == 'POST':
                print(request.POST)
                if "submit" in request.POST:
                    print("submit button pressed")
                    goal_obj.name = request.POST['name']
                    goal_obj.start_date = request.POST['startdate']
                    goal_obj.user = request.POST['user']
                    goal_obj.time_period = Decimal(request.POST['time_period'])*12
                    goal_obj.curr_val = Decimal(request.POST['curr_val'])
                    goal_obj.inflation = Decimal(request.POST['inflation'])
                    goal_obj.final_val = Decimal(request.POST['final_val'])
                    goal_obj.expense_period = Decimal(request.POST['expense_period'])*12
                    goal_obj.post_returns = Decimal(request.POST['roi_corpus'])
                    goal_obj.recurring_pay_goal = True
                    goal_obj.post_returns = Decimal(request.POST['roi_corpus'])
                    goal_obj.notes = request.POST['notes']
                    goal_obj.save()
                else:
                    print("calculate button pressed")
                    name = request.POST['name']
                    start_date = request.POST['startdate']
                    user = request.POST['user']
                    time_period = Decimal(request.POST['time_period'])
                    curr_val = Decimal(request.POST['curr_val'])
                    inflation = Decimal(request.POST['inflation'])
                    expense_period = Decimal(request.POST['expense_period'])
                    post_returns = Decimal(request.POST['roi_corpus'])
                    notes = request.POST['notes']
                    corpus = get_corpus_to_be_saved(int(curr_val), float(inflation), int(time_period), int(expense_period), float(post_returns))
                    print("calculated value", corpus)
                    dates, corpus_vals, expense_vals = get_depletion_vals(corpus, int(curr_val), int(time_period), int(expense_period), float(inflation),  float(post_returns), start_date)
                    print(json.dumps(dates))
                    users = get_all_users()
                    context = {'users':users, 'user':user, 'startdate':start_date, 'name': name, 'notes':notes,
                                'time_period': time_period, 'curr_val': curr_val, 'inflation':inflation, 'final_val':corpus,
                                'expense_period': expense_period, 'roi_corpus':post_returns, 'labels':json.dumps(dates), 
                                'corpus_vals': corpus_vals, 'expense_vals': expense_vals, 'operation':operation, 'curr_module_id':'id_goal_module'}
                    return render(request, template, context=context)
                return HttpResponseRedirect("../")
            else:
                users = get_all_users()
                dates, corpus_vals, expense_vals = get_depletion_vals(int(goal_obj.final_val), int(goal_obj.curr_val), int(goal_obj.time_period/12), int(goal_obj.expense_period/12), float(goal_obj.inflation),  float(goal_obj.post_returns), goal_obj.start_date.strftime("%Y-%m-%d"))
                context = {'users':users, 'user':goal_obj.user, 'startdate':goal_obj.start_date.strftime("%Y-%m-%d"), 'name': goal_obj.name,
                            'time_period': int(goal_obj.time_period/12), 'curr_val': goal_obj.curr_val,
                            'inflation':goal_obj.inflation, 'final_val':goal_obj.final_val,
                            'expense_period': int(goal_obj.expense_period/12), 'roi_corpus':goal_obj.post_returns,
                            'notes':goal_obj.notes, 'recurring_pay_goal': goal_obj.recurring_pay_goal, 'labels':json.dumps(dates),
                            'corpus_vals': corpus_vals, 'expense_vals': expense_vals, 'operation':operation, 'curr_module_id':'id_goal_module'}
                return render(request, template, context=context) 
        else:
            template = 'goals/add_goal.html'
            if request.method == 'POST':
                print(request.POST)
                if "submit" in request.POST:
                    print("submit button pressed")
                    goal_obj.name = request.POST['name']
                    goal_obj.start_date = request.POST['startdate']
                    goal_obj.user = request.POST['user']
                    goal_obj.time_period = Decimal(request.POST['time_period'])
                    goal_obj.curr_val = Decimal(request.POST['curr_val'])
                    goal_obj.inflation = Decimal(request.POST['inflation'])
                    goal_obj.final_val = Decimal(request.POST['final_val'])
                    goal_obj.recurring_pay_goal = False
                    goal_obj.expense_period = 0
                    goal_obj.post_returns = 0
                    goal_obj.notes = request.POST['notes']
                    goal_obj.save()
                else:
                    print("calculate button pressed")
                    name = request.POST['name']
                    start_date = request.POST['startdate']
                    user = request.POST['user']
                    time_period = Decimal(request.POST['time_period'])
                    curr_val = Decimal(request.POST['curr_val'])
                    inflation = Decimal(request.POST['inflation'])
                    notes = request.POST['notes']

                    val = one_time_pay_final_val(curr_val, inflation, time_period)
                    print("calculated value", val)
                    users = get_all_users()
                    context = {'users':users, 'user':user, 'startdate':start_date, 'name': name, 'notes':notes,
                        'time_period': time_period, 'curr_val': curr_val, 'inflation':inflation, 'final_val':val, 'operation':operation,
                        'curr_module_id':'id_goal_module'}
                    return render(request, template, context=context)
                return HttpResponseRedirect("../")
            else:
                users = get_all_users()
                context = {'users':users, 'user':goal_obj.user, 'startdate':goal_obj.start_date.strftime("%Y-%m-%d"), 'name': goal_obj.name,
                            'time_period': goal_obj.time_period, 'curr_val': goal_obj.curr_val,
                            'inflation':goal_obj.inflation, 'final_val':goal_obj.final_val,
                            'expense_period': goal_obj.expense_period, 'roi_corpus':goal_obj.post_returns,
                            'notes':goal_obj.notes, 'recurring_pay_goal': goal_obj.recurring_pay_goal, 'operation':operation,
                            'curr_module_id':'id_goal_module'}
                return render(request, template, context=context) 
    except Goal.DoesNotExist:
        pass

class GoalNames(APIView):
    authentication_classes = []
    permission_classes = []
    def get(self, request, format=None, user=None):
        data = dict()
        data['goal_list'] = list()
        if not user:
            return Response(data)
        print('user is', user)
        try:
            goal_list = dict()
            goal_objs = Goal.objects.filter(user=user)
            for goal_obj in goal_objs:
                goal_list[goal_obj.id] = goal_obj.name
            data['goal_list'] = goal_list
        except Exception as e:
            print(e)
        finally:
            print(data)
            return Response(data)


class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, id=None):
        data = dict()
        try:
            goal_obj = Goal.objects.get(id=id)
            contrib = get_goal_contributions(id)
            debt = contrib['debt']
            equity = contrib['equity']
            achieved = contrib['total']
            target = goal_obj.final_val
            if target < 1:
                target = 1
            remaining = target - achieved
            if remaining < 0:
                remaining = 0
            remaining_per = round(remaining*100/target, 2)
            achieve_per = round(achieved*100/target, 2)
            data = {
                "id": id,
                "debt": debt,
                "equity": equity,
                "distrib_labels": contrib['distrib_labels'],
                "distrib_vals": contrib['distrib_vals'],
                "distrib_colors": contrib['distrib_colors'],
                "achieved": achieved,
                "remaining": remaining,
                "remaining_per": remaining_per,
                "achieve_per": achieve_per,
            }
        except Exception as e:
            print(e)
        finally:
            print(data)
            return Response(data)

class CurrentGoals(APIView):
    authentication_classes = []
    permission_classes = []
    def get(self, request, format=None, user_id=None):
        goals = list()
        if user_id:
            goal_objs = Goal.objects.filter(user=user_id)
        else:
            goal_objs = Goal.objects.all()
        for goal_obj in goal_objs:
            data = dict()
            data['id'] = goal_obj.id
            data['name'] = goal_obj.name
            data['start_date'] = goal_obj.start_date
            data['curr_val'] = goal_obj.curr_val
            data['final_val'] = goal_obj.final_val
            data['user'] = get_user_name_from_id(goal_obj.user)
            data['user_id'] = goal_obj.user
            data['notes'] = goal_obj.notes
            contrib = get_goal_contributions(goal_obj.id)
            data['debt'] = contrib['debt']
            data['equity'] = contrib['equity']
            data['achieved'] = contrib['total']
            target = goal_obj.final_val
            if target < 1:
                target = 1
            remaining = target - data['achieved']
            if remaining < 0:
                remaining = 0
            data['remaining'] = remaining
            data['remaining_per'] = int(remaining*100/target)
            data['achieve_per'] = int(data['achieved']*100/target)
            data['target_date'] = goal_obj.start_date + relativedelta(months=goal_obj.time_period)
            goals.append(data)
        return Response(goals)

class GoalProgressData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, id=None, expected_return=None):
        print('inside goal progress data')
        data = dict()
        try:
            goal_obj = Goal.objects.get(id=id)
            #target_vals,target_dates = get_monthly_projected_vals_and_dates(goal_obj.start_date, goal_obj.start_amount, goal_obj.time_period, goal_obj.inflation)
            chart_data, ret = get_goal_yearly_contrib(id, expected_return)
            data['chart_data'] = chart_data
            data['avg_growth'] = ret.get('avg_growth', 0)
            data['avg_contrib'] = ret.get('avg_contrib', 0)
            print("GoalProgressData - returning:", data)
            
        except Exception as e:
            print('exception in GoalProgressData', e)
        finally:
            print('returning from finally', data)
            return Response(data)