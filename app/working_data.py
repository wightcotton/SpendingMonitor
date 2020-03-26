import pandas as pd


class DatasetFactory(object):

    tran_dataset = ''

    def __init__(self, file):
        if '.csv'in file.filename:
            self.tran_dataset = Transactions(file)


class Transactions():
    base_file = ''

    def __init__(self, file):
        if '.csv' in file.filename:
            data = pd.read_csv(file)
        print(data)

