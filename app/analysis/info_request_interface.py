from datetime import date
import math

from app.analysis.dataframe_actor import File_Upload
from app.analysis.dataframe_actor import DataFrameActor
import pandas as pd

class DataSourceFactory(object):
    def __init__(self, user_id):
        # in the future, if there are other source types for the info, the selection occurs here
        self.source_helper = File_Upload(user_id)
        self.actor = self.source_helper.get_actor()

    def get_source_helper(self):
        # look here for to carry out actions and get info related to the source ie, fileupload
        return self.source_helper

    def get_actor(self):
        #look here for information on the data in the data frames
        return self.actor

class InfoRequestHandler(object):
    def __init__(self, user_id):
        factory = DataSourceFactory(user_id)
        self.source_helper = factory.get_source_helper()
        self.actor = factory.get_actor()
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

    # requests against the source file upload
    def get_source_details(self):
        return self.source_helper.get_file_details()

    def add_new_source(self, attribute_list):
        return self.source_helper.add_new_file(attribute_list)

    def set_recent_source_details(self, attribute_list):
        self.source_helper.set_recent_file(attribute_list)

    def get_source_list(self):
        return self.source_helper.get_files()

    def delete_all_sources(self):
        self.source_helper.delete_files()

    def delete_source(self, list):
        self.source_helper.delete_file(list)

    def get_category_summary_info(self):
        return self.actor.get_category_summary_info().sort_values(['category_type', 'frequency'], ascending=False)\
            .to_html(float_format=lambda f: '{:,.2f}'.format(f))

    def get_columns_for_spending(self):
        return self.actor.get_columns_for_spending()

    def get_summary_info(self):
        return self.actor.get_summary_info()

    def get_summary_of_all_spending(self):
        return self.actor.get_summary_of_all_spending()

    def get_summary_spending_info(self):
        return self.actor.get_summary_spending_info()



class SpendingTransInfo(InfoRequestHandler):
    def __init__(self, user_id):
        super().__init__(user_id)
        self.df_actor = self.factory.get_all_trans_actor()  # this resets a variable that is set in super.__init__
        self.spending_cat_info_headings = ['Monthly Items', 'Ave Amount', 'Frequency', 'Monthly Budget']
        self.spending_cat_info = {}

    def get_category_summary_info(self):
        self.df_actor.get_category_summary_info

    def get_spending_cat_info_headings(self):
        return self.spending_cat_info_headings

    def get_spending_cat_info(self):
        if self.spending_cat_info is None:
            for cat in self.df_actor.get_categories():
                self.spending_cat_info[cat] = ['{:,.2f}'.format(self.df_actor.get_monthly_frequency(cat)),
                                               '{:,.2f}'.format(self.df_actor.get_mean_by_cat(cat)),
                                               self.get_spending_frequency_category(cat),
                                               '${:,.2f}'.format(self.df_actor.get_monthly_budget(cat))
                                               ]
        return self.spending_cat_info

    def get_spending_cat_info_by(self, column_number_of_detail):
        ret = []
        for key, value in self.spending_cat_info.items():
            temp = [key]
            for v in value:
                temp.append(v)
            ret.append(temp)
        return sorted(ret, key=lambda x: float(x[column_number_of_detail]), reverse=True)

    # end init methods

    # summarize results into list by listing of summary items above...

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
