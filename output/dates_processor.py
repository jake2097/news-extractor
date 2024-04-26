import calendar
from datetime import date

class DatesProcessor:

    def __init__(self, required_months_count):
        self.required_months_count = required_months_count


    def get_current_month(self):
        today = date.today()
        current_month = today.strftime("%B")
        return current_month


    def get_required_months(self, months_count):
        all_months = list(calendar.month_name)
        all_months.remove("")
        current_month = self.get_current_month()
        current_month_index = all_months.index(current_month)
        required_months = all_months[current_month_index-months_count: current_month_index+1]
        return required_months


    def is_suitable_date(self, date):
        all_months = list(calendar.month_name)
        all_months.remove("")
        required_months = self.get_required_months(self.required_months_count)
        suitable = all(month not in date for month in all_months) or any(month in date for month in required_months)
        return suitable