from app.models import UploadedFile, User
from app.analysis.dataframe_actor import DataFrameActor
from io import BytesIO
from app import db
import pandas as pd


class FileUpload(object):
    def __init__(self, user_id):
        self.user_id = user_id
        user = User.query.filter_by(id=user_id).first()
        file = None
        if user.recent_file_id is not None:
            file = UploadedFile.query.filter_by(id=user.recent_file_id).first()  # user has uploaded file previously
        # else: # check to see of there are other uploaded files - this is a double check, shouldn't get here
        # file = UploadedFile.query.filter_by(user_id=user_id).order_by(UploadedFile.timestamp.desc()).first()
        self.file_info = None
        if file is not None:
            self.file_info = [file.filename, file.uploaded_timestamp, file.data]
        self.trans_df = None
        if self.file_info is not None:
            if '.csv' in self.file_info[0]:
                self.trans_df = pd.read_csv(BytesIO(self.file_info[2]))
            elif '.xlsx' in self.file_info[0]:
                self.trans_df = pd.read_excel(BytesIO(self.file_info[2]), "Transactions")
            else:
                raise Exception("unknown file type")

    def add_new_file(self, file_details_list):
        uploaded_file = UploadedFile(filename=file_details_list[0],
                                     data=file_details_list[1],
                                     user_id=self.user_id)
        db.session.add(uploaded_file)
        db.session.commit()
        return uploaded_file.id

    def set_recent_source(self, list):
        user = User.query.filter_by(id=self.user_id).first()
        user.recent_file_id = list[0]
        db.session.add(user)
        db.session.commit()

    def get_details(self):
        # just return file name and timestamp
        return self.file_info[0:2] if self.file_info is not None else None

    def get_sources(self):
        files = UploadedFile.query.filter_by(user_id=self.user_id).order_by(
            UploadedFile.uploaded_timestamp.desc()).all()
        return files

    def delete_sources(self):
        for f in UploadedFile.query.filter_by(user_id=self.user_id):
            db.session.delete(f)
            db.session.commit()

    def delete_source(self, file_id_list):
        file = UploadedFile.query.filter_by(id=file_id_list[0]).first()
        db.session.delete(file)
        db.session.commit()

    def get_df(self):
        return self.trans_df if self.trans_df is not None else None
