from .models import User
from epf.epf_interface import EpfInterface
from espp.espp_interface import EsppInterface
from fixed_deposit.fd_interface import FdInterface
from ppf.ppf_interface import PpfInterface
from ssy.ssy_interface import SsyInterface
from shares.share_interface import ShareInterface
from mutualfunds.mf_interface import MfInterface
from retirement_401k.r401k_interface import R401KInterface
from rsu.rsu_interface import RsuInterface
from insurance.insurance_interface import InsuranceInterface
from gold.gold_interface import GoldInterface
from bankaccounts.bank_account_interface import BankAccountInterface
from goal.goal_interace import GoalInterface

class UserInterface:

    @classmethod
    def get_chart_name(self):
        return 'User'

    @classmethod
    def get_export_name(self):
        return 'users'
    
    @classmethod
    def get_current_version(self):
        return 'v1'

    @classmethod
    def export(self):
        ret = {
            self.get_export_name(): {
                'version':self.get_current_version()
            }
        }
        data = list()
        for user in User.objects.all():
            ud = {
                'name': user.name,
                'email': user.email,
                'dob': user.dob, 
                'notes':user.notes,
                'short_name': user.short_name
            }
            for intf in [GoalInterface, EpfInterface, EsppInterface, FdInterface, MfInterface, PpfInterface, SsyInterface, ShareInterface, R401KInterface, RsuInterface, InsuranceInterface, GoldInterface, BankAccountInterface]:
                ud = {**ud, **intf.export(user.id)}
            data.append(ud)
        ret[self.get_export_name()]['data'] = data
        print(ret)
        return ret

