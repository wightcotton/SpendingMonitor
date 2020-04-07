import pandas as pd
from datetime import date
import xlrd
import numpy as np

class DataObjectFactory_old(object):

    def __init__(self, filename, file):
        self.trans = None
        self.budget = None
        if '.csv'in filename:
            self.trans = Transactions_old(pd.read_csv(file), None)
        elif '.xlsx' in filename:
            self.budget = Budget_old(pd.read_excel(file, "Budget Amounts"))
            self.trans = Transactions_old(pd.read_excel(file, "Transactions"), self.budget.budget_info)

    def get_trans_dataframe(self):
        return self.trans

    def get_budgets_dataframe(self):
        return self.budget

class Budget_old(object):
    def __init__(self, df):
 # load transactions into model.Transactions
    # col   value
    # 1     date
    # 2 - 6 concatenate into a list
    # 7     category
    # 8 - 14 concatenate with earlier concatenated list

        self.budget_amounts = df

       # these are the attributes that model is looking for...
        self.budget_info = {}  # contains budget meta info, super_category, annual and monthly budget amounts by category
        #
        # build self.budget_info
        #
        # budget_amounts is a dataframe
        super_category = ""
        total_annual_budget = 0
        for index, row in self.budget_amounts.iterrows():
            if not pd.isnull(row["Super Category"]): super_category = row["Super Category"]
            if not pd.isnull(row["Category"]):
                self.budget_info[row["Category"]] = [super_category, row["Annual"], row["Annual"] / 12]
                total_annual_budget += row["Annual"]
        self.budget_info["Total"] = ["Spending", total_annual_budget, total_annual_budget / 12]


