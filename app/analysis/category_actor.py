import pandas as pd
import numpy as np
from app.database_access.category_state_access import CategoryStateAccess
from flask_login import current_user

class CategoryDFActor(object):
    """class <>
    Categories are key to monitoring spending, most analysis is done by category, monitoring against expected spending
    and to figure out if a category should be included or excluded to figure out expected spending

    expense categories have a majority of entries where money goes out (for mint, transaction type is debit)
    income categories have a majority of entries where money come in (for mint, transaction type is credit)

    this focuses now exclusively on spending (expecting to handle income as some later point...)

    base is a data frame containing all transactions.  it is assumed that each transaction has, at a minimum,
    a date, category and amount.  all the analysis stems from those columns.  the outcome of this class is a data frame
    indexed by category containing all information about a category.  the key data construct for the UI is category
    metadata
    eventually, the user will be able to select which metadata they are interested in seeing on the UI,  currently
    it is arbitrary as more columns are derived and their usefulness determined.

    attributes
    ----------
    cat_df : data frame containing all derived columns

    methods
    -------
    init : takes transactional dataframe and uses it to derive columns for cat_df
            (hoping that because the transactional actor (df_actor) is only used in init, it does not weigh down this class
    get_category_info: dataframe containing categories and columns specified or the whole dataframe if none

    """

    def __init__(self, df_actor):
        # category data frame is derived from data frame containing all the transactions
        temp_category_group_obj = df_actor.df.groupby(['Category'])['Amount']

        # helper methods in creating category df
        def det_cat(row):
            # return 'investment' if row['large_percent'] > .4 else 'expense' if row['debit_percent'] > .6 else 'income'
            return 'expense' if row['debit_percent'] > .51 else 'income'

        def get_state(row):
            return CategoryStateAccess(current_user.id).get_current_state(row['Category'])

        def calc_freq_index(row):
            return row['cat freq']

        def det_freq_cat(row):
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

        cat_item_count = temp_category_group_obj.count()
        cat_first_item_date = df_actor.df.groupby(['Category'])['Date'].min()
        cat_last_item_date = df_actor.df.groupby(['Category'])['Date'].max()
        cat_item_timespan = (cat_last_item_date - cat_first_item_date).dt.days + 1  # for where only one expense
        cat_first_item_date = cat_first_item_date.dt.strftime('%m/%d/%Y')
        cat_last_item_date = cat_last_item_date.dt.strftime('%m/%d/%Y')
        cat_item_ave_diff = df_actor.df.groupby(['Category'])['Time_between_items'].mean()
        cat_frequency = cat_item_timespan / cat_item_count  # items per day
        cat_total_spend = temp_category_group_obj.sum()
        cat_debit_item_count = df_actor.df.loc[df_actor.df['Transaction Type'] == 'debit'].groupby(['Category'])[
            'Amount'].count()
        cat_large_item_count = df_actor.df.loc[df_actor.df['Amount'] > 5000].groupby(['Category'])['Amount'].count()
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
        self.cat_df['Category'] = self.cat_df.index
        self.number_of_months = len(df_actor.df['MthYr'].unique())
        self.cat_df['monthly_spend'] = self.cat_df['total spend'].map(lambda s: s / self.number_of_months)
        self.cat_df['large_percent'] = self.cat_df['large'] / self.cat_df['count']
        self.cat_df['debit_percent'] = self.cat_df['debit'] / self.cat_df['count']
        # create false mutual exclusivity among the three cat types - check for investment first to eliminate
        # those from spending
        self.cat_df['category_type'] = self.cat_df.apply(det_cat, axis=1)
        self.cat_df['frequency_index'] = self.cat_df.apply(calc_freq_index, axis=1)
        self.cat_df['frequency'] = self.cat_df.apply(det_freq_cat, axis=1)
        self.cat_df['state'] = self.cat_df.apply(get_state, axis=1)
        self.cat_df.replace([np.inf, -np.inf, np.nan], 1)
        self.cat_df['cluster'] = self.do_clustering()
        self.temp_type_freq_group = self.cat_df.groupby(['category_type', 'frequency'])

    # PUBLIC INTERFACE METHODS

    def is_category_included(self, category=None):
        return category in self.cat_df.index.tolist()

    def get_category_metadata_df(self, categories=None, columns=None, sort_by_cols=None, ascending=None):
        if sort_by_cols is None:
            sort_by_cols = 'monthly_spend'
            ascending = False
        if categories and columns:
            return self.cat_df.loc[categories, columns].sort_values(by=sort_by_cols, ascending=ascending)
        elif categories:
            return self.cat_df.loc[categories].sort_values(by=sort_by_cols, ascending=ascending)
        elif columns:
            return self.cat_df.loc[:, columns].sort_values(by=sort_by_cols, ascending=ascending)
        else:
            return self.cat_df.sort_values(by=sort_by_cols, ascending=ascending)

    def get_category_metadata_list(self, categories=None, columns=None):
        temp_df = self.get_category_metadata_df(categories=categories, columns=columns)
        temp_df.reset_index(inplace=True)
        temp_df = temp_df.rename(columns={'index': 'category'})
        return [temp_df.columns.values.tolist()] + temp_df.values.tolist()

    def get_frequency(self, category):
        return self.cat_df.loc[category]['frequency']

    def get_frequencies(self):
        return self.cat_df.frequency.unique()

    # end INFO REQUESTS

    def get_categories(self, category_type=None, frequency=None):
        if category_type is None and frequency is None:
            return self.cat_df.index.tolist()
        elif frequency is None:
            return self.cat_df.loc[(self.cat_df['category_type'] == category_type)].index.tolist()
        elif category_type is None:
            return self.cat_df.loc[(self.cat_df['category_type'] == category_type)].index.tolist()
        else:
            # need to include check to see if frequency in spending categories list
            return self.cat_df.loc[((self.cat_df['category_type'] == 'expense') & (
                    self.cat_df['frequency'] == frequency))].index.tolist()

    def get_category_list(self, category_type=None, frequency=None):
        if frequency and category_type:
            # return all categories with category_type and frequency
            return self.cat_df.loc[((self.cat_df['category_type'] == 'expense') &
                                    (self.cat_df['frequency'] == frequency))].index.tolist()
        elif frequency:
            # return all categories with given frequency
            return self.cat_df[(self.cat_df['frequency'] == frequency)].index.tolist()
        elif category_type:
            # return all categories with given category_type
            return self.cat_df[(self.cat_df['category_type'] == category_type)].index.tolist()
        else:
            # return all categories
            return self.cat_df.index.tolist()

    def get_budget_for(self, category_type=None, frequency=None, category=None):
        if category:
            return self.cat_df.loc[category]['monthly_spend']
        elif category_type and frequency:
            return self.cat_df.loc[(self.cat_df['category_type'] == category_type) &
                                   (self.cat_df['frequency'] == frequency) &
                                   (self.cat_df['state'] != 'ignore')].sum()['monthly_spend']
        elif category_type:
            return self.cat_df.loc[(self.cat_df['category_type'] == category_type) &
                                   (self.cat_df['state'] != 'ignore')].sum()['monthly_spend']

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
