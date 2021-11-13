from .models import Goal

class GoalInterface:

    @classmethod
    def get_chart_name(self):
        return 'Goal'

    @classmethod
    def get_export_name(self):
        return 'goals'
    
    @classmethod
    def get_current_version(self):
        return 'v1'

    @classmethod
    def export(self, user_id):
        ret = {
            self.get_export_name(): {
                'version':self.get_current_version()
            }
        }
        data = list()
        for goal in Goal.objects.filter(user=user_id):
            data.append({
                'name': goal.name,
                'start_date': goal.start_date,
                'curr_val': goal.curr_val, 
                'notes':goal.notes,
                'time_period': goal.time_period,
                'inflation':goal.inflation,
                'final_val':goal.final_val,
                'recurring_pay_goal':goal.recurring_pay_goal,
                'expense_period':goal.expense_period,
                'post_returns':goal.post_returns
            })
        
        ret[self.get_export_name()]['data'] = data
        print(ret)
        return ret
