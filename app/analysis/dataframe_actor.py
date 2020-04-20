from io import BytesIO

import pandas as pd
import numpy as np
from datetime import date
import math
from app.analysis.working_data import File_Helper


class DataFrameFactory(object):
    def __init__(self, user_id):
        self.file_info = File_Helper().get_file_info(user_id)
        if self.file_info is not None:
            if '.csv' in self.file_info[0]:
                self.trans_df = pd.read_csv(BytesIO(self.file_info[2]))
            elif '.xlsx' in self.file_info[0]:
                self.trans_df = pd.read_excel(BytesIO(self.file_info[2]), "Transactions")
            else:
                raise Exception("unknown file type")
            self.trans_df_actor = DataFrameActor(self.trans_df)

    def get_file_info(self):
        # just return file name and datetime
        return self.file_info[0:2]

    def get_all_trans_actor(self):
        return self.trans_df_actor


class DataFrameActor(object):
    # all actions against df happen here and in children
    def __init__(self, df):
        self.df = df
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.df['Year'] = self.df['Date'].map(lambda d: d.strftime('%Y'))
        self.df['Qtr'] = self.df['Date'].dt.quarter  # int 1, 2, 3, 4
        self.df['Month'] = self.df["Date"].dt.strftime('%B')  # text month name
        self.df['MthYr'] = self.df['Month'] + self.df['Year'].astype(str)
        self.df['Month_as_dec'] = self.df['Date'].map(lambda m: int(m.strftime('%m')))  # as 2 digit int
        # orient amounts toward spending - what is spend is a positive number
        self.df["normalizer"] = [1 if x == 'debit' else -1 for x in self.df["Transaction Type"]]
        self.df['Amount'] = self.df['Amount'] * self.df['normalizer']
        self.number_of_entries = self.df.count()['Amount']  # returns int64
        self.total_amount = self.df["Amount"].sum()  # returns float64
        self.months = self.df.Month.unique().tolist()  # returns Series
        self.years = sorted(self.df['Year'].unique())  # returns list
        self.number_of_months = len(self.df['MthYr'].unique())  # returns int
        self.categories = self.df['Category'].unique().tolist()  # returns list
        self.entries_by_cat = self.df.groupby(['Category'])  # returns groupby object
        self.category_info_df = self.create_category_info_df()
        #        for index, value in self.df.groupby(['Year', 'Month', 'Category'])['Amount'].sum().iteritems():
        #            print( str(index[0]) + '; ' + str(value))
        self.entries_by_cat.sum()
        self.number_of_entries_by_cat = None
        self.total_by_cat = None
        self.mean_by_cat = None
        self.credit_entries = None
        self.number_of_credit_entries = None
        self.entries_with_amounts_over_by_cat = None
        self.number_of_entries_with_amounts_over = None
        self.last_12_months = None
        self.last_12_months_total = None
        self.last_12_months_entries = None
        self.last_year = None
        self.last_year_total = None
        self.last_year_entries = None
        self.this_year = None
        self.this_year_total = None
        self.this_year_entries = None
        self.last_qtr = None
        self.last_qtr_total = None
        self.this_qtr = None
        self.this_qtr_total = None
        self.last_month = None
        self.last_month_total = None
        self.this_month = None
        self.this_month_total = None

        # need to expose these tolerances to allow for analysis within web site to figure out best levels to discriminate among categories
        # expense categories have a majority of entries where money goes out (for mint, transaction type is debit)
        # income categories have a majority of entries where money come in (for mint, transaction type is credit)
        # investment categories have a ??
        # continuous categories have entries at least once a month
        # sporadic categories have entries less than once a month up to once a half year
        # rare categories have entries that happen less than once a half year
        # consistent means the entry amounts are within one standard deviation of one another
        # variable are not consistent
        # categories must be in one and only one category
        # lists of these kinds of categories must be available to create subset of full dataframe based on those categories
        # 1. create a dataframe containing a row for each category (combine 1 and 2?)
        # 2. create columns for summarized base info from category entries that can be used to determine these key attributes of categories
        # 3. create indicator columns that can be used to determine the kind of category as functions of the summarized base info
        #   and derive stats about categories
        # 4. get lists conntaining appropriate categories from some kind of dataframe operation to get the subset of categories in a list

    def create_category_info_df(self):
        temp_category_group_obj = self.df.groupby(['Category'])['Amount']
        entries_count_by_category_series = temp_category_group_obj.count()
        entries_amount_total_category_series = temp_category_group_obj.sum()
        debit_entries_count_series = self.df.loc[self.df['Transaction Type'] == 'debit'].groupby(['Category'])['Amount'
        ].count()
        large_entries_count_series = self.df.loc[self.df['Amount'] > 7500].groupby(['Category'])['Amount'].count()
        temp_df = pd.concat([entries_count_by_category_series,
                             entries_amount_total_category_series,
                             large_entries_count_series,
                             debit_entries_count_series],
                            axis=1)
        temp_df.set_axis(['count', 'sum', 'large', 'debit'], axis=1, inplace=True)
        temp_df['large_percent'] = temp_df['large'] / temp_df['count']
        temp_df['debit_percent'] = temp_df['debit'] / temp_df['count']
        temp_df['category_type'] = temp_df['debit_percent'].map(lambda cp: 'expense' if cp > .6 else 'income')
        temp_df['frequency'] = temp_df['count'].map(
            lambda c: self.determine_frequency_descriptor(self.number_of_months, c))
        return temp_df

    def get_category_types(self):
        return ['expense', 'income', 'investment']

    def determine_frequency_descriptor(self, total_number_of_months_in_df, cat_entries):
        naive_actual_frequency = cat_entries / total_number_of_months_in_df
        # value of 1 equals one cat entry per month
        # value of 4 equals one per week
        if cat_entries < 5:
            return 'rare'
        elif naive_actual_frequency > 4:
            return 'weekly'
        elif naive_actual_frequency > .9:
            return 'monthly'
        elif naive_actual_frequency > .6:
            return 'quarterly'
        else:
            return 'sporadic'

    def get_spending_category_frequencies(self):
        return ['all_spending', 'weekly', 'monthly', 'quarterly', 'sporadic', 'rare']

    def get_subset_df(self, cat_type, frequency):
        if cat_type is None and frequency is None:
            return self.df
        if cat_type == 'expense':
            if frequency == 'all_spending':  # get all categories for that type
                selected_categories = self.category_info_df.loc[(self.category_info_df['category_type'] == cat_type)].index.tolist()
            else:
                # need to include check to see if frequency in spending categories list
                selected_categories = self.category_info_df.loc[((self.category_info_df['category_type'] == cat_type)
                                                                 & (self.category_info_df[
                                                                        'frequency'] == frequency))].index.tolist()
        elif cat_type == 'income':
            pass
        elif cat_type == 'investment':
            pass
        else:
            raise Exception('no such category type:' + cat_type)
        return self.df.loc[self.df['Category'].isin(selected_categories)]

    def get_entries_by_cat(self):
        # returns a dataframe grouped by Category
        if self.entries_by_cat is None:
            self.entries_by_cat = self.df.groupby(['Category'])
        return self.entries_by_cat

    def get_number_of_entries_by_cat(self):
        # returns an int
        if self.number_of_entries_by_cat is None:
            self.number_of_entries_by_cat = self.get_entries_by_cat()['Amount'].count()
        return self.number_of_entries_by_cat

    def get_total_by_cat(self, df):
        # returns an series?
        if self.total_by_cat is None:
            self.total_by_cat = self.get_entries_by_cat().sum()
        return self.total_by_cat

    def get_mean_by_cat(self, df):
        # returns a series keyed by category of the mean size of amounts
        if self.mean_by_cat is None:
            self.mean_by_cat = self.get_entries_by_cat().mean()
        return self.mean_by_cat

    # summary info is [[name of summary group, [included category list], [[last year summary], [last 12 months], etc]]

    def get_summary_info(self):
        return [['All Transaction', self.df.index.tolist(), self.get_summary_info_for(self.df)]]

    def get_summary_spending_info(self):
        # return a list of lists: [['Total' ['last year', spending, budget, percent spent],
        #                                 ['last 12', spending, budget, percent spent],
        #                                           ...                               ],
        #                          ['Weekly' ['last year', spending, budget, percent spent]]]
        ret = []
        frequencies = self.get_spending_category_frequencies()
        for freq in frequencies:
            temp_df = self.get_subset_df('expense', freq)
            ret.append([freq, len(temp_df['Category'].unique().tolist()), self.get_summary_info_for(temp_df)])
        return ret


    def get_summary_info_for(self, temp_df):
        # return list of lists containing summary info for last year, last 12 months, this year, etc...
        ret = []
        # ['all trans', 'for last year', 'this year', 'last qtr', 'this qtr', 'last month', 'this month']
        ret.append(self.get_summary_detail('all trans', temp_df))
        ret.append(self.get_summary_detail('last year', temp_df.loc[temp_df['Year'] == str(date.today().year - 1)]))
        ret.append(self.get_summary_detail('last 12 months', temp_df.loc[
            ((temp_df['Month_as_dec'] < date.today().month) & (temp_df["Year"] == str(date.today().year)))
            | ((temp_df["Year"] == date.today().year - 1) & (temp_df['Month_as_dec'] >= date.today().month))]))
        ret.append(self.get_summary_detail('this year', temp_df.loc[temp_df["Year"] == str(date.today().year)] ))

        current_qtr = math.ceil(date.today().month / 3.)
        temp_yr = date.today().year - 1 if current_qtr == 1 else date.today().year
        temp_qtr = 4 if current_qtr == 1 else current_qtr - 1
        ret.append(self.get_summary_detail('last quarter', temp_df.loc[((temp_df['Year'] == str(temp_yr)) & (temp_df["Qtr"] == temp_qtr))] ))
        ret.append(self.get_summary_detail('this quarter', temp_df.loc[((temp_df['Year'] == str(date.today().year)) & (temp_df["Qtr"] == current_qtr))]))
        temp_yr = date.today().year - 1 if date.today().month == 1 else date.today().year
        temp_month = 12 if date.today().month == 1 else date.today().month - 1
        ret.append(self.get_summary_detail('last month', temp_df.loc[((self.df['Year'] == str(temp_yr)) & (temp_df["Month_as_dec"] == temp_month))]))
        ret.append(self.get_summary_detail('this month', temp_df.loc[((self.df['Year'] == str(date.today().year)) & (temp_df["Month_as_dec"] == date.today().month))]))
        return ret

    def get_summary_detail(self, name, detail_df):
        monthly_budget = detail_df['Amount'].sum() / self.number_of_months
        total_spending = detail_df['Amount'].sum()
        percent_budget = total_spending / (monthly_budget * 12) * 100
        return [name, detail_df['Amount'].count(),
                    '${:,.2f}'.format(total_spending),
                    '${:,.2f}'.format(monthly_budget * 12),
                    '{:,.2f}%'.format(percent_budget)]


class SpendingDFActor(DataFrameActor):
    def __init__(self, df):
        super(df)

    # results based on analysis of basic facts
    def get_monthly_budget(self, cat):
        # naive budget is average of spending by cat divided by number of months
        return self.get_total_by_cat()['Amount'][cat] / self.get_number_of_months()

    def get_monthly_frequency(self, cat):
        # mean of the number of entries for a category by month
        return self.get_number_of_entries_by_cat()['Amount'][cat] / self.get_number_of_months()

    def get_ave_entry_spending_amount(self, cat):
        # the average amount spent per entry in a category
        return self.get_total_by_cat()['Amount'][cat] / self.get_number_of_entries_by_cat()['Amount'][cat]
