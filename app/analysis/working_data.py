import pandas as pd
from datetime import date
import xlrd
import numpy as np
import math
from app.analysis.wrangle_categories import Category_Whisperer

class DataObjectFactory(object):
    def __init__(self, filename, file):
        self.trans = None
        self.budget = None
        self.uploaded_filename = filename
        if '.csv' in filename:
            self.trans = Transactions(pd.read_csv(file))
        elif '.xlsx' in filename:
            self.budget = Budget(pd.read_excel(file, "Budget Amounts"))
            self.trans = Transactions(pd.read_excel(file, "Transactions"))

    def get_trans(self):
        return self.trans

    def get_budgets(self):
        return self.budget


class Budget(object):
    def __init__(self, budget_file):
        self.budget_structure = {}

class Transactions(object):
    def __init__(self, incoming_df):
        self.trans_df = incoming_df
        self.instantiate_constants()
        self.transform_df()
        self.cat_worker = Category_Whisperer(self.trans_df)
        self.secondary_transform_df()
        self.spending_df = self.trans_df.loc[self.trans_df["Account_Type"] == 'Expense'].copy()

    def instantiate_constants(self):
        self.display_columns =["Category", "Date", "Description", "Amount"] # eventually this will be a user setting
        current_month = date.today().month
        self.current_qtr = math.ceil(current_month/3.)
        self.last_qtr = self.current_qtr - 1
        self.qtr_year = date.today().year
        if self.current_qtr == 1:
            self.last_qtr = 4
            self.qtr_year -= 1
        self.last_month = date.today().month - 1
        if self.last_month == 0:
            self.last_month = 12

    def transform_df(self):
        self.trans_df['Date'] = pd.to_datetime(self.trans_df['Date'])
        self.trans_df['Year'] = self.trans_df["Date"].map(lambda y: int(y.strftime('%Y'))) # year as 4 digit int
        self.trans_df['Qtr'] = self.trans_df['Date'].dt.quarter # int 1, 2, 3, 4
        self.trans_df['Month'] = self.trans_df["Date"].dt.strftime('%B') # text month name
        self.trans_df['MthYr'] = self.trans_df['Month'] + self.trans_df['Year'].astype(str)
        self.trans_df['Month_as_dec'] = self.trans_df['Date'].map(lambda m: int(m.strftime('%m'))) # as 2 digit int
        # orient amounts toward spending - what is spend is a positive number
        self.trans_df["normalizer"] = [1 if x == 'debit' else -1 for x in self.trans_df["Transaction Type"]]
        self.trans_df['Amount'] = self.trans_df['Amount'] * self.trans_df['normalizer']

    def secondary_transform_df(self):
        self.trans_df['Account_Type'] = self.trans_df['Category'].map(lambda c: self.cat_worker.get_category_type(c))
        self.trans_df['Category_Budget'] = self.trans_df['Category'].map(lambda c: self.cat_worker.get_montly_budget(c))

    def get_all_categories(self):
        return sorted(self.trans_df.Category.unique())

    def get_all_months(self):
        return self.trans_df.Month.unique()

    def get_all_years(self):
        return sorted(self.trans_df.Year.unique())

    def get_trans_full(self):
        return [self.trans_df, self.trans_df["Amount"].sum()]

    def get_last_12_months_info(self):
        # get all spending trans for the past 12 months
        temp_df = self.spending_df.loc[((self.spending_df['Month_as_dec'] < date.today().month) & (self.spending_df["Year"] == date.today().year))
                             | ((self.spending_df["Year"] == date.today().year - 1)
                                & (self.spending_df['Month_as_dec'] >= date.today().month))]
        total_spending = temp_df['Amount'].sum()
        number_spending_entries = temp_df['Amount'].count()
        budget = self.get_annual_budget()
        percent_of_budget = total_spending / budget *100
        return ["last 12 full months", total_spending, budget, percent_of_budget ]

    def get_last_year_info(self):
        # get all spending trans for last calendar year
        temp_df = self.spending_df.loc[self.spending_df['Year'] == date.today().year-1]
        total_spending = temp_df['Amount'].sum()
        budget = self.get_annual_budget()
        percent_budget = total_spending / budget * 100
        return ['for last year', total_spending, budget, percent_budget]

    def get_this_year_info(self):
        # get spending so far this year
        temp_df = self.spending_df.loc[self.spending_df["Year"] == date.today().year]
        total_spending = temp_df["Amount"].sum()
        budget = self.get_annual_budget()
        percent_budget = total_spending / budget * 100
        return ['so far this year', total_spending, budget, percent_budget]

    def get_last_qtr_info(self):
        # get spending for last quarter
        temp_df = self.spending_df.loc[((self.spending_df['Year'] == self.qtr_year)
                                        & (self.spending_df["Qtr"] == self.last_qtr))]
        total_spending = temp_df["Amount"].sum()
        budget = self.get_annual_budget() / 4
        percent_budget = total_spending / budget * 100
        return ['for last quarter', total_spending, budget, percent_budget]

    def get_this_qtr_info(self):
        # get spending for last quarter
        temp_df = self.spending_df.loc[((self.spending_df['Year'] == date.today().year)
                                        & (self.spending_df["Qtr"] == self.current_qtr))]
        total_spending = temp_df["Amount"].sum()
        budget = self.get_annual_budget() / 4
        percent_budget = total_spending / budget * 100
        return ['so far this quarter', total_spending, budget, percent_budget]

    def get_last_month_info(self):
        # get spending for last month
        temp_yr = date.today().year if self.last_month < 12 else date.today().year - 1
        temp_df = self.spending_df.loc[((self.spending_df['Year'] == temp_yr)
                                        & (self.spending_df["Month_as_dec"] == self.last_month))]
        total_spending = temp_df["Amount"].sum()
        budget = self.get_annual_budget() / 12
        percent_budget = total_spending / budget * 100
        return ['for last month', total_spending, budget, percent_budget]

    def get_this_month_info(self):
        # get spending for last quarter
        temp_df = self.spending_df.loc[((self.spending_df['Year'] == date.today().year)
                                        & (self.spending_df["Month_as_dec"] == date.today().month))]
        total_spending = temp_df["Amount"].sum()
        budget = self.get_annual_budget() / 12
        percent_budget = total_spending / budget * 100
        return ['so far this month', total_spending, budget, percent_budget]

    def get_annual_budget(self):
        # TODO derive number of months actually available in dataframe...need to worry about missing months?
        # just count number of distinct year month combos with some transactions?
        number_of_months_in_data = len(self.spending_df['MthYr'].unique())
        total_spending = self.spending_df['Amount'].sum()
        return total_spending / number_of_months_in_data * 12

    def get_category_spending_for_month(self, cat, m, y):
        ret = []
        ret.append(self.spending_df.loc[(self.spending_df["Category"] == cat) &
                                     (self.spending_df["Month"] == m) &
                                     (self.spending_df["Year"] == y),
                                     self.display_columns])
        ret.append(ret[0]["Amount"].sum())
        return ret


    def get_cat_spending_by_qtr_and_year(self):
        ret = []
        return (self.trans_df.groupby(["Category", "Year", "Qtr"])["Amount"].sum())

    def get_cat_spending_by_month_qtr_and_year(self):
        ret = []
        return(self.trans_df.groupby(["Category", "Year", "Month"])["Amount"].sum())

    def foobar(self):
        return(self.get_cat_spending_by_month_and_year() + self.get_cat_spending_by_year())
        #return self.trans_df.loc[self.trans_df[(self.trans_df["Category"] == cat) & (self.trans_df["Month"] == m), :]]

        # self.trans_df.Category.unique().to_frame()
        # selecting columns - df.loc[:, [list of column names]
        # minimum - df.loc[:, [list of column names].min() or max(), count(), avg(), sum()
        # selection rows - df.loc[df.[column_name] >= 1000000
        # group by - df.groupby([column names]).sum()
        # self.trans_df.column.unique() returns distinct values in column

