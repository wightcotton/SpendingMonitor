from flask import render_template, flash, redirect, url_for, request, session
from app import app, db
from config import Config
from app.forms import UploadForm, HomeForm, FileAdminForm, CategorySummaryForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, UploadedFile
from app.analysis.info_request_interface import InfoRequestHandler
from app.old_working_data import DataObjectFactory_old
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import date


@app.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_source_details()
    if not file_info:
        return redirect(url_for('upload_file'))  # someday need to abstract this
    return render_template('categories.html',
                           file_info=[file_info[0], file_info[1]],
                           title='Categories',
                           today=date.today(),
                           items=info_requester.get_category_info_by(['category_type', 'frequency_index']))


@app.route('/category_summary/<category>', methods=['GET', 'POST'])
@login_required
def category_summary(category):
    form = CategorySummaryForm()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_source_details()
    if category in session["categories_to_be_examined"]:
        look_into = True
    else:
        look_into = False
    if not file_info:
        return redirect(url_for('upload_file'))  # someday need to abstract this
    if category in session['categories_to_be_examined']:
        form.is_good_button()
    if request.method == 'POST':
        if form.look_into_button.data:
            session['categories_to_be_examined'].append(category)
        elif form.is_good_button:
            session['categories_to_be_examined'].remove(category)
    return render_template('category_summary.html',
                           form=form,
                           file_info=[file_info[0], file_info[1]],
                           title=category + ' summary',
                           today=date.today(),
                           look_into= look_into,
                           frequency=info_requester.get_frequency(category),
                           columns=info_requester.get_columns_for_spending(),
                           spending_summary_info=info_requester.get_category_detail(category=category),
                           metadata_items=info_requester.get_category_metadata(category=category),
                           items=info_requester.get_items_for(category=category))


@app.route('/file_admin', methods=['GET', 'POST'])
@login_required
def file_admin():
    form = FileAdminForm()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_source_details()
    if not file_info:
        return redirect(url_for('upload_file'))  # someday need to abstract this
    form.files.choices = [(f.id, f.filename + "; " + str(f.uploaded_timestamp)) for f in
                          info_requester.get_source_list()]
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
                           file_info=file_info)


@app.route('/frequency_categories/<frequency>', methods=["GET"])
@login_required
def frequency_categories(frequency):
    #    form = Form()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_source_details()
    return render_template('frequency_categories.html', title='summary of categories for ' + frequency,
                           file_info=[file_info[0], file_info[1]],
                           frequency=frequency,
                           spending_summary_info=info_requester.get_category_details_for(frequency=frequency),
                           items=info_requester.get_category_metadata(frequency=frequency))


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    if 'categories_to_be_examined' not in session:
        session['categories_to_be_examined'] = []
    form = HomeForm()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_source_details()
    if not file_info:
        return redirect(url_for('upload_file'))  # someday need to abstract this
    return render_template('index.html',
                           file_info=[file_info[0], file_info[1]],
                           title='Home',
                           today=date.today(),
                           columns=info_requester.get_columns_for_spending(),
                           topline_spending_summary=info_requester.get_top_line_spending_info())


@app.route('/items/<category>', methods=["GET"])
@login_required
def items(category):
    #    form = Form()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_source_details()
    return render_template('items.html', title='All Items', file_info=[file_info[0], file_info[1]],
                           subtitle=category,
                           items=info_requester.get_items_for(category=category))


@app.route('/recent_category_items/<category>', methods=["GET"])
@login_required
def recent_category_items(category):
    #    form = Form()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_source_details()
    return render_template('recent_items.html', title='Recent Items', file_info=[file_info[0], file_info[1]],
                           subtitle=category,
                           items=info_requester.get_recent_items_for(category=category))


@app.route('/recent_frequency_items/<frequency>', methods=["GET"])
@login_required
def recent_frequency_items(frequency):
    #    form = Form()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_source_details()
    return render_template('recent_items.html', title='Recent Items', file_info=[file_info[0], file_info[1]],
                           subtitle=frequency,
                           items=info_requester.get_recent_items_for('expense', frequency=frequency))


@app.route('/spending_analysis', methods=['GET', 'POST'])
@login_required
def spending_analysis():
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_source_details()
    if not file_info:
        return redirect(url_for('upload_file'))  # someday need to abstract this
    # spending summary
    return render_template('spending_analysis.html',
                           file_info=[file_info[0], file_info[1]],
                           title='Home',
                           today=date.today(),
                           annual_budget=info_requester.get_monthly_budget() * 12,
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
