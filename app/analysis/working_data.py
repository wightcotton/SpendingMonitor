import pandas as pd
from datetime import date
import xlrd
import numpy as np
import math
from app.analysis.wrangle_categories import Category_Whisperer
from app.models import UploadedFile
from app import db
from io import BytesIO


class File_Helper(object):
    def __init__(self):
        pass

    def set_file(self, filename, data, user_id):
        uploaded_file = UploadedFile(filename=filename, data=data, user_id=user_id)
        db.session.add(uploaded_file)
        db.session.commit()

    def get_file_info(self, user_id):
        file = UploadedFile.query.filter_by(user_id=user_id).order_by(UploadedFile.timestamp.desc()).first()
        file_info = None
        if file is not None:
            file_info = [file.filename, file.timestamp, file.data]
        return file_info


class Transactions(object):
    def __init__(self, file):
        self.populate_dataframe(file)
        self.instantiate_constants()
        self.transform_df()
        self.secondary_transform_df()
        self.spending_df = self.spending_df = self.trans_df.loc[self.trans_df['Account_Type'] == 'Expense']
        self.spending_cat_info_headings = ['Monthly Items', 'Ave Amount', 'Frequency', 'Monthly Budget']
        self.number_of_spending_months = None
        self.spending_entries_by_cat = None
        self.count_of_spending_entries_by_cat = None
        self.mean_spending_by_cat = None
        self.total_spending_by_cat = None
        self.spending_cat_info = self.create_spending_cat_info()

    # init methods
    def populate_dataframe(self, file):
        if '.csv' in file.filename:
            self.trans_df = pd.read_csv(BytesIO(file.data))
        elif '.xlsx' in file.filename:
            self.trans_df = pd.read_excel(BytesIO(file.data), "Transactions")

    def instantiate_constants(self):
        self.display_columns = ["Category", "Date", "Description", "Amount"]  # eventually this will be a user setting
        current_month = date.today().month
        self.current_qtr = math.ceil(current_month / 3.)
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
        self.trans_df['Year'] = self.trans_df["Date"].map(lambda y: int(y.strftime('%Y')))  # year as 4 digit int
        self.trans_df['Qtr'] = self.trans_df['Date'].dt.quarter  # int 1, 2, 3, 4
        self.trans_df['Month'] = self.trans_df["Date"].dt.strftime('%B')  # text month name
        self.trans_df['MthYr'] = self.trans_df['Month'] + self.trans_df['Year'].astype(str)
        self.trans_df['Month_as_dec'] = self.trans_df['Date'].map(lambda m: int(m.strftime('%m')))  # as 2 digit int
        # orient amounts toward spending - what is spend is a positive number
        self.trans_df["normalizer"] = [1 if x == 'debit' else -1 for x in self.trans_df["Transaction Type"]]
        self.trans_df['Amount'] = self.trans_df['Amount'] * self.trans_df['normalizer']

    def secondary_transform_df(self):
        self.trans_df['Account_Type'] = self.trans_df['Category'].map(lambda c: self.get_category_type(c))

    # end init methods

    def get_spending_cat_info_headings(self):
        return self.spending_cat_info_headings

    def get_spending_cat_info(self):
        return self.spending_cat_info

    def get_spending_cat_info_by(self, column_number_of_detail):
        ret = []
        for key, value in self.spending_cat_info.items():
            temp = []
            temp.append(key)
            for v in value:
                temp.append(v)
            ret.append(temp)
        return sorted(ret, key=lambda x: float(x[column_number_of_detail]), reverse=True)

    def get_trans_full(self):
        return [self.trans_df, self.trans_df["Amount"].sum()]

    def get_all_categories(self):
        return sorted(self.trans_df.Category.unique())

    def get_all_months(self):
        return self.trans_df.Month.unique()

    def get_all_years(self):
        return sorted(self.trans_df.Year.unique())

    def get_number_of_all_entries(self, cat):
        return self.trans_df.loc[self.trans_df['Category'] == cat]['Category'].count()

    def get_number_of_all_credit_entries(self, cat):
        return \
            self.trans_df.loc[((self.trans_df["Category"] == cat) & (self.trans_df['Transaction Type'] == 'credit'))][
                'Category'].count()

    def get_number_of_all_amounts_over(self, cat, tolerance):
        return self.trans_df.loc[((self.trans_df["Category"] == cat) & (self.trans_df['Amount'] > tolerance))][
            'Category'].count()

    def get_category_type(self, cat):
        number_of_category_entries = self.get_number_of_all_entries(cat)
        number_of_credit_entries = self.get_number_of_all_credit_entries(cat)
        credit_entries_percent = number_of_credit_entries / number_of_category_entries
        number_of_large_entries = self.get_number_of_all_amounts_over(cat, 1000)
        large_entries_percent = number_of_large_entries / number_of_category_entries
        if credit_entries_percent > .5:
            return 'Income'
        elif large_entries_percent > .1:
            return 'Investment'
        else:
            return 'Expense'

    def get_spending_categories(self):
        return self.spending_df['Category'].unique().tolist()

    # basic spending facts, lazily initialized

    def get_number_of_spending_months(self):
        # returns an int
        if self.number_of_spending_months is None:
            self.number_of_spending_months = len(self.spending_df['MthYr'].unique())
        return self.number_of_spending_months

    def get_spending_entries_by_cat(self):
        # returns a dataframe grouped by Category
        if self.spending_entries_by_cat is None:
            self.spending_entries_by_cat = self.spending_df.groupby(['Category'])
        return self.spending_entries_by_cat

    def get_count_of_spending_entries_by_cat(self):
        if self.count_of_spending_entries_by_cat is None:
            self.count_of_spending_entries_by_cat = self.get_spending_entries_by_cat().count()
        return self.count_of_spending_entries_by_cat

    def get_total_spending_by_cat(self):
        if self.total_spending_by_cat is None:
            self.total_spending_by_cat = self.get_spending_entries_by_cat().sum()
        return self.total_spending_by_cat

    def get_mean_spending_by_cat(self):
        # returns a series keyed by category of the mean size of amounts
        if self.mean_spending_by_cat is None:
            self.mean_spending_by_cat = self.get_spending_entries_by_cat().mean()
        return self.mean_spending_by_cat

    # results based on analysis of basic facts

    def get_monthly_spending_budget(self, cat):
        # naive budget is average of spending by cat divided by number of months
        return self.get_total_spending_by_cat()['Amount'][cat] / self.get_number_of_spending_months()

    def get_monthly_spending_frequency(self, cat):
        # mean of the number of entries for a category by month
        return self.get_count_of_spending_entries_by_cat()['Amount'][cat] / self.get_number_of_spending_months()

    def get_ave_entry_spending_amount(self, cat):
        # the average amount spent per entry in a category
        return self.get_total_spending_by_cat()['Amount'][cat] / self.get_count_of_spending_entries_by_cat()['Amount'][
            cat]

    def get_spending_frequency_category(self, cat):
        # count items by month - regular equals 3 0r 4 per month?
        frequency_of_items = self.get_monthly_spending_frequency(cat)
        if frequency_of_items > 3.5:
            return 'weekly'
        elif frequency_of_items > .85:
            return 'monthly'
        elif frequency_of_items > .2:
            return 'quarterly'
        else:
            return 'sporadically'

    # summarize results into list by listing of summary items above...

    def create_spending_cat_info(self):
        # category dict of useful info about category
        ret = {}
        for cat in self.spending_df.Category.unique():
            ret[cat] = ['{:,.2f}'.format(self.get_monthly_spending_frequency(cat)),
                        '{:,.2f}'.format(self.get_ave_entry_spending_amount(cat)),
                        self.get_spending_frequency_category(cat),
                        '${:,.2f}'.format(self.get_monthly_spending_budget(cat))
                        ]
        return ret

    def get_last_12_months_info(self):
        # get all spending trans for the past 12 months
        temp_df = self.spending_df.loc[
            ((self.spending_df['Month_as_dec'] < date.today().month) & (self.spending_df["Year"] == date.today().year))
            | ((self.spending_df["Year"] == date.today().year - 1)
               & (self.spending_df['Month_as_dec'] >= date.today().month))]
        total_spending = temp_df['Amount'].sum()
        number_spending_entries = temp_df['Amount'].count()
        budget = self.get_annual_budget()
        percent_of_budget = total_spending / budget * 100
        return ["last 12 full months", total_spending, budget, percent_of_budget]

    def get_last_year_info(self):
        # get all spending trans for last calendar year
        temp_df = self.spending_df.loc[self.spending_df['Year'] == date.today().year - 1]
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
        total_spending = self.spending_df['Amount'].sum()
        return total_spending / self.get_number_of_spending_months() * 12

    def get_number_of_spending_entries(self, cat):
        return self.spending_df.loc[self.spending_df['Category'] == cat]['Category'].count()

    def get_number_of_spending_items(self, cat):
        return self.spending_df.loc[self.spending_df['Category'] == cat]['Amount'].count()

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
        return (self.trans_df.groupby(["Category", "Year", "Month"])["Amount"].sum())

    def foobar(self):
        return (self.get_cat_spending_by_month_and_year() + self.get_cat_spending_by_year())
        # return self.trans_df.loc[self.trans_df[(self.trans_df["Category"] == cat) & (self.trans_df["Month"] == m), :]]

        # self.trans_df.Category.unique().to_frame()
        # selecting columns - df.loc[:, [list of column names]
        # minimum - df.loc[:, [list of column names].min() or max(), count(), avg(), sum()
        # selection rows - df.loc[df.[column_name] >= 1000000
        # group by - df.groupby([column names]).sum()
        # self.trans_df.column.unique() returns distinct values in column
