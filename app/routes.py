from flask import render_template, flash, redirect, url_for, request, session
from app import app, db
from config import Config
from app.forms import LoginForm, RegistrationForm, UploadForm, HomeForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, UploadedFile
from app.working_data import DataObjectFactory, DataObjectFactory_old
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from io import BytesIO


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form=HomeForm()
    uploaded_file = UploadedFile.query.filter_by(user_id=current_user.id).order_by(UploadedFile.timestamp.desc()).first()
    if uploaded_file is None:
        return redirect(url_for('upload_file'))
    dfact = DataObjectFactory(uploaded_file.filename, BytesIO(uploaded_file.data))
    form.category.choices = create_selectfield_choices(dfact.get_trans().get_all_categories())
    form.month.choices = create_selectfield_choices(dfact.get_trans().get_all_months())
    form.year.choices = create_selectfield_choices(dfact.get_trans().get_all_years())
    if form.validate_on_submit():
        session["category"] = form.category.data
        session["month"] = form.month.data
        session['year'] = form.year.data
        return redirect(url_for('monthly_detail'))
    return render_template('index.html', form=form, title='Home', file_info=[uploaded_file.filename, uploaded_file.timestamp])


@app.route('/login', methods=['GET', 'POST'])
def login():
    # for now, just have this user and do not allow people to register but still have to login
    db.session.query(User).filter(User.username =='bob').delete(synchronize_session=False)
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
    return render_template('login.html', title='Sign In', form=form, file_info = ["none yet", "not yet"])


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
    return render_template('register.html', title='Register', form=form, file_info = ["none yet", "not yet"])

# helpers
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def get_current_file():
    uploaded_file = UploadedFile.query.filter_by(user_id=current_user.id).order_by(UploadedFile.timestamp.desc()).first()
    if uploaded_file is None:
        return redirect(url_for('upload_file'))
    #assumes multiple files are returned least recent to most recent...and returns last file uploaded
    return uploaded_file

def create_selectfield_choices(choice_list):
    return [(l, l) for l in choice_list]

@app.route('/upload_file', methods=['GET', 'POST'])
@login_required
def upload_file():
    form = UploadForm()
    if form.validate_on_submit():
        filename = secure_filename(form.file.data.filename)
        data = form.file.data.read()
        uploaded_file = UploadedFile(filename=filename, data=data, user_id=current_user.id)
        print(db.session.add(uploaded_file))
        print(db.session.commit())
        return redirect(url_for('index'))
    return render_template('upload_file.html', title='Upload file with budget data', form=form, file_info = ['pending', ''])


@app.route('/monthly_drill_down')
@login_required
def monthly_drill_down():
    uploaded_files = UploadedFile.query.filter_by(user_id=current_user.id)
    if uploaded_files is None:
        return redirect(url_for('upload_file'))
    f = BytesIO(uploaded_files[-1].data)
    dfact = DataObjectFactory_old(uploaded_files[-1].filename, f)
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

@app.route('/monthly_detail')
@login_required
def monthly_detail():
    f = get_current_file()
    dfact = DataObjectFactory(f.filename, BytesIO(f.data))
    category = session['category']
    month = session["month"]
    year = session['year']
    info = dfact.get_trans().get_category_by_month(category, month, year)
    df = info[0]
    category_total = info[1]
    return render_template('monthly_detail.html',
                           file_info=[f.filename, f.timestamp],
                           month = month,
                           year= year,
                           category_total = category_total,
                           tables=[df.to_html(classes='data')],
                           titles=df.columns.values)

