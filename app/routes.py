from flask import render_template, flash, redirect, url_for, request, session
from app import app, db
from config import Config
from app.forms import LoginForm, RegistrationForm, UploadForm, HomeForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, UploadedFile
from app.analysis.working_data import File_Helper
from app.old_working_data import DataObjectFactory_old
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import date


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = HomeForm()
    file_info = File_Helper().get_file_info(current_user.id)
    if file_info == []:
        return redirect(url_for('upload_file'))
    return render_template('index.html',
                           file_info=[file_info[0], file_info[1]],
                           title='Home')


@app.route('/spending_analysis', methods=['GET', 'POST'])
@login_required
def spending_analysis():
    file = File_Helper()
    file_info = file.get_file_info(current_user.id)
    if file_info == []:
        return redirect(url_for('upload_file'))
    dfact_df = file.get_trans_df()
    # spending summary
    annual_spending_info = [dfact_df.get_last_year_info(),
                            dfact_df.get_this_year_info(),
                            dfact_df.get_last_qtr_info(),
                            dfact_df.get_this_qtr_info(),
                            dfact_df.get_last_month_info(),
                            dfact_df.get_this_month_info()]
    return render_template('spending_analysis.html',
                           file_info=[file_info[0], file_info[1]],
                           title='Home',
                           today=date.today(),
                           annual_spending=annual_spending_info,
                           cat_info_headings=dfact_df.get_spending_cat_info_headings(),
                           cat_info=dfact_df.get_spending_cat_info_by(2))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # for now, just have this user and do not allow people to register but still have to login
    db.session.query(User).filter(User.username == 'bob').delete(synchronize_session=False)
    default_user = User(username='bob', email='b@b.com')
    default_user.set_password('time_flies!!!!')
    db.session.add(default_user)
    db.session.commit()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form, file_info=["none yet", "not yet"])


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form, file_info=["none yet", "not yet"])


# helpers
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/upload_file', methods=['GET', 'POST'])
@login_required
def upload_file():
    form = UploadForm()
    if form.validate_on_submit():
        filename = secure_filename(form.file.data.filename)
        data = form.file.data.read()
        file_helper = File_Helper()
        file_helper.set_file(filename, data, user_id=current_user.id)
        return redirect(url_for('index'))
    return render_template('upload_file.html', title='Upload file with budget data', form=form,
                           file_info=['pending', ''])
