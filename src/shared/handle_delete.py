from ppf.models import Ppf
from epf.models import Epf
from fixed_deposit.models import FixedDeposit
from espp.models import Espp
from goal.models import Goal
from users.models import User

def delete_user(id):
    try:
        name = User.objects.get(id=id).name
        print('name is', name)
        Epf.objects.filter(user=name).delete()
        Ppf.objects.filter(user=name).delete()
        FixedDeposit.objects.filter(user=name).delete()
        Espp.objects.filter(user=name).delete()
        Goal.objects.filter(user=name).delete()
    except User.DoesNotExist:
        print("No user with that id found")
        pass

def delete_goal(id):
    print("inside delete goal")
    try:
        epf_objs = Epf.objects.filter(goal=id)
        for epf_obj in epf_objs:
            epf_obj.goal = None
            epf_obj.save()
        ppf_objs = Ppf.objects.filter(goal=id)
        for ppf_obj in ppf_objs:
            print("inside delete ppf_obj")
            ppf_obj.goal = None
            ppf_obj.save()
        fixed_deposit_objs = FixedDeposit.objects.filter(goal=id)
        for fixed_deposit_obj in fixed_deposit_objs:
            fixed_deposit_obj.goal = None
            fixed_deposit_obj.save()
        espp_objs = Espp.objects.filter(goal=id)
        for espp_obj in espp_objs:
            espp_obj.goal = None
            espp_obj.save()

    except Goal.DoesNotExist:
        pass


    