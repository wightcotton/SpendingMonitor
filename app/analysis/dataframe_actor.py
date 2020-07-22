import pandas as pd
import numpy as np
from datetime import date, datetime
import math
from flask_login import current_user
from config import UserConfig

from app.database_access.category_state_access import CategoryStateAccess


# from sklearn.cluster import KMeans

class DataFrameActor(object):
    #
    def __init__(self, df):

        def det_last_12_months(row):
            return ((row['Month_as_dec'] < date.today().month) & (row["Year"] == str(date.today().year))) | \
                   ((row["Year"] == str(date.today().year - 1)) & (row['Month_as_dec'] >= date.today().month))

        def det_last_qtr(row):
            return (row['Year'] == str(temp_yr)) & (row["Qtr"] == temp_qtr)

        def det_this_qtr(row):
            return (row['Year'] == str(date.today().year)) & (row["Qtr"] == current_qtr)

        def det_last_month(row):
            return (row['Year'] == str(temp_yr)) & (row["Month_as_dec"] == temp_month)

        def det_this_month(row):
            return (row['Year'] == str(date.today().year)) & (row["Month_as_dec"] == date.today().month)

        self.df = df
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.df['Year'] = self.df['Date'].map(lambda d: d.strftime('%Y'))
        self.df['Qtr'] = self.df['Date'].dt.quarter  # int 1, 2, 3, 4
        self.df['Month'] = self.df["Date"].dt.strftime('%B')  # text month name
        self.df['MthYr'] = self.df['Month'] + self.df['Year'].astype(str)
        self.df['Month_as_dec'] = self.df['Date'].map(lambda m: int(m.strftime('%m')))  # as 2 digit int
        current_qtr = math.ceil(date.today().month / 3.)
        temp_yr = date.today().year - 1 if current_qtr == 1 else date.today().year
        temp_qtr = 4 if current_qtr == 1 else current_qtr - 1
        temp_month = 12 if date.today().month == 1 else date.today().month - 1
        self.df['last year'] = self.df['Year'].map(lambda d:  d == str(date.today().year - 1))
        self.df['last 12 months'] = self.df.apply(det_last_12_months, axis=1)
        self.df['this year'] = self.df['Year'].map(lambda d: d == str(date.today().year))
        self.df['last quarter'] = self.df.apply(det_last_qtr, axis=1)
        self.df['this quarter'] = self.df.apply(det_this_qtr, axis=1)
        self.df['last month'] = self.df.apply(det_last_month, axis=1)
        self.df['this month'] = self.df.apply(det_this_month, axis=1)
        # orient amounts toward spending - what is spend is a positive number
        self.df["normalizer"] = [1 if x == 'debit' else -1 for x in self.df["Transaction Type"]]
        self.df['Amount'] = self.df['Amount'] * self.df['normalizer']
        self.df['Time_between_items'] = self.df.groupby('Category')['Date'].diff() / np.timedelta64(1, 'D')

    def get_subset_df(self, category_list=None, override_ignore=False):
        if category_list is None:
            category_list = self.get_unique_categories().tolist()
        if not override_ignore:
            for item in CategoryStateAccess(current_user.id).get_categories_current_state_for('ignore'):
                try:
                    category_list.remove(item)
                except ValueError:
                    pass
        return self.df.loc[self.df['Category'].isin(category_list)]

    def get_unique_categories(self):
        return self.df['Category'].unique()

    def get_categories_for(self, summary_tag=None):
        return self.df.loc[self.df[summary_tag]]['Category'].unique()

    def get_summary_tag_info(self, summary_tag, categories=None):
        ret_amount = 0
        ret_tran_count = 0
        ret_category_count = 0
        if categories:
            for cat in categories:
                items = self.df.loc[(self.df[summary_tag]) & (self.df['Category'] == cat)]['Amount'].count()
                if items > 0:
                    ret_amount += self.df.loc[(self.df[summary_tag]) & (self.df['Category'] == cat)]['Amount'].sum()
                    ret_tran_count += items
                    ret_category_count += 1
        else:
            ret_amount = self.df.loc[self.df[summary_tag]]['Amount'].sum()
            ret_tran_count = self.df.loc[self.df[summary_tag]]['Amount'].count()
            ret_category_count = len(self.df.loc[self.df[summary_tag]]['Category'].unique().tolist())
        return [ret_amount, ret_tran_count, ret_category_count]

    # INFO REQUESTS

    def get_items_for(self, category=None, summary_tag=None):
        if category:
            # gets all items for a category grouped by year and month
            return self.get_subset_df(category_list=[category], override_ignore=True)[
                self.get_detail_item_display_columns()]
        elif summary_tag:
            return self.df.loc[self.df[summary_tag], self.get_detail_item_display_columns()]


    def get_recent_items_for(self, category_list):
        # recent is this month and last month
        temp_df = self.get_subset_df(category_list)
        this_year = str(date.today().year)
        this_month = date.today().month
        # need to check if current month is january, then previous month is last year december
        prev_month = DataFrameActor.get_prev_month_and_year()[0]
        prev_year = DataFrameActor.get_prev_month_and_year()[1]
        return temp_df.loc[((temp_df["Year"] == this_year) & (temp_df["Month_as_dec"] == this_month)) |
                           ((temp_df["Year"] == prev_year) & (temp_df["Month_as_dec"] == prev_month)),
                           self.get_detail_item_display_columns()].to_html()

    # helpers
    @staticmethod
    def get_prev_month_and_year():
        this_year = str(date.today().year)
        this_month = date.today().month
        prev_month = 12 if this_month == 1 else this_month - 1
        year_of_prev_month = this_year - 1 if this_month == 12 else this_year
        return prev_month, year_of_prev_month

    # end INFO REQUESTS
    #    def get_category_details_for(self, frequency=None):
    #       return self.get_cat_summary_spending_info(self.cat_df_actor.get_categories('expense', frequency))

    #    def get_category_detail(self, category=None):
    #        return self.get_cat_summary_spending_info([category])

    def get_detail_item_display_columns(self):
        return ["Date", "Category", "Amount", "Description"]  # eventually this will be a user setting








