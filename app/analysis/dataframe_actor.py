
import pandas as pd
import numpy as np
from datetime import date, datetime
import math
from app.database_access.category_state_access import CategoryStateAccess


# from sklearn.cluster import KMeans

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
        self.df['Time_between_items'] = self.df.groupby('Category')['Date'].diff() / np.timedelta64(1, 'D')

    def get_subset_df(self, category_list=None):
        return self.df.loc[self.df['Category'].isin(category_list)]

    # INFO REQUESTS

    def get_items_for(self, category=None):
        # gets all items for a category grouped by year and month
        return self.get_subset_df(category_list=[category])[self.get_detail_item_display_columns()]

    def get_columns_for_spending_summary(self):
        # columns for constructed spending summaries - list of lists...
        return ['Period', 'Count', 'Amount', 'of ave spend']

    # summary info is [[name of summary group, [included category list], [[last year summary], [last 12 months], etc]]
    def get_summary_info(self):
        return [['All Transaction', self.df.index.tolist(), self.get_summary_info_for(self.df)]]

    def get_recent_items_for(self, category_list):
        # recent is this month and last month
        temp_df = self.get_subset_df(category_list)
        this_year = str(date.today().year)
        this_month = date.today().month
        # need to check if current month is january, then previous month is last year december
        prev_month = 12 if this_month == 1 else this_month - 1
        prev_year = this_year - 1 if prev_month == 12 else this_year
        return temp_df.loc[((temp_df["Year"] == this_year) & (temp_df["Month_as_dec"] == this_month)) |
                           ((temp_df["Year"] == prev_year) & (temp_df[
                                                                  "Month_as_dec"] == prev_month)), self.get_detail_item_display_columns()].to_html()

    # end INFO REQUESTS
#    def get_category_details_for(self, frequency=None):
 #       return self.get_cat_summary_spending_info(self.cat_df_actor.get_categories('expense', frequency))

#    def get_category_detail(self, category=None):
#        return self.get_cat_summary_spending_info([category])

    def get_detail_item_display_columns(self):
        return ["Date", "Category", "Amount", "Description"]  # eventually this will be a user setting

    def get_summary_info_for(self, temp_df, monthly_budget):
        # return list of lists containing summary info for last year, last 12 months, this year, etc...
        ret = []
        # useful intermediate values
        # ['all trans', 'for last year', 'this year', 'last qtr', 'this qtr', 'last month', 'this month']
        #        ret.append(self.get_summary_detail('all trans', temp_df))
        budget = monthly_budget * 12
        ret.append(
            self.get_summary_detail('last year', temp_df.loc[temp_df['Year'] == str(date.today().year - 1)], budget))

        ret.append(self.get_summary_detail('last 12 months', temp_df.loc[
            ((temp_df['Month_as_dec'] < date.today().month) & (temp_df["Year"] == str(date.today().year)))
            | ((temp_df["Year"] == str(date.today().year - 1)) & (temp_df['Month_as_dec'] >= date.today().month))],
                                           budget))

        ret.append(self.get_summary_detail('this year', temp_df.loc[temp_df["Year"] == str(date.today().year)], budget))

        budget = monthly_budget * 4
        current_qtr = math.ceil(date.today().month / 3.)
        temp_yr = date.today().year - 1 if current_qtr == 1 else date.today().year
        temp_qtr = 4 if current_qtr == 1 else current_qtr - 1
        ret.append(self.get_summary_detail('last quarter', temp_df.loc[
            ((temp_df['Year'] == str(temp_yr)) & (temp_df["Qtr"] == temp_qtr))], budget))

        ret.append(self.get_summary_detail('this quarter', temp_df.loc[
            ((temp_df['Year'] == str(date.today().year)) & (temp_df["Qtr"] == current_qtr))], budget))
        temp_yr = date.today().year - 1 if date.today().month == 1 else date.today().year
        temp_month = 12 if date.today().month == 1 else date.today().month - 1

        budget = monthly_budget
        ret.append(self.get_summary_detail('last month', temp_df.loc[
            ((self.df['Year'] == str(temp_yr)) & (temp_df["Month_as_dec"] == temp_month))], budget))

        ret.append(self.get_summary_detail('this month', temp_df.loc[
            ((self.df['Year'] == str(date.today().year)) & (temp_df["Month_as_dec"] == date.today().month))], budget))
        return ret

    @staticmethod
    def get_summary_detail(name, detail_df, budget):
        total_spending = detail_df['Amount'].sum()
        percent_budget = total_spending / budget * 100
        return [name, detail_df['Amount'].count(),
                '${:,.2f}'.format(total_spending),
                '{:,.2f}%'.format(percent_budget)]


