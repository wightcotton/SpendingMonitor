import pandas as pd
import numpy as np

class Category_Whisperer(object):
    def __init__(self, full_df):
        self.df = full_df
        self.cat_info = {}

    def create_cat_info(self):
        # category dict of useful info about category
        for cat in self.df.Category.unique():
            self.cat_info[cat] = {}
            self.cat_info[cat]['category_type'] = self.get_category_type(cat)
            self.cat_info[cat]['monthly_budget'] = self.get_monthly_budget(cat)

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

    def get_montly_budget(self, cat):
        return self.df.loc[self.df['Category'] == cat]['Amount'].mean()
        # somehow take advantage of df.groupby("Category")['Amount'].mean()?
        # would return a df with an entery for each category with averaged amounts?
        # might represent a more effecient approach?