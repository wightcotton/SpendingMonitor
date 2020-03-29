from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'

from app import routes, models
from app.models import User

# for now, just have this user and do not allow people to register but still have to login
#db.session.query(User).filter(User.username =='bob').delete(synchronize_session=False)
#default_user = User(username='bob', email='b@b.com')
#default_user.set_password('time_flies!!!!')
#db.session.add(default_user)
#db.session.commit()


