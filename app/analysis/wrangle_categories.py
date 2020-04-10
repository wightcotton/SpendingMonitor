import pandas as pd
import numpy as np

class Category_Whisperer(object):
    def __init__(self, transactions):
        self.trans = transactions
        self.cat_info_headings = []
        self.cat_info = {}
        self.create_cat_info()

    def create_cat_info(self):
        # category dict of useful info about category
        self.cat_info_headings = ['Category Type', 'Frequency', 'Monthly Budget']
        for cat in self.df.Category.unique():
            self.cat_info[cat] = [self.get_category_type(cat),
                                  self.trans.get_spending_frequency(cat),
                                  self.trans.get_monthly_budget(cat)]

    def get_cat_info_headings(self):
        return self.cat_info_headings

    def get_cat_info(self):
        return self.cat_info

    def get_category_type(self, cat):
        number_of_category_entries = self.trans.get_number_of_entries(cat)
        number_of_credit_entries = self.trans.get_number_of_credit_entries(cat)
        credit_entries_percent = number_of_credit_entries / number_of_category_entries
        number_of_large_entries = self.trans.get_number_of_amounts_over(cat, 1000)
        large_entries_percent = number_of_large_entries / number_of_category_entries
        if credit_entries_percent > .5:
            return 'Income'
        elif large_entries_percent > .1:
            return 'Investment'
        else:
            return 'Expense'


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
