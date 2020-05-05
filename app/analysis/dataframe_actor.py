from app.models import UploadedFile, User
from io import BytesIO
from app import db
import pandas as pd
import numpy as np
from datetime import date
import math

class File_Upload(object):
    def __init__(self, user_id):
        self.user_id = user_id
        user = User.query.filter_by(id=user_id).first()
        file = None
        if user.recent_file_id is not None:
            file = UploadedFile.query.filter_by(id=user.recent_file_id).first()  # user has uploaded file previously
        # else: # check to see of there are other uploaded files - this is a double check, shouldn't get here
        # file = UploadedFile.query.filter_by(user_id=user_id).order_by(UploadedFile.timestamp.desc()).first() # no files uploaded
        self.file_info = None
        if file is not None:
            self.file_info = [file.filename, file.uploaded_timestamp, file.data]
        self.trans_df_actor = None
        if self.file_info is not None:
            if '.csv' in self.file_info[0]:
                self.trans_df = pd.read_csv(BytesIO(self.file_info[2]))
            elif '.xlsx' in self.file_info[0]:
                self.trans_df = pd.read_excel(BytesIO(self.file_info[2]), "Transactions")
            else:
                raise Exception("unknown file type")
            self.trans_df_actor = DataFrameActor(self.trans_df)

    def add_new_file(self, file_details_list):
        uploaded_file = UploadedFile(filename=file_details_list[0],
                                     data=file_details_list[1],
                                     user_id=self.user_id)
        db.session.add(uploaded_file)
        db.session.commit()
        return uploaded_file.id

    def set_recent_file(self, list):
        user = User.query.filter_by(id=self.user_id).first()
        user.recent_file_id = list[0]
        db.session.add(user)
        db.session.commit()

    def get_file_details(self):
        # just return file name and timestamp
        return self.file_info[0:2] if self.file_info is not None else None

    def get_files(self):
        files = UploadedFile.query.filter_by(user_id=self.user_id).order_by(UploadedFile.uploaded_timestamp.desc()).all()
        return files

    def delete_files(self):
        for f in UploadedFile.query.filter_by(user_id=self.user_id):
            db.session.delete(f)
            db.session.commit()

    def delete_file(self, list):
        file = UploadedFile.query.filter_by(id=list[0]).first()
        db.session.delete(file)
        db.session.commit()

    def get_actor(self):
        return self.trans_df_actor if self.trans_df_actor is not None else None


