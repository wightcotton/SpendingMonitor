from flask import render_template, flash, redirect, url_for, request, session
from app import app, db
from config import Config
from app.forms import LoginForm, RegistrationForm, UploadForm, HomeForm, FileAdminForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, UploadedFile
from app.analysis.info_request_interface import InfoRequestHandler
from app.old_working_data import DataObjectFactory_old
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import date


@app.route('/category_analysis', methods=['GET', 'POST'])
@login_required
def category_analysis():
    form = FileAdminForm()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_source_details()
    if not file_info:
        return redirect(url_for('upload_file')) # someday need to abstract this
    return render_template('category_details.html',
                           file_info=[file_info[0], file_info[1]],
                           title='Category Analysis',
                           today=date.today(),
                           category_info=info_requester.get_category_info_by(['category_type', 'frequency_index']))


@app.route('/category_detail/<category>', methods=["GET"])
@login_required
def category_detail(category):
    #    form = Form()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_source_details()
    return render_template('category_detail.html', title='Category Details', file_info=[file_info[0], file_info[1]],
                           cat = category,
                           items = info_requester.get_recent_items_for(category=category))


@app.route('/file_admin', methods=['GET', 'POST'])
@login_required
def file_admin():
    form = FileAdminForm()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_source_details()
    if not file_info:
        return redirect(url_for('upload_file')) # someday need to abstract this
    form.files.choices = [(f.id, f.filename + "; " + str(f.uploaded_timestamp)) for f in info_requester.get_source_list()]
    file_info = info_requester.get_source_details()
    if request.method == 'POST':
        if form.select.data:
            info_requester.set_recent_source_details([int(form.files.data)])
        elif form.delete.data:
            info_requester.delete_source([int(form.files.data)])
        elif form.delete_all.data:
            info_requester.delete_all_sources()
            return redirect(url_for('upload_file'))
        return redirect(url_for('index'))
    return render_template('file_admin.html',
                           title='files...',
                           form=form,
                           file_info = file_info)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = HomeForm()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_source_details()
    if not file_info:
        return redirect(url_for('upload_file')) # someday need to abstract this
    return render_template('index.html',
                           file_info=[file_info[0], file_info[1]],
                           title='Home',
                           today=date.today(),
                           columns=info_requester.get_columns_for_spending(),
                           topline_spending_summary=info_requester.get_top_line_spending_info())


@app.route('/login', methods=['GET', 'POST'])
def login():
    # for now, just have this user and do not allow people to register but still have to login
    '''
    db.session.query(User).filter(User.username == 'bob').delete(synchronize_session=False)
    # clean up old users, TODO build user admin page and file admin
    # default_user = User(username='bob', email='b@bibbbo.com')
    default_user.set_password('time_flies!!!!')
    db.session.add(default_user)
    db.session.commit()
    '''
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

@app.route('/monthly_detail/<frequency>', methods=["GET"])
@login_required
def monthly_detail(frequency):
    #    form = Form()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_source_details()
    return render_template('monthly_detail.html', title='Monthly Details', file_info=[file_info[0], file_info[1]],
                           freq = frequency,
                           items = info_requester.get_recent_items_for('expense', frequency=frequency))


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


@app.route('/spending_analysis', methods=['GET', 'POST'])
@login_required
def spending_analysis():
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_source_details()
    if not file_info:
        return redirect(url_for('upload_file')) # someday need to abstract this
    # spending summary
    return render_template('spending_analysis.html',
                           file_info=[file_info[0], file_info[1]],
                           title='Home',
                           today=date.today(),
                           columns=info_requester.get_columns_for_spending(),
                           spending_summary_info=info_requester.get_summary_spending_info())


@app.route('/upload_file', methods=['GET', 'POST'])
@login_required
def upload_file():
    form = UploadForm()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_source_details()
    if form.validate_on_submit():
        filename = secure_filename(form.file.data.filename)
        data = form.file.data.read()
        file_id = info_requester.add_new_source([filename, data])
        info_requester.set_recent_source_details([file_id])
        return redirect(url_for('index'))
    return render_template('upload_file.html', title='Upload file with budget data', form=form,
                           file_info=file_info)


# helpers
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
