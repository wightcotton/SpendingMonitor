from flask import render_template, redirect, url_for, request, session
from app import app
from config import Config
from app.forms import UploadForm, HomeForm, FileAdminForm, CategorySummaryForm, StateAdminForm
from flask_login import current_user, login_required
from app.info_request_interface import InfoRequestHandler
from werkzeug.utils import secure_filename
from datetime import date


# manage routing within the app
# get data through data requester, which marshalls the data sources


@app.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_file_details()
    if not file_info:
        return redirect(url_for('upload_file'))  # someday need to abstract this
    return render_template('categories.html',
                           file_info=[file_info[0], file_info[1]],
                           title='Categories',
                           today=date.today(),
                           items=info_requester.get_category_info(['category_type', 'frequency_index']))


@app.route('/category/<cat>', methods=['GET', 'POST'])
@login_required
def category(cat):
    form = CategorySummaryForm()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_file_details()
    if not file_info:
        return redirect(url_for('upload_file'))  # someday need to abstract this
    # few categories will have existing state
    if request.method == 'POST':
        if form.change_state.data:
            info_requester.set_category_current_state(cat, form.state_radio_button.data)
        elif form.delete_prev_states_button.data:
            info_requester.delete_category_states(cat)
        redirect(url_for('category', cat=cat))
    form.state_radio_button.choices = [(s.id, s.state) for s in (info_requester.get_state_lookups() or [])]
    form.state_radio_button.default = info_requester.get_current_state_id(cat) or 0
    form.prev_states.choices = [(index, str(s.StateLookup.state) + ' @ ' + str(s.CategoryState.timestamp))
                                for s in (info_requester.get_category_state_info(cat))]
    form.process()
    return render_template('category_summary.html',
                           form=form,
                           file_info=[file_info[0], file_info[1]],
                           title=cat + ' summary',
                           today=date.today(),
                           frequency=info_requester.get_frequency(cat),
                           columns=info_requester.get_columns_for_spending_summary(),
                           spending_summary_info=info_requester.get_cat_summary_spending_info(list_of_categories=[cat]),
                           headings=info_requester.get_category_metadata_headings(),
                           metadata=info_requester.get_category_metadata(category=cat),
                           items=info_requester.get_items_for(category=cat))


@app.route('/file_admin', methods=['GET', 'POST'])
@login_required
def file_admin():
    form = FileAdminForm()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_file_details()
    if not file_info:
        return redirect(url_for('upload_file'))  # someday need to abstract this
    form.files.choices = [(f.id, f.filename + "; " + str(f.uploaded_timestamp)) for f in
                          info_requester.get_source_list()]
    if request.method == 'POST':
        if form.select.data:
            info_requester.set_recent_file_details([int(form.files.data)])
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
    file_info = info_requester.get_file_details()
    return render_template('frequency_categories.html', title='summary of categories for ' + frequency,
                           file_info=[file_info[0], file_info[1]],
                           frequency=frequency,
                           headings=info_requester.get_category_metadata_headings(),
                           metadata=info_requester.get_category_metadata(frequency=frequency))


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    if 'categories_to_be_examined' not in session:
        session['categories_to_be_examined'] = []
    form = HomeForm()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_file_details()
    if not file_info:
        return redirect(url_for('upload_file'))  # someday need to abstract this
    return render_template('index.html',
                           file_info=[file_info[0], file_info[1]],
                           title='Home',
                           today=date.today(),
                           annual_budget=info_requester.get_budget_for(category_type='expense') * 12,
                           columns=info_requester.get_columns_for_spending_summary(),
                           topline_spending_summary=info_requester.get_top_line_spending_info(),
                           freq_examine_list=info_requester.get_freq_examine_list(),
                           cat_examine_list=info_requester.get_cat_examine_list(),
                           categories_by_state=info_requester.get_categories_by_current_state())


@app.route('/info')
@login_required
def info():
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_file_details()
    return render_template('info.html',
                           file_info=[file_info[0], file_info[1]])


@app.route('/items/<category>', methods=["GET"])
@login_required
def items(category):
    #    form = Form()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_file_details()
    return render_template('items.html', title='All Items', file_info=[file_info[0], file_info[1]],
                           subtitle=category,
                           items=info_requester.get_items_for(category=category))


@app.route('/recent_category_items/<category>', methods=["GET"])
@login_required
def recent_category_items(category):
    #    form = Form()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_file_details()
    return render_template('recent_items.html', title='Recent Items', file_info=[file_info[0], file_info[1]],
                           subtitle=category,
                           items=info_requester.get_recent_items_for(category=category))


@app.route('/recent_frequency_items/<frequency>', methods=["GET"])
@login_required
def recent_frequency_items(frequency):
    #    form = Form()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_file_details()
    return render_template('recent_items.html', title='Recent Items', file_info=[file_info[0], file_info[1]],
                           subtitle=frequency,
                           items=info_requester.get_recent_items_for('expense', frequency=frequency))


@app.route('/spending_analysis', methods=['GET', 'POST'])
@login_required
def spending_analysis():
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_file_details()
    if not file_info:
        return redirect(url_for('upload_file'))  # someday need to abstract this
    return render_template('spending_analysis.html',
                           file_info=[file_info[0], file_info[1]],
                           title='Home',
                           today=date.today(),
                           annual_budget=info_requester.get_budget_for(category_type='expense') * 12,
                           columns=info_requester.get_columns_for_spending_summary(),
                           spending_summary_info=info_requester.get_freq_summary_spending_info())


@app.route('/state_admin', methods=['GET', 'POST'])
@login_required
def state_admin():
    form = StateAdminForm()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_file_details()
    if not file_info:
        return redirect(url_for('upload_file'))  # someday need to abstract this
    if request.method == 'POST':
        if form.new_state.data:
            info_requester.add_lookup_state(state=form.new_state.data, desc=form.new_state_description.data)
        elif form.delete.data:
            info_requester.delete_lookup_states([int(form.states.data)])
        redirect(url_for('state_admin'))
    form.states.choices = [(s.id, str(s.id) + ': ' + s.state) for s in (info_requester.get_state_lookups() or [])]
    return render_template('state_admin.html',
                           title='files...',
                           form=form,
                           file_info=file_info,
                           categories_by_state=info_requester.get_categories_by_current_state())


@app.route('/upload_file', methods=['GET', 'POST'])
@login_required
def upload_file():
    form = UploadForm()
    info_requester = InfoRequestHandler(current_user.id)
    file_info = info_requester.get_file_details()
    if form.validate_on_submit():
        filename = secure_filename(form.file.data.filename)
        data = form.file.data.read()
        file_id = info_requester.add_new_file([filename, data])
        info_requester.set_recent_file_details([file_id])
        return redirect(url_for('index'))
    return render_template('upload_file.html', title='Upload file with budget data', form=form,
                           file_info=file_info)


# helpers
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
