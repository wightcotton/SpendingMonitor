from flask import render_template, flash, redirect, url_for, request
from app import app, db
from config import Config
from app.forms import LoginForm, RegistrationForm, UploadForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, UploadedFile
from app.working_data import DataObjectFactory, Budget, Transactions
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from io import BytesIO


@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')


@app.route('/login', methods=['GET', 'POST'])
def login():
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
    return render_template('login.html', title='Sign In', form=form)


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
    return render_template('register.html', title='Register', form=form)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@app.route('/upload_file', methods=['GET', 'POST'])
@login_required
def upload_file():
    form = UploadForm()
    if form.validate_on_submit():
        filename = secure_filename(form.file.data.filename)
        data = form.file.data.read()
        uploaded_file = UploadedFile(filename=filename, data=data, user_id=current_user.id)
        print(uploaded_file)
        print(db.session.add(uploaded_file))
        print(db.session.commit())
        flash('file is: ' + filename)
        return redirect(url_for('index'))
    return render_template('upload_file.html', title='Upload file with budget data', form=form)


@app.route('/monthly_drill_down')
@login_required
def monthly_drill_down():
    uploaded_files = UploadedFile.query.filter_by(user_id=current_user.id)
    f = BytesIO(uploaded_files[-1].data)
    dfact = DataObjectFactory(uploaded_files[-1].filename, f)
    budget_df = dfact.get_budgets_dataframe()
    trans_df = dfact.get_trans_dataframe()

    budget_info = budget_df.budget_info
    actuals_dict = trans_df.accumulated_spending_by_category_by_month
    summary_dict = trans_df.accumulated_spending_by_category
    past_year_dict = trans_df.accumulated_spending_for_past_year
    super_cat_dict = trans_df.accumulated_spending_by_super_category
    category_dict = trans_df.accumulated_spending_by_category
    transactions_dict = trans_df.transactions
    return render_template('monthly_drill_down.html',
                           actuals=actuals_dict,
                           budgets=budget_info,
                           summary=summary_dict,
                           past_year=past_year_dict,
                           super_categories=super_cat_dict,
                           categories=category_dict,
                           transactions=transactions_dict)
