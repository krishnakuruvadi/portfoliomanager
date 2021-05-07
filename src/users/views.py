from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import (
    ListView,
    DetailView,
    DeleteView
)
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from django.template import Context
from shared.handle_delete import delete_user
from shared.handle_chart_data import get_user_contributions
from .models import User

# Create your views here.
class UserListView(ListView):
    template_name = 'users/user_list.html'
    queryset = User.objects.all()

class UserDetailView(DetailView):
    template_name = 'users/user_detail.html'

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(User, id=id_)

class UserDeleteView(DeleteView):
    template_name = 'users/user_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(User, id=id_)

    def get_success_url(self):
        return reverse('users:user-list')
    
    def delete(self, request, *args, **kwargs):
        print(request)
        delete_user(kwargs['id'])
        return super(DeleteView, self).delete(request, *args, **kwargs)

def add_user(request):
    template = 'users/add_user.html'
    if request.method == 'POST':
        name = request.POST['name']
        dob = request.POST['dob']
        email = request.POST['email']
        notes = request.POST['notes']
        User.objects.create(name=name, dob=dob, notes=notes, email=email)
    return render(request, template)

def update_user(request, id):
    template = 'users/add_user.html'
    try:
        user_obj = User.objects.get(id=id)
        if request.method == 'POST':
            user_obj.name = request.POST['name']
            user_obj.email = request.POST['email']
            user_obj.dob = request.POST['dob']
            user_obj.notes = request.POST['notes']
            user_obj.save()
        else:
            context = {'name': user_obj.name, 'email':user_obj.email, 'dob':user_obj.dob.strftime("%Y-%m-%d"), 'notes':user_obj.notes}
            return render(request, template, context=context)
        return HttpResponseRedirect("../")
    except User.DoesNotExist:
        pass

class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, id=None):
        data = dict()
        try:
            user_obj = User.objects.get(id=id)
            contrib = get_user_contributions(id)
            debt = contrib['debt']
            equity = contrib['equity']
            achieved = contrib['total']
            target = contrib['target']
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

class Users(APIView):
    authentication_classes = []
    permission_classes = []
    def get(self, request, format=None):
        data = dict()
        data['user_list'] = list()
        user_objs = User.objects.all()
        for user_obj in user_objs:
            obj = dict()
            obj['id'] = user_obj.id
            obj['name'] = user_obj.name
            data['user_list'].append(obj)
        return Response(data)