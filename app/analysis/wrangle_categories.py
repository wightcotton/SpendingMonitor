import pandas as pd
import numpy as np

class Category_Whisperer(object):
    def __init__(self, full_df):
        self.df = full_df
        self.number_of_months_in_data = len(self.df['MthYr'].unique())
        self.cat_info_headings = []
        self.cat_info = {}
        self.create_cat_info()

    def create_cat_info(self):
        # category dict of useful info about category
        self.cat_info_headings = ['Category Type', 'Frequency', 'Monthly Budget']
        for cat in self.df.Category.unique():
            self.cat_info[cat] = [self.get_category_type(cat),
                                  self.get_spending_frequency(cat),
                                  self.get_monthly_budget(cat)]

    def get_cat_info_headings(self):
        return self.cat_info_headings

    def get_cat_info(self):
        return self.cat_info

    def get_category_type(self, cat):
        number_of_category_entries = self.df.loc[self.df['Category'] == cat]['Category'].count()
        number_of_credit_entries = self.df.loc[((self.df["Category"] ==  cat) & (self.df['Transaction Type'] == 'credit'))]['Category'].count()
        credit_entries_percent = number_of_credit_entries / number_of_category_entries
        number_of_large_entries = self.df.loc[((self.df["Category"] ==  cat) & (self.df['Amount'] > 10000 ))]['Category'].count()
        large_entries_percent = number_of_large_entries / number_of_category_entries
        if credit_entries_percent > .5:
            return 'Income'
        elif large_entries_percent > .1:
            return 'Investment'
        else:
            return 'Expense'

    def get_monthly_budget(self, cat):
        return '${:,.2f}'.format(self.df.loc[self.df['Category'] == cat]['Amount'].mean())
        # somehow take advantage of df.groupby("Category")['Amount'].mean()?
        # would return a df with an entery for each category with averaged amounts?
        # might represent a more effecient approach?

    def get_spending_frequency(self, cat):
        number_of_items = self.df.loc[self.df['Category'] == cat]['Amount'].count()
        # count items by month - regular equals 3 0r 4 per month?
        frequency_of_items = number_of_items / self.number_of_months_in_data
        if frequency_of_items > 3.5:
            return 'weekly'
        elif frequency_of_items > .85:
            return 'monthly'
        elif frequency_of_items > .2:
            return 'quarterly'
        else:
            return 'sporadically'
