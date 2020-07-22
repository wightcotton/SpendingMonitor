from app.database_access.uplodedfile_access import FileUpload
from app.analysis.dataframe_actor import DataFrameActor
from app.analysis.category_actor import CategoryDFActor
from app.analysis.summary_actor import SummaryActor
from app.database_access.category_state_access import CategoryStateAccess
from config import UserConfig
from datetime import date
import math


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
        self.cat_state_actor = CategoryStateAccess(user_id)

        def get_columns_for_spending_summary():
            # column headings for constructed spending summaries in get_summary_detail - list of lists...
            return ['Period', 'Categories', 'Count', 'Amount', 'vs expected']

        def refine_budget(tag, monthly_budget):
            if tag in ['last year', 'last 12 months', 'this year']:
                budget = monthly_budget * 12
            elif tag in ['last quarter', 'this quarter']:
                budget = monthly_budget * 3
            else:
                budget = monthly_budget
            return budget

        def get_summary_detail(summary_tag, categories=None, budget=0):
            tag_info = self.trans_actor.get_summary_tag_info(summary_tag=summary_tag, categories=categories)
            spending = tag_info[0]
            tran_count = tag_info[1]
            cat_count = tag_info[2]
            percent_budget = spending / budget * 100
            return [summary_tag, cat_count, tran_count, '${:,.2f}'.format(spending), '{:,.2f}%'.format(percent_budget)]

        def get_top_line_summary(actor):
            summary_list = [get_columns_for_spending_summary()]
            categories = self.cat_actor.get_categories(category_type='expense')
            for cat in self.cat_state_actor.get_categories_current_state_for('ignore'):
                try:
                    categories.remove(cat)
                except ValueError:  # there could be categories not in data frame that are in database
                    pass
            monthly_budget = self.get_budget_for(category_type='expense')
            for tag in UserConfig.SUMMARY_TAGS:
                budget = refine_budget(tag, monthly_budget)
                summary_list.append(get_summary_detail(tag, categories=categories, budget=budget))
            return [['All Spending', summary_list]]

        def get_frequency_summaries(actor):
            ret_dict = {}
            for freq in self.cat_actor.get_frequencies():
                categories = self.cat_actor.get_categories(category_type='expense', frequency=freq)
                for cat in self.cat_state_actor.get_categories_current_state_for('ignore'):
                    try:
                        categories.remove(cat)
                    except ValueError:  # there could be categories not in data frame that are in database
                        pass
                summary_list = [get_columns_for_spending_summary()]
                monthly_budget = self.get_budget_for(category_type='expense', frequency=freq)
                for tag in UserConfig.SUMMARY_TAGS:
                    budget = refine_budget(tag, monthly_budget)
                    summary_list.append(get_summary_detail(tag, categories=categories, budget=budget))
                ret_dict[freq] = [freq, summary_list]
            return ret_dict

        def get_category_summaries(actor):
            # returns summary of spending by categories
            # return a list of lists: [['Total' ['last year', spending, budget, percent spent],
            #                                 ['last 12', spending, budget, percent spent],
            #                                           ...                               ],
            #                          ['Weekly' ['last year', spending, budget, percent spent]]]
            ret_dict = {}
            categories = self.cat_actor.get_categories(category_type='expense')
            for cat in self.cat_state_actor.get_categories_current_state_for('ignore'):
                try:
                    categories.remove(cat)
                except ValueError:  # there could be categories not in data frame that are in database
                    pass
            for cat in categories:
                summary_list = [get_columns_for_spending_summary()]
                monthly_budget = self.get_budget_for(category=cat)
                for tag in UserConfig.SUMMARY_TAGS:
                    budget = refine_budget(tag, monthly_budget)
                    summary_list.append(get_summary_detail(tag, categories=[cat], budget=budget))
                ret_dict[cat] = [cat, summary_list]
            return ret_dict

        self.summary_actor = SummaryActor(get_top_line_summary(self.trans_actor),
                                          get_frequency_summaries(self.trans_actor),
                                          get_category_summaries(self.trans_actor))


        # calc for summary table

    # end summary table

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

    def get_items_for(self, category=None, summary_tag=None):
        return self.trans_actor.get_items_for(category=category, summary_tag=summary_tag).sort_values(['Date'],
                                                                                                      ascending=False).to_html(
            float_format='{:,.2f}'.format)

    def get_recent_items_for(self, cat_type=None, frequency=None, category=None):
        if category:
            category_list = [category]
        else:
            category_list = self.cat_actor.get_categories(category_type=cat_type, frequency=frequency)
        return self.trans_actor.get_recent_items_for(category_list)

    # end TRANS

    # CATEGORY (requests against derived category data frame)

    def is_category_included(self, category=None):
        return self.cat_actor.is_category_included(category=category)

    def get_category_metadata_headings(self):
        return self.cat_actor.get_category_metadata_cols()

    def get_category_metadata_df(self, categories=None, columns=None, sort_by_cols=None, ascending=None):
        return self.cat_actor.get_category_metadata_df(categories=categories,
                                                       columns=columns,
                                                       sort_by_cols=sort_by_cols,
                                                       ascending=ascending)

    def get_category_metadata_dict(self, categories=None, columns=None, sort_by_cols=None, ascending=None):
        temp_df = self.get_category_metadata_df(ategories=categories, columns=columns,
                                                sort_by_cols=sort_by_cols, ascending=ascending)
        temp_df.reset_index(inplace=True)
        temp_df = temp_df.rename(columns={'index': 'category'})
        return temp_df.to_dict(orient='index')

    def get_category_metadata_list(self, categories=None, columns=None, sort_by_cols=None, ascending=None):
        if columns is None:
            columns = UserConfig.META_DATA_COLUMNS
        temp_df = self.cat_actor.get_category_metadata_df(categories=categories, columns=columns,
                                                          sort_by_cols=sort_by_cols, ascending=ascending)
        temp_df.reset_index(inplace=True)
        temp_df = temp_df.rename(columns={'index': 'category'})
        return_list = temp_df.values.tolist()
        return_list.insert(0, temp_df.columns.values.tolist())
        return return_list

    def get_frequency(self, category):
        return self.cat_actor.get_frequency(category)

    def get_categories(self, category_type=None, frequency=None, summary_tag=None):
        if frequency:
            return self.cat_actor.get_categories(category_type=category_type, frequency=frequency)
        elif summary_tag:
            return self.trans_actor.get_categories_for(summary_tag=summary_tag).tolist()

    def get_budget_for(self, category_type=None, frequency=None, category=None):
        return self.cat_actor.get_budget_for(category_type=category_type, frequency=frequency, category=category)

    # end CATEGORY

    # SUMMARY

    def get_top_line_spending_info(self):
        return self.summary_actor.get_top_line_spending_info()

    def get_freq_summary_spending_info(self, list_of_frequencies=None):
        return self.summary_actor.get_freq_summary_spending_info(list_of_frequencies)

    def get_cat_summary_spending_info(self, list_of_categories=None):
        return self.summary_actor.get_cat_summary_spending_info(list_of_categories)

    def get_overspent_frequencies_by_summary_tag(self):
        return self.summary_actor.get_overspent_frequencies_by_summary_tag()

    def get_overspent_categories_by_summary_tag(self):
        return self.summary_actor.get_overspent_categories_by_summary_tag()

    def get_overspent_cat_metadata_by_summary_tag(self):
        ret_list = []
        for i in self.get_overspent_categories_by_summary_tag():
            ret_list.append([i[0], self.cat_actor.get_category_metadata_list(categories=i[1],
                                                                             columns=UserConfig.META_DATA_COLUMNS)])
        return ret_list

    def get_overspent_frequencies_for(self, summary_tag=None):
        for i in self.get_overspent_frequencies_by_summary_tag():
            if i[0] == summary_tag:
                return i[1]
        return None

    def get_overspent_categories_for(self, summary_tag=None):
        for i in self.get_overspent_categories_by_summary_tag():
            if i[0] == summary_tag:
                return i[1]
        return None

    # end summary generation

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
