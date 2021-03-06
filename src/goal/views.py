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
from .goal_helper import one_time_pay_final_val, add_goal_entry, get_corpus_to_be_saved, get_depletion_vals
from dateutil.relativedelta import relativedelta
from ppf.models import Ppf, PpfEntry

from rest_framework.views import APIView
from rest_framework.response import Response
import json
from shared.handle_delete import delete_goal
from shared.handle_get import *
from shared.handle_chart_data import get_goal_contributions, get_goal_yearly_contrib


# Create your views here.

class GoalListView(ListView):
    template_name = 'goals/goal_list.html'
    queryset = Goal.objects.all() # <blog>/<modelname>_list.html
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['user_name_mapping'] = get_all_users()
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
        data['user_str'] = get_user_name_from_id(data['object'].user)
        data['target_date'] = data['object'].start_date+relativedelta(months=data['object'].time_period)
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
                'time_period': time_period, 'curr_val': curr_val, 'inflation':inflation, 'final_val':val}
            return render(request, template, context=context)
    users = get_all_users()
    context = {'users':users}
    return render(request, template, context=context)

def add_retirement_goal(request):
    # https://www.youtube.com/watch?v=Zx09vcYq1oc&list=PLLxk3TkuAYnpm24Ma1XenNeq1oxxRcYFT
    template = 'goals/add_retirement_goal.html'
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
                        'corpus_vals': corpus_vals, 'expense_vals': expense_vals}
            return render(request, template, context=context)
    users = get_all_users()
    context = {'users':users}
    return render(request, template, context)

def update_goal(request, id):
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
                                'corpus_vals': corpus_vals, 'expense_vals': expense_vals}
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
                            'corpus_vals': corpus_vals, 'expense_vals': expense_vals}
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
                        'time_period': time_period, 'curr_val': curr_val, 'inflation':inflation, 'final_val':val}
                    return render(request, template, context=context)
                return HttpResponseRedirect("../")
            else:
                users = get_all_users()
                context = {'users':users, 'user':goal_obj.user, 'startdate':goal_obj.start_date.strftime("%Y-%m-%d"), 'name': goal_obj.name,
                            'time_period': goal_obj.time_period, 'curr_val': goal_obj.curr_val,
                            'inflation':goal_obj.inflation, 'final_val':goal_obj.final_val,
                            'expense_period': goal_obj.expense_period, 'roi_corpus':goal_obj.post_returns,
                            'notes':goal_obj.notes, 'recurring_pay_goal': goal_obj.recurring_pay_goal}
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
            remaining_per = int(remaining*100/target)
            achieve_per = int(achieved*100/target)
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