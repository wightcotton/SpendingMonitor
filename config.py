import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('secret_key') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ALLOWED_EXTENSIONS = ['csv', 'xlsx']


class UserConfig(object):
    SUMMARY_TOLERANCE = 110
    SUMMARY_TAGS = ['last year', 'last 12 months', 'this year',
                    'last quarter', 'this quarter',
                    'last month', 'this month']
    META_DATA_COLUMNS = ['frequency', 'state', 'category_type', 'monthly_spend', 'last date', 'timespan', 'ave diff',
                         'large_percent', 'frequency_index']

    # will be user config eventually, ensure columns are correct