class CategoryDFActor:
    # need to expose these tolerances to allow for analysis within web site to figure out best levels to discriminate
    # among categories
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
    # 2. create columns for summarized base info from category entries that can be used to determine these
    # key attributes of categories
    # 3. create indicator columns that can be used to determine the kind of category as functions of the
    # summarized base info and derive stats about categories
    # 4. get lists containing appropriate categories from some kind of dataframe operation to get the
    # subset of categories in a list
    def __init__(self, full_df):
        # category data frame is derived from data frame containing all the transactions
        temp_category_group_obj = full_df.groupby(['Category'])['Amount']
        cat_item_count = temp_category_group_obj.count()
        cat_first_item_date = full_df.groupby(['Category'])['Date'].min()
        cat_last_item_date = full_df.groupby(['Category'])['Date'].max()
        cat_item_timespan = (cat_last_item_date - cat_first_item_date).dt.days + 1  # for where only one expense
        cat_item_ave_diff = full_df.groupby(['Category'])['Time_between_items'].mean()
        cat_frequency = cat_item_timespan / cat_item_count  # items per day
        cat_total_spend = temp_category_group_obj.sum()
        cat_debit_item_count = full_df.loc[full_df['Transaction Type'] == 'debit'].groupby(['Category'])[
            'Amount'].count()
        cat_large_item_count = full_df.loc[full_df['Amount'] > 5000].groupby(['Category'])['Amount'].count()
        self.cat_df = pd.concat([cat_item_count,
                                 cat_first_item_date,
                                 cat_last_item_date,
                                 cat_item_timespan,
                                 cat_item_ave_diff,
                                 cat_frequency,
                                 cat_total_spend,
                                 cat_large_item_count,
                                 cat_debit_item_count],
                                axis=1)
        self.cat_df.set_axis(
            ['count', 'first date', 'last date', 'timespan', 'ave diff', 'cat freq', 'total spend', 'large', 'debit'],
            axis=1, inplace=True)
        self.number_of_months = len(full_df['MthYr'].unique())
        self.cat_df['ave_mnthly_spend'] = self.cat_df['total spend'].map(lambda s: s / self.number_of_months)
        self.cat_df['large_percent'] = self.cat_df['large'] / self.cat_df['count']
        self.cat_df['debit_percent'] = self.cat_df['debit'] / self.cat_df['count']
        # create false mutual exclusivity among the three cat types - check for investment first to eliminate
        # those from spending
        self.cat_df['category_type'] = self.cat_df.apply(self.det_cat, axis=1)
        self.cat_df['frequency_index'] = self.cat_df.apply(self.calc_freq_index, axis=1)
        self.cat_df['frequency'] = self.cat_df.apply(self.det_freq_cat, axis=1)
        self.cat_df['state'] = self.cat_df.apply(self.get_state, axis=1)
        self.cat_df.replace([np.inf, -np.inf, np.nan], 1)
        self.cat_df['cluster'] = self.do_clustering()
        self.temp_type_freq_group = self.cat_df.groupby(['category_type', 'frequency'])

    # helper methods in creating category df

    def det_cat(self, row):
        # return 'investment' if row['large_percent'] > .4 else 'expense' if row['debit_percent'] > .6 else 'income'
        return 'expense' if row['debit_percent'] > .51 else 'income'

    def get_state(self, row):
        #return CategoryStateAccess.get_current_state(row['Category'])
        return 'happy'

    def get_category_types(self):
        return ['expense', 'income']

    def calc_freq_index(self, row):
        return row['cat freq']

    def det_freq_cat(self, row):
        if row['count'] < 5:
            return 'rare'
        elif row['frequency_index'] < 8:
            return 'weekly'
        elif row['frequency_index'] < 16:
            return 'biweekly'
        elif row['frequency_index'] < 35:
            return 'monthly'
        elif row['frequency_index'] < 100:
            return 'quarterly'
        else:
            return 'sporadic'

    # end helper methods

    # INFO REQUESTS

    def get_category_info(self):
        return self.cat_df

    def get_category_metadata(self, frequency=None, category=None):
        if frequency:
            categories = self.get_categories('expense', frequency)
            return self.cat_df.loc[categories, self.get_category_metadata_cols()]
        elif category:
            return self.cat_df.loc[[category], self.get_category_metadata_cols()]
        else:
            return None

    def get_frequency(self, category=None):
        return self.cat_df.loc[category]['frequency']

    # end INFO REQUESTS

    def get_spending_category_frequencies(self):
        return ['weekly', 'biweekly', 'monthly', 'quarterly', 'sporadic', 'rare']

    def get_categories(self, category_type, frequency=None):
        if frequency is None:
            return self.cat_df.loc[(self.cat_df['category_type'] == category_type)].index.tolist()
        elif frequency == 'all_spending':  # get all categories for that type
            return self.cat_df.loc[(self.cat_df['category_type'] == category_type)].index.tolist()
        else:
            # need to include check to see if frequency in spending categories list
            return self.cat_df.loc[((self.cat_df['category_type'] == 'expense') & (
                    self.cat_df['frequency'] == frequency))].index.tolist()

    def get_budget_for(self, category_type=None, frequency=None, category=None):
        if category:
            return self.cat_df.loc[category]['ave_mnthly_spend']
        elif category_type and frequency:
            return self.temp_type_freq_group['ave_mnthly_spend'].sum()[category_type, frequency]
        elif category_type:
            return self.cat_df.loc[self.cat_df['category_type'] == category_type].sum()['ave_mnthly_spend']

    def get_category_metadata_cols(self):
        return ['frequency', 'last date', 'timespan', 'ave diff', 'large_percent', 'frequency_index']

    def do_clustering(self):
        return True
        # km = KMeans(n_clusters=5, init='random', n_init=10, max_iter=300, tol=1e-04, random_state=0)
        # return km.fit_predict(self.cat_df[['frequency_index']])

    # category dataframe graveyard of stats...

    # category_number_of_months_series = full_df.groupby(['Category'])['MthYr'].unique().map(lambda m: len(m))
    # category_days_since_last_item = cat_last_item_date.map(
    #             lambda d: (datetime.today().date() - datetime.date(d)).days)
    #         self.cat_df['frequency_within_months'] = self.cat_df['count'] / self.cat_df['months']
    #         self.cat_df['frequency_across_full_timeframe'] = self.cat_df['count'].map(lambda c: c /
    #         self.number_of_months)

    #     def calc_freq_index(self, row):
    #         # on average, if there are  more than 3 items per month category is a good weekly candidate,
    #         #   but can be weak because category has to be active across full time
    #         #   if last item ws within the last ~ 10 days, locks it in as weekly
    #         #   other weekly categories, have a frequency within > 3 as well but need to have a fresh dispersion
    #         # monthly frequency divided by full number of months * or / dispersion factor
    #         (degree to which items been spent across full time frame)
    #         # user frequency within months if recent and if dispersion is consistent with frequency
    #         if 20 < row['dispersion'].days / row['months'] < 40 and 20 < row['days since last item'] / row[
    #             'frequency_within_months'] < 40:
    #             return row['frequency_within_months']
    #         else:
    #             return row['frequency_across_full_timeframe']
