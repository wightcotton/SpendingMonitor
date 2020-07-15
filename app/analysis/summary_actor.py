from config import UserConfig


class SummaryActor(object):
    """class <>

    place to access derived information regarding categories
    Summaries are calculated over the last year, last 12 months, this year, last quarter, this quarter,
    last month and this month (these are summary tags)
    for each of these, how many transactions, how much was spent and what percent of expected spending are calculated
    there is a top line summary (all spending), by each frequency and by each category
    for the frequency and category summaries, over spending is flagged for each of the summary tags

    Attributes
    ----------
        top_line_summary_list : list [[period, count, amount, percent], [period, count, amount, percent],..]
            all spending as described above
        frequencies_summary_dict : summary by frequency (weekly, biweekly, monthly, quarterly, sparodic, rare)
        categories_summary_dict : summary by category
        overspent_frequencies_by_summary_tag : list  of frequencies by summary tag
        overspent_categories_by_summary_tag : list of categories by summary tag

    Methods
    -------
        __init__(self, top_line_summary_list, freq_summary_spending_info, cat_summary_spending_info):
            sets the paramaters and calculates overspending attributes

        get_top_line_spending_info: list as defined above for all spending (not ignored categories)
        get_freq_summary_spending_info(list_of_frequencies) : summary table for each listed frequency
                or list of summaries from all frequencies
        get_cat_summary_spending_info(list_of_categories) : summary table for each listed cat
                or list of summaries from all categories
        get_overspent_frequencies_by_summary_tag : list of [summary_tag, [frequencies]]
        get_overspent_categories_by_summary_tag : list of [summary_tag, [frequencies]]
    """

    def __init__(self, top, freq, cat):
        self.top_line_summary_list = top
        self.frequencies_summary_dict = freq
        self.categories_summary_dict = cat

        def get_percent_as_float(percent_string):
            return float(percent_string.replace('%', '').replace(',', ''))

        def create_overspent_by_summary_tag(focus_dict):
            # returns list of keys exceeding spending by some summary tag
            ret_list = []
            for k, v in focus_dict.items():
                for i in v[2]:
                    if get_percent_as_float(i[3]) > UserConfig.SUMMARY_TOLERANCE:
                        add_new_tag = True
                        for r in ret_list:
                            if i[0] == r[0]:
                                r[1].append(k)
                                add_new_tag = False
                        if add_new_tag:
                            ret_list.append([i[0], [k]])
            return ret_list

        self.overspent_frequencies_by_summary_tag = create_overspent_by_summary_tag(freq)
        self.overspent_categories_by_summary_tag = create_overspent_by_summary_tag(cat)

    @staticmethod
    def create_summary_list(list_to_include=None, summary_dict=None):
        ret_list = []
        if list_to_include:
            for k, v in summary_dict.items():
                if k in list_to_include:
                    ret_list.append(v)
        else:
            for k, v in summary_dict.items():
                ret_list.append(v)
        return ret_list

    # PUBLIC INTERFACE METHODS

    def get_top_line_spending_info(self):
        return self.top_line_summary_list

    def get_freq_summary_spending_info(self, list_of_frequencies=None):
        return self.create_summary_list(list_of_frequencies, self.frequencies_summary_dict)

    def get_cat_summary_spending_info(self, list_of_categories=None):
        return self.create_summary_list(list_of_categories, self.categories_summary_dict)

    def get_overspent_frequencies_by_summary_tag(self):
        return self.overspent_frequencies_by_summary_tag

    def get_overspent_categories_by_summary_tag(self):
        return self.overspent_categories_by_summary_tag

    # END PUBLIC INTERFACE METHODS