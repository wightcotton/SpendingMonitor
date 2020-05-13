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
    """
    the interface between the underlying data and its implementation
    as little as possible should happen here in the methods as they represent the methods that
    they underlying data implementation needs to meet.
    how the data is delivered through the interface is independent of the underlying data representation
    lists or html are returned
    lists when not based directly on a dataframe
    html when based on a dataframe using to_html with formatting
    limitation is ability to create links inside of the html dataframe tables...
    """
    def __init__(self, user_id):
        factory = DataSourceFactory(user_id)
        self.source_helper = factory.get_source_helper()
        self.actor = factory.get_actor()

    # requests against the sourcing of the data
    def get_source_details(self):
        return self.source_helper.get_details()

    def add_new_source(self, attribute_list):
        return self.source_helper.add_new_source(attribute_list)

    def set_recent_source_details(self, attribute_list):
        self.source_helper.set_recent_source(attribute_list)

    def get_source_list(self):
        return self.source_helper.get_sources()

    def delete_all_sources(self):
        self.source_helper.delete_sources()

    def delete_source(self, list):
        self.source_helper.delete_source(list)
    # end data source

    # requests against content
    def get_category_info_by(self, sort_by_col_list):
        return self.actor.get_category_info(sort_by_col_list)

    def get_columns_for_spending(self):
        return self.actor.get_columns_for_spending()

    def get_summary_info(self):
        return self.actor.get_summary_info()

    def get_top_line_spending_info(self):
        return self.actor.get_top_line_spending_info()

    def get_summary_spending_info(self):
        return self.actor.get_summary_spending_info()

    def get_recent_items_for(self, cat_type=None, frequency=None, category=None):
        return self.actor.get_recent_items_for(cat_type=cat_type, frequency=frequency, category=category)

