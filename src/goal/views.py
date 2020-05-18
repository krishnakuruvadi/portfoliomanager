from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import (
    ListView,
    DetailView,
    DeleteView
)
from django.template import Context
from decimal import Decimal
from .models import Goal
from .goal_helper import one_time_pay_final_val, add_goal_entry, get_corpus_to_be_saved, get_depletion_vals

from ppf.models import Ppf, PpfEntry

from rest_framework.views import APIView
from rest_framework.response import Response
import json


# Create your views here.

class GoalListView(ListView):
    template_name = 'goals/goal_list.html'
    queryset = Goal.objects.all() # <blog>/<modelname>_list.html

class GoalDetailView(DetailView):
    template_name = 'goals/goal_detail.html'
    #queryset = Ppf.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Goal, id=id_)

class GoalDeleteView(DeleteView):
    template_name = 'goals/goal_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Goal, id=id_)

    def get_success_url(self):
        return reverse('goals:goal-list')

def add_goal(request):
    # https://www.youtube.com/watch?v=Zx09vcYq1oc&list=PLLxk3TkuAYnpm24Ma1XenNeq1oxxRcYFT
    template = 'goals/add_goal.html'
    if request.method == 'POST':
        print(request.POST)
        if "submit" in request.POST:
            print("submit button pressed")
            name = request.POST['name']
            start_date = request.POST['startdate']
            user = request.POST['user']
            time_period = Decimal(request.POST['time_period'])
            curr_val = Decimal(request.POST['curr_val'])
            inflation = Decimal(request.POST['inflation'])
            final_val = Decimal(request.POST['final_val'])
            recurring_pay_goal = False
            expense_period = 0
            post_returns = 0
            notes = request.POST['notes']
            add_goal_entry(name, start_date, curr_val, time_period, inflation,
                    final_val, user, recurring_pay_goal, expense_period,
                    post_returns, notes)
        else:
            print("calculate button pressed")
            name = request.POST['name']
            start_date = request.POST['startdate']
            user = request.POST['user']
            time_period = Decimal(request.POST['time_period'])
            curr_val = Decimal(request.POST['curr_val'])
            inflation = Decimal(request.POST['inflation'])

            val = one_time_pay_final_val(curr_val, inflation, time_period)
            print("calculated value", val)
            context = {'user':user, 'startdate':start_date, 'name': name,
                'time_period': time_period, 'curr_val': curr_val, 'inflation':inflation, 'final_val':val}
            return render(request, template, context=context)
    return render(request, template)

def add_retirement_goal(request):
    # https://www.youtube.com/watch?v=Zx09vcYq1oc&list=PLLxk3TkuAYnpm24Ma1XenNeq1oxxRcYFT
    template = 'goals/add_retirement_goal.html'
    if request.method == 'POST':
        print(request.POST)
        if "submit" in request.POST:
            print("submit button pressed")
            name = request.POST['name']
            start_date = request.POST['startdate']
            user = request.POST['user']
            time_period = Decimal(request.POST['time_period'])
            curr_val = Decimal(request.POST['curr_val'])
            inflation = Decimal(request.POST['inflation'])
            final_val = Decimal(request.POST['final_val'])
            expense_period = Decimal(request.POST['expense_period'])
            post_returns = Decimal(request.POST['roi_corpus'])
            recurring_pay_goal = True
            expense_period = Decimal(request.POST['expense_period'])
            post_returns = Decimal(request.POST['roi_corpus'])
            notes = request.POST['notes']
            add_goal_entry(name, start_date, curr_val, time_period*12, inflation,
                    final_val, user, recurring_pay_goal, expense_period*12,
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
            corpus = get_corpus_to_be_saved(int(curr_val), float(inflation), int(time_period), int(expense_period), float(post_returns))
            print("calculated value", corpus)
            dates, corpus_vals, expense_vals = get_depletion_vals(corpus, int(curr_val), int(time_period), int(expense_period), float(inflation),  float(post_returns), start_date)
            print(json.dumps(dates))
            context = {'user':user, 'startdate':start_date, 'name': name,
                        'time_period': time_period, 'curr_val': curr_val, 'inflation':inflation, 'final_val':corpus,
                        'expense_period': expense_period, 'roi_corpus':post_returns, 'labels':json.dumps(dates), 
                        'corpus_vals': corpus_vals, 'expense_vals': expense_vals}
            return render(request, template, context=context)
    return render(request, template)

class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, id=None):
        data = dict()
        try:
            goal_obj = Goal.objects.get(id=id)
            ppf_objs = Ppf.objects.filter(goal=id)
            total_ppf = 0
            for ppf_obj in ppf_objs:
                ppf_num = ppf_obj.number
                amt = 0
                ppf_trans = PpfEntry.objects.filter(number=ppf_num)
                for entry in ppf_trans:
                    if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                        amt += entry.amount
                    else:
                        amt -= entry.amount
                    if amt < 0:
                        amt = 0
                total_ppf += amt
            debt = total_ppf
            equity = 0
            achieved = debt + equity
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
                "total_ppf": total_ppf,
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