from ppf.models import Ppf
from ssy.models import Ssy
from epf.models import Epf
from fixed_deposit.models import FixedDeposit
from espp.models import Espp
from goal.models import Goal
from users.models import User
from shares.models import Share
from mutualfunds.models import Folio
from rsu.models import RSUAward
from retirement_401k.models import Account401K
from insurance.models import InsurancePolicy
from gold.models import Gold
from bankaccounts.models import BankAccount

def delete_user(id):
    try:
        name = User.objects.get(id=id).name
        print(f'deleting user {id}: {name}')
        Epf.objects.filter(user=id).delete()
        Ppf.objects.filter(user=id).delete()
        Ssy.objects.filter(user=id).delete()
        FixedDeposit.objects.filter(user=id).delete()
        Espp.objects.filter(user=id).delete()
        Goal.objects.filter(user=id).delete()
        Share.objects.filter(user=id).delete()
        Folio.objects.filter(user=id).delete()
        RSUAward.objects.filter(user=id).delete()
        Account401K.objects.filter(user=id).delete()
        InsurancePolicy.objects.filter(user=id).delete()
        Gold.objects.filter(user=id).delete()
        BankAccount.objects.filter(user=id).delete()
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
        ssy_objs = Ssy.objects.filter(goal=id)
        for ssy_obj in ssy_objs:
            print("inside delete ssy_obj")
            ssy_obj.goal = None
            ssy_obj.save()
        fixed_deposit_objs = FixedDeposit.objects.filter(goal=id)
        for fixed_deposit_obj in fixed_deposit_objs:
            fixed_deposit_obj.goal = None
            fixed_deposit_obj.save()
        espp_objs = Espp.objects.filter(goal=id)
        for espp_obj in espp_objs:
            espp_obj.goal = None
            espp_obj.save()
        share_objs = Share.objects.filter(goal=id)
        for share_obj in share_objs:
            share_obj.goal = None
            share_obj.save()
        folio_objs = Folio.objects.filter(goal=id)
        for folio_obj in folio_objs:
            folio_obj.goal = None
            folio_obj.save()
        rsu_awards = RSUAward.objects.filter(goal=id)
        for rsu_award in rsu_awards:
            rsu_award.goal = None
            rsu_award.save()
        a401s = Account401K.objects.filter(goal=id)
        for a401 in a401s:
            a401.goal = None
            a401.save()
        ips = InsurancePolicy.objects.filter(goal=id)
        for ip in ips:
            ip.goal = None
            ip.save()
        gtrans = Gold.objects.filter(goal=id)
        for gt in gtrans:
            gt.goal = None
            gt.save()
        accounts = BankAccount.objects.filter(goal=id)
        for acc in accounts:
            acc.goal = None
            acc.save()

    except Goal.DoesNotExist:
        print(f'Exception during delete goal - doesnt exist')
    except Exception as ex:
        print(f'Exception {ex} during deleting goal')

