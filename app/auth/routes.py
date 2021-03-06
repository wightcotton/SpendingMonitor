from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.auth.forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user
from app.models import User
from werkzeug.urls import url_parse
from app.database_access.category_state_access import CategoryStateAccess


@app.route('/login', methods=['GET', 'POST'])
def login():
    # for now, just have this user and do not allow people to register but still have to login
    """
    db.session.query(User).filter(User.username == 'bob').delete(synchronize_session=False)
    # clean up old users, TODO build user admin page and file admin
    # default_user = User(username='bob', email='b@bibbbo.com')
    default_user.set_password('time_flies!!!!')
    db.session.add(default_user)
    db.session.commit()

    default_user = User(username='jessie', email='j@bibbbo.com')
    default_user.set_password('time_flies!!!!')
    db.session.add(default_user)
    db.session.commit()
    """

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
        CategoryStateAccess(user.id).set_default_lookup_states()
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form, file_info=["none yet", "not yet"])