class DataFrameActor(object):
    #
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
        self.cat_df_actor = CategoryDFActor(self.df)

    def get_subset_df(self, cat_type, frequency=None):
        if frequency is None:
            return self.df.loc[self.df['Category'].isin(self.cat_df_actor.get_categories(cat_type))]
        else:
            return self.df.loc[self.df['Category'].isin(self.cat_df_actor.get_categories(cat_type, frequency))]


    # general category info request - TODO are these really spending requests? right now they go against full dataframe
    def get_entries_by_cat(self):
        # returns a dataframe grouped by Category
        return self.df.groupby(['Category']) #probably need to change what the return value is?

    def get_number_of_entries_by_cat(self):
        # returns an int
        return self.get_entries_by_cat()['Amount'].count()

    def get_total_by_cat(self):
        # returns an series?
        return self.get_entries_by_cat().sum()

    def get_mean_by_cat(self):
        # returns a series keyed by category of the mean size of amounts
        return self.get_entries_by_cat().mean()

    # specific category info request - TODO are these really spending requests? right now they go against full dataframe
    def get_detail_item_display_columns(self):
        return ["Date", "Category",  "Amount", "Description"]  # eventually this will be a user setting

    def get_recent_items_for(self, category, frequency):
        # recent is this and last month, for now just this month
        temp_df = self.get_subset_df(category, frequency)
        # recent items are all items in the current month and last month
        this_year = str(date.today().year)
        this_month = date.today().month
        # need to check if current month is january, then previous month is last year december
        prev_month = 12 if this_month == 1 else this_month - 1
        prev_year = this_year - 1 if prev_month == 12 else this_year
        return temp_df.loc[((temp_df["Year"] == this_year) & (temp_df["Month_as_dec"] == this_month)) |
                           ((temp_df["Year"] == prev_year) & (temp_df["Month_as_dec"] == prev_month)), self.get_detail_item_display_columns()].to_html()

    # summary info is [[name of summary group, [included category list], [[last year summary], [last 12 months], etc]]

    def get_summary_info(self):
        return [['All Transaction', self.df.index.tolist(), self.get_summary_info_for(self.df)]]

    def get_top_line_spending_info(self):
        temp_df = self.get_subset_df('expense')
        number_of_months = len(temp_df['MthYr'].unique())
        monthly_budget = temp_df['Amount'].sum() / number_of_months
        return [['All Spending', len(temp_df['Category'].unique().tolist()), self.get_summary_info_for(temp_df, monthly_budget)]]

    def get_summary_spending_info(self):
        # return a list of lists: [['Total' ['last year', spending, budget, percent spent],
        #                                 ['last 12', spending, budget, percent spent],
        #                                           ...                               ],
        #                          ['Weekly' ['last year', spending, budget, percent spent]]]
        ret = []
        frequencies = self.cat_df_actor.get_spending_category_frequencies()
        for freq in frequencies:
            temp_df = self.get_subset_df('expense', freq)
            monthly_budget = self.cat_df_actor.get_budget_for( 'expense', freq )
            ret.append([freq, len(temp_df['Category'].unique().tolist()), self.get_summary_info_for(temp_df, monthly_budget)])
        return ret

    def get_columns_for_spending(self):
        return ['Period', 'Count', 'Amount', 'of ave spend']

    def get_summary_info_for(self, temp_df, monthly_budget):
        # return list of lists containing summary info for last year, last 12 months, this year, etc...
        ret = []
        # useful intermediate values
        # ['all trans', 'for last year', 'this year', 'last qtr', 'this qtr', 'last month', 'this month']
#        ret.append(self.get_summary_detail('all trans', temp_df))
        budget = monthly_budget * 12
        ret.append(self.get_summary_detail('last year', temp_df.loc[temp_df['Year'] == str(date.today().year - 1)], budget))

        ret.append(self.get_summary_detail('last 12 months', temp_df.loc[
            ((temp_df['Month_as_dec'] < date.today().month) & (temp_df["Year"] == str(date.today().year)))
            | ((temp_df["Year"] == str(date.today().year - 1)) & (temp_df['Month_as_dec'] >= date.today().month))], budget))

        ret.append(self.get_summary_detail('this year', temp_df.loc[temp_df["Year"] == str(date.today().year)], budget))

        budget = monthly_budget * 4
        current_qtr = math.ceil(date.today().month / 3.)
        temp_yr = date.today().year - 1 if current_qtr == 1 else date.today().year
        temp_qtr = 4 if current_qtr == 1 else current_qtr - 1
        ret.append(self.get_summary_detail('last quarter', temp_df.loc[((temp_df['Year'] == str(temp_yr)) & (temp_df["Qtr"] == temp_qtr))], budget))

        ret.append(self.get_summary_detail('this quarter', temp_df.loc[((temp_df['Year'] == str(date.today().year)) & (temp_df["Qtr"] == current_qtr))], budget))
        temp_yr = date.today().year - 1 if date.today().month == 1 else date.today().year
        temp_month = 12 if date.today().month == 1 else date.today().month - 1

        budget=monthly_budget
        ret.append(self.get_summary_detail('last month', temp_df.loc[((self.df['Year'] == str(temp_yr)) & (temp_df["Month_as_dec"] == temp_month))], budget))

        ret.append(self.get_summary_detail('this month', temp_df.loc[((self.df['Year'] == str(date.today().year)) & (temp_df["Month_as_dec"] == date.today().month))], budget))
        return ret

    def get_summary_detail(self, name, detail_df, budget):
        total_spending = detail_df['Amount'].sum()
        percent_budget = total_spending / budget * 100
        return [name, detail_df['Amount'].count(),
                    '${:,.2f}'.format(total_spending),
                    '{:,.2f}%'.format(percent_budget)]

    def get_category_summary_info(self):
        return self.cat_df_actor.get_category_summary_info()


