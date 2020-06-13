from app.database_access.uplodedfile_access import FileUpload
from app.analysis.dataframe_actor import DataFrameActor, CategoryDFActor
from app.database_access.category_state_access import CategoryStateAccess
from collections import defaultdict


class InfoRequestHandler(object):
    """
    the source of data for routes
    interface between the underlying data and its implementation
    as little as possible should happen here in the methods as they represent the methods that
    they underlying data implementation needs to meet.
    how the data is delivered through the interface is independent of the underlying data representation
    lists or html are returned
    lists when not based directly on a dataframe
    html when based on a dataframe using to_html with formatting
    limitation is ability to create links inside of the html dataframe tables...
    """

    def __init__(self, user_id):
        self.file_actor = FileUpload(user_id)
        self.trans_actor = DataFrameActor(self.file_actor.get_df())
        self.cat_actor = CategoryDFActor(self.file_actor.get_df())
        self.cat_state_actor = CategoryStateAccess(user_id)

    # FILE

    def get_file_details(self):
        return self.file_actor.get_details()

    def add_new_file(self, attribute_list):
        return self.file_actor.add_new_file(attribute_list)

    def set_recent_file_details(self, attribute_list):
        self.file_actor.set_recent_source(attribute_list)

    def get_source_list(self):
        return self.file_actor.get_sources()

    def delete_all_sources(self):
        self.file_actor.delete_sources()

    def delete_source(self, list):
        self.file_actor.delete_source(list)

    # end FILE

    # TRANS (requests against full data frame)

    def get_columns_for_spending_summary(self):
        return self.trans_actor.get_columns_for_spending_summary()

    def get_items_for(self, category=None):
        return self.trans_actor.get_items_for(category).sort_values(['Date'], ascending=False).to_html(
            float_format='{:,.2f}'.format)

    def get_recent_items_for(self, cat_type=None, frequency=None, category=None):
        if category:
            category_list = [category]
        else:
            category_list = self.cat_actor.get_categories(category_type=cat_type, frequency=frequency)
        return self.trans_actor.get_recent_items_for(category_list)

    def get_summary_info(self):
        return self.trans_actor.get_summary_info()

    # next three methods generate same summary info as list of lists by all spending (top line), by frequency and by
    # category

    def get_top_line_spending_info(self):
        categories = self.cat_actor.get_categories(category_type='expense')
        temp_df = self.trans_actor.get_subset_df(category_list=categories)
        return [['All Spending', len(temp_df['Category'].unique().tolist()),
                 self.trans_actor.get_summary_info_for(temp_df, self.cat_actor.get_budget_for('expense'))]]

    def get_freq_summary_spending_info(self, list_of_frequencies=None):
        # returns summary of spending by frequencies, if no list given, do all frequencies
        # return a list of lists: [['Total' ['last year', spending, budget, percent spent],
        #                                 ['last 12', spending, budget, percent spent],
        #                                           ...                               ],
        #                          ['Weekly' ['last year', spending, budget, percent spent]]]
        ret = []
        if list_of_frequencies is None:
            list_of_frequencies = self.cat_actor.get_spending_category_frequencies()
        for freq in list_of_frequencies:
            categories = self.cat_actor.get_categories(category_type='expense', frequency=freq)
            temp_df = self.trans_actor.get_subset_df(category_list=categories)
            monthly_budget = self.cat_actor.get_budget_for(category_type='expense', frequency=freq)
            ret.append([freq, len(temp_df['Category'].unique().tolist()),
                        self.trans_actor.get_summary_info_for(temp_df, monthly_budget)])
        return ret

    def get_cat_summary_spending_info(self, list_of_categories=None, frequency=None):
        # returns summary of spending by categories
        # return a list of lists: [['Total' ['last year', spending, budget, percent spent],
        #                                 ['last 12', spending, budget, percent spent],
        #                                           ...                               ],
        #                          ['Weekly' ['last year', spending, budget, percent spent]]]
        ret = []
        if frequency:
            list_of_categories = self.cat_actor.get_categories('expense', frequency=frequency)
        for cat in list_of_categories:
            temp_df = self.trans_actor.get_subset_df(category_list=[cat])
            monthly_budget = self.cat_actor.get_budget_for(category=cat)
            ret.append(
                [cat, len(temp_df['Category'].unique().tolist()), self.trans_actor.get_summary_info_for(temp_df, monthly_budget)])
        return ret

    # end summary generation

    # end TRANS

    # CATEGORY (requests against derived category data frame)

    def get_budget_for(self, category_type=None, frequency=None, category=None):
        return self.cat_actor.get_budget_for(category_type=category_type, frequency=frequency, category=category)

    def get_category_info(self, sort_by_col_list):
        return self.cat_actor.get_category_info().sort_values(sort_by_col_list, ascending=True).to_html(
            float_format='{:,.2f}'.format)

    def get_category_metadata(self, frequency=None, category=None):
        return self.cat_actor.get_category_metadata(frequency=frequency, category=category).to_html()

    def get_frequency(self, category=None):
        return self.cat_actor.get_frequency(category=category)

    # end CATEGORY

    # CATEGORY STATE

    def get_current_state_id(self, category):
        return self.cat_state_actor.get_current_state_id(category)

    def get_category_state_info(self, category):
        return self.cat_state_actor.get_category_state_info(category)

    def set_category_current_state(self, category, state_lookup_id):
        return self.cat_state_actor.set_current_state(category, state_lookup_id)

    def get_categories_current_state(self):
        return self.cat_state_actor.get_categories_current_state()

    def get_categories_by_current_state(self):
        return self.cat_state_actor.get_categories_by_current_state()

    def get_category_states(self):
        return self.cat_state_actor.get_lookup_states()

    def get_state_lookups(self):
        return self.cat_state_actor.get_lookup_states()

    def add_lookup_state(self, state=None, desc=None):
        self.cat_state_actor.add_lookup_state(state=state, desc=desc)

    def delete_lookup_states(self, id_list):
        self.cat_state_actor.delete_lookup_states(state_id_list=id_list)

    def delete_category_states(self, category):
        self.cat_state_actor.delete_category_states(category)

    # end CATEGORY STATE
