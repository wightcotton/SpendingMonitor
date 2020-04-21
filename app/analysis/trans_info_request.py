from datetime import date
import math
from app.analysis.dataframe_actor import DataFrameFactory


class TransInfo(object):
    def __init__(self, user_id):
        self.fact = DataFrameFactory(user_id)
        self.file_info = self.fact.get_file_info()
        self.df_actor = self.fact.get_trans_df_actor()
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

    def get_file_info(self):
        return self.file_info

    def get_summary_info(self):
        return self.df_actor.get_summary_info()

    def get_summary_spending_info(self):
        return self.df_actor.get_summary_spending_info()


class SpendingTransInfo(TransInfo):
    def __init__(self, user_id):
        super().__init__(user_id)
        self.df_actor = self.fact.get_all_trans_actor()  # this resets a variable that is set in super.__init__
        self.spending_cat_info_headings = ['Monthly Items', 'Ave Amount', 'Frequency', 'Monthly Budget']
        self.spending_cat_info = {}

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