class CategoryDFActor():
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
    def __init__(self, full_df):
        # category dataframe is derived from dataframe containing all the transactions
        temp_category_group_obj = full_df.groupby(['Category'])['Amount']
        entries_count_by_category_series = temp_category_group_obj.count()
        entries_amount_total_category_series = temp_category_group_obj.sum()
        debit_entries_count_series = full_df.loc[full_df['Transaction Type'] == 'debit'].groupby(['Category'])['Amount'].count()
        large_entries_count_series = full_df.loc[full_df['Amount'] > 5000].groupby(['Category'])['Amount'].count()
        self.cat_df = pd.concat([entries_count_by_category_series,
                             entries_amount_total_category_series,
                             large_entries_count_series,
                             debit_entries_count_series],
                            axis=1)
        self.cat_df.set_axis(['count', 'sum', 'large', 'debit'], axis=1, inplace=True)
        self.number_of_months = len(full_df['MthYr'].unique())
        self.cat_df['ave_mnthly_spend'] = self.cat_df['sum'].map(lambda s: s / self.number_of_months)
        self.cat_df['large_percent'] = self.cat_df['large'] / self.cat_df['count']
        self.cat_df['debit_percent'] = self.cat_df['debit'] / self.cat_df['count']
        # create false mutual exclusity among the three cat types - check for investment first to eliminate those from spending
        self.cat_df['category_type'] = self.cat_df.apply(self.det_cat, axis=1)
        self.cat_df['frequency'] = self.cat_df['count'].map(lambda f: f / self.number_of_months)
        self.cat_df['frequency_category'] = self.cat_df.apply(self.det_freq_cat, axis=1)
        self.temp_type_freq_group = self.cat_df.groupby(['category_type', 'frequency_category'])
    # category summary info is list of categories with calculated values in category_info_df

    def get_category_summary_info(self):
        return self.cat_df

    def det_cat(self, row):
        return 'investment' if row['large_percent'] > .4 else 'expense' if row['debit_percent'] > .6 else 'income'

    def get_category_types(self):
        return ['investment', 'expense', 'income']

    def det_freq_cat(self, row):
        naive_actual_frequency = row['count'] / self.number_of_months
        # value of 1 equals one cat entry per month
        # value of 4 equals one per week
        if row['count'] < 5:
            return 'rare'
        elif naive_actual_frequency > 3:
            return 'weekly'
        elif naive_actual_frequency > 1.75:
            return 'biweekly'
        elif naive_actual_frequency > .9:
            return 'monthly'
        elif naive_actual_frequency > .7:
            return 'quarterly'
        else:
            return 'sporadic'

    def get_spending_category_frequencies(self):
        return ['weekly', 'biweekly', 'monthly', 'quarterly', 'sporadic', 'rare']

    def get_categories(self, category_type, frequency=None):
        if frequency is None:
            return self.cat_df.loc[(self.cat_df['category_type'] == category_type)].index.tolist()
        elif frequency == 'all_spending':  # get all categories for that type
            return self.cat_df.loc[(self.cat_df['category_type'] == category_type)].index.tolist()
        else:
            # need to include check to see if frequency in spending categories list
            return self.cat_df.loc[((self.cat_df['category_type'] == 'expense') & (self.cat_df['frequency_category'] == frequency))].index.tolist()

    def get_budget_for(self, category_type, freq):
        return self.temp_type_freq_group['ave_mnthly_spend'].sum()[category_type, freq]