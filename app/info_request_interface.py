from app.database_access.uplodedfile_access import FileUpload
from app.analysis.dataframe_actor import DataFrameActor, CategoryDFActor, SummaryActor
from app.database_access.category_state_access import CategoryStateAccess


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
        self.cat_actor = CategoryDFActor(self.trans_actor)
        self.summary_actor = SummaryActor()
        self.summary_actor.set_top_line_summary_list(self.cat_actor.get_top_line_summary(self.trans_actor))
        self.summary_actor.set_frequencies_summary_dict(self.cat_actor.get_frequencies_summary(self.trans_actor))
        self.summary_actor.set_categories_summary_dict(self.cat_actor.get_categories_summary(self.trans_actor))
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
        return self.summary_actor.get_top_line_spending_info()

    def get_freq_summary_spending_info(self, list_of_frequencies=None):
        if list_of_frequencies is None:
            list_of_frequencies = self.cat_actor.get_frequencies()
        return self.summary_actor.get_freq_summary_spending_info(list_of_frequencies)

    def get_cat_summary_spending_info(self, list_of_categories=None, frequency=None):
        if list_of_categories is None and frequency is None:
            list_of_categories = self.cat_actor.get_categories('expense')
        elif list_of_categories is None:
            list_of_categories = self.cat_actor.get_categories(category_type='expense', frequency=frequency)
        return self.summary_actor.get_cat_summary_spending_info(list_of_categories)

    def get_freq_examine_list(self):
        return self.summary_actor.get_freq_examine_list()

    def get_cat_examine_list(self):
        return self.summary_actor.get_cat_examine_list()

    # end summary generation

    # end TRANS

    # CATEGORY (requests against derived category data frame)

    def get_budget_for(self, category_type=None, frequency=None, category=None):
        return self.cat_actor.get_budget_for(category_type=category_type, frequency=frequency, category=category)

    def get_category_info(self, sort_by_col_list):
        return self.cat_actor.get_category_info().sort_values(sort_by_col_list, ascending=True).to_html(
            float_format='{:,.2f}'.format)

    def get_category_metadata_headings(self):
        return self.cat_actor.get_category_metadata_cols()

    def get_category_metadata(self, frequency=None, category=None):
        return self.cat_actor.get_category_metadata(frequency=frequency, category=category).to_dict(orient='index')


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