class Transactions_old(object):
    def __init__(self, df, budget_info):
        self.actuals = df
        self.budget_info = budget_info
        #
        # build self.accumulated_spending_by_category_by_month and self.transactions
        #
        self.transactions_labels = []
        self.transactions = {}
        self.ignore_list = ["Hide from Budgets & Trends", "loan to sage", "Finance Charge", "ATM Fee",
                            "Transfer", "Inheritance", "utepils investment", "Misc Expenses", "Betsy Estate Work",
                            "misc", "Investment", "Credit Card Rewards", "Interest Income", "Paycheck", "Misc. Income"]

        # dict of transaction data by super category by category by yr by month
        self.accumulated_spending_by_category_by_month = {}
        # dict of actual spending amount by super category by category by yr by month
        self.accumulated_spending_by_category = {}
        # dict of list of amounts by super_category by category:  this dict is used to generate budget info by all the levels of the dict...
        #  - spending in last full 12 months against budget [budgetted amount, amount spend, delta]
        #  - spending in current year against budget
        #  - spending in last full month
        #  - spending in current partial month
        self.accumulated_spending_by_super_category = {} # sames as above but for super category
        self.accumulated_spending_for_past_year = {} # same as above but grand total for the past 12 full months
        # list of interesting outliers
        self.alerts = []

        current_datetime = datetime.datetime.now()
        current_year = current_datetime.year
        current_month = current_datetime.month
        start_date = datetime.datetime(current_year-1, current_month-1, 1)
        self.actuals['Date'] = pd.to_datetime(self.actuals['Date'])
        print(self.actuals)
        for index, row in self.actuals.iterrows():
            # read row and only columns we care about: Date, Amount, Transaction Type, Category
            # need to sum or subtract amounts within a category for actuals within period
            # first figure out the period this transaction fits within
            mnth = row["Date"].month
            mnth1 = str(mnth) if len(str(mnth)) == 2 else "0" + str(mnth)
            yr = row["Date"].year
            category = row["Category"]
            if category not in self.ignore_list and row["Date"] >= start_date :
                try:
                    super_category = self.budget_info[category][0]
                    if super_category not in self.accumulated_spending_by_category_by_month:
                        self.accumulated_spending_by_category_by_month[super_category] = {}
                        self.transactions[super_category] = {}
                    if category not in self.accumulated_spending_by_category_by_month[super_category]:
                        self.accumulated_spending_by_category_by_month[super_category][category] = {}
                        self.transactions[super_category][category] = {}
                    if yr not in self.accumulated_spending_by_category_by_month[super_category][category]:
                        self.accumulated_spending_by_category_by_month[super_category][category][yr] = {}
                        self.transactions[super_category][category][yr] = {}
                    tran_amount = row["Amount"] if row["Transaction Type"] == "debit" else row["Amount"] * -1
                    if mnth not in self.accumulated_spending_by_category_by_month[super_category][category][yr]:
                        self.accumulated_spending_by_category_by_month[super_category][category][yr][mnth] = 0
                        self.transactions[super_category][category][yr][mnth] = []
                    self.accumulated_spending_by_category_by_month[super_category][category][yr][mnth] += tran_amount
                    tran_type_text = "(+)" if row["Transaction Type"] == "credit" else ""
                    readable_row = str(row["Date"].day) + " | " + str(row["Description"]) + " | " + str(row["Amount"]) + " " + tran_type_text
                    self.transactions[super_category][category][yr][mnth].append( readable_row )
                except KeyError:
 #                   print("KeyError: " + str(row) )
                    pass
            print(self.transactions)
        #
        # build self.accumulated_spending_by_category
        #
        for supcat, supcat_dict in self.accumulated_spending_by_category_by_month.items():
            if supcat not in self.accumulated_spending_by_category: self.accumulated_spending_by_category[supcat] = {}
            for cat, cat_dict in supcat_dict.items():
                cat_total_spending = 0
                cat_current_year_spending = 0
                cat_last_full_month_spending = 0
                cat_current_month_spending = 0
                for yr, yr_dict in cat_dict.items():
                    for mnth, mnthly_value in yr_dict.items():
                        cat_total_spending += mnthly_value
                        if yr == current_year:
                            cat_current_year_spending += mnthly_value
                            if mnth == current_month - 1: cat_last_full_month_spending += mnthly_value  # there is a problem when the current month is January
                            elif mnth == current_month: cat_current_month_spending += mnthly_value
                try:
                    self.accumulated_spending_by_category[supcat][cat] = [
                        [self.budget_info[cat][1], cat_total_spending, cat_total_spending / self.budget_info[cat][1] * 100],
                        [self.budget_info[cat][1]*(current_month-1)/12, cat_current_year_spending, cat_current_year_spending/(self.budget_info[cat][1]*(current_month - 1)/12)*100],
                        [self.budget_info[cat][2], cat_last_full_month_spending, cat_last_full_month_spending / self.budget_info[cat][2] * 100 ],
                        [self.budget_info[cat][2], cat_current_month_spending, cat_current_month_spending / self.budget_info[cat][2] * 100 ] ]
                except ZeroDivisionError:
                    print( "HHHAAAA" )

        #
        # buildself.accumulated_spending_by_super_category
        #
        for supcat, supcat_dict in self.accumulated_spending_by_category.items():
            if supcat not in self.accumulated_spending_by_super_category: self.accumulated_spending_by_super_category[supcat] = [[0, 0, 0], [0, 0, 0, 0], [0, 0, 0], [0, 0, 0]]
            for cat, summary_list in supcat_dict.items():
                for i in range(len(summary_list)):
                    self.accumulated_spending_by_super_category[supcat][i][0] += summary_list[i][0]
                    self.accumulated_spending_by_super_category[supcat][i][1] += summary_list[i][1]
            for item in self.accumulated_spending_by_super_category[supcat]:
                item[2] = item[1] / item[0] * 100

        #
        # buildself.accumulated_spending_for_past_year
        #
        self.accumulated_spending_for_past_year = [[0, 0, 0], [0, 0, 0, 0], [0, 0, 0], [0, 0, 0]]
        for supcat, supcat_dict in self.accumulated_spending_by_category.items():
            for cat, summary_list in supcat_dict.items():
                for i in range(len(summary_list)):
                    self.accumulated_spending_for_past_year[i][0] += summary_list[i][0]
                    self.accumulated_spending_for_past_year[i][1] += summary_list[i][1]
            for item in self.accumulated_spending_for_past_year:
                item[2] = item[1] / item[0] * 100

        #
        # build alerts
        #
        for supcat, supcat_dict in self.accumulated_spending_by_category_by_month.items():
            for cat, cat_dict in supcat_dict.items():
                for yr, yr_dict in cat_dict.items():
                    for mnth, mnthly_value in yr_dict.items():
                        if mnthly_value  > self.budget_info[cat][2] * 10: self.alerts.append( cat + " for " + str(yr) + ":" + str(mnth) + " " + str(mnthly_value) + " is over 10 times budget (" + str(self.budget_info[cat][2]) + ")!")


