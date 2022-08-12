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
from crypto.crypto_interface import CryptoInterface

def get_users(ext_user):
    return User.objects.all()

def get_ext_user(id):
    return None

def user_count():
    count = User.objects.count()
    return count

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
            for intf in [GoalInterface, EpfInterface, EsppInterface, FdInterface, MfInterface, PpfInterface, SsyInterface, ShareInterface, R401KInterface, RsuInterface, InsuranceInterface, GoldInterface, BankAccountInterface, CryptoInterface]:
                ud = {**ud, **intf.export(user.id)}
            data.append(ud)
        ret[self.get_export_name()]['data'] = data
        print(ret)
        return ret

