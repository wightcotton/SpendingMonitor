from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import datetime
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    recent_file_id = db.Column(db.Integer, db.ForeignKey('uploaded_file.id'))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class StateLookup(db.Model):
    __tablename__ = 'state_lookup'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    state = db.Column(db.String(64), index=True)
    description = db.Column(db.Text)
    __table_args__ = (UniqueConstraint('user_id', 'state', name='_user_state_uc'),)


class CategoryState(db.Model):
    __tablename__ = 'category_state'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category = db.Column(db.String(64), index=True)
    state = db.Column(db.Integer, db.ForeignKey('state_lookup.id'))
    comment = db.Column(db.Text)
    timestamp = db.Column(db.TIMESTAMP, index=True, default=func.now())


class UploadedFile(db.Model):
    __tablename__ = 'uploaded_file'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(64))
    data = db.Column(db.LargeBinary)
    uploaded_timestamp = db.Column(db.TIMESTAMP, index=True, default=datetime.datetime.now())
    file_last_modified_dt = db.Column(db.TIMESTAMP)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<UploadedFile {}>'.format(self.filename)
