import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from foodsafe import app, db, bcrypt
from foodsafe.forms import RegistrationForm, LoginForm, UpdateAccountForm, DonateForm
from foodsafe.models import User, Donate
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
def cover():
    cover_img = url_for('static', filename='profile_pics/cover.jpg')
    return render_template('cover.html',cover_img=cover_img)

@app.route("/home")

def home():
    page = request.args.get('page', 1, type=int)
    donations = Donate.query.order_by(Donate.date_donate.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', donations = donations)



@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password,address= form.address.data, phone_number= form.phone_number.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=current_user.username).first_or_404()
    donations = Donate.query.filter_by(author=user)\
        .order_by(donations.date_posted.desc())\
        .paginate(page=page, per_page=5)
    donations_count = len(Donate.query.filter_by(user_id=current_user.id).all())
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form, donations_count=donations_count, donations=donations, user=user)


@app.route("/donate/new", methods=['GET', 'POST'])
@login_required
def new_donate():
    form = DonateForm()
    if form.validate_on_submit():
        donate = Donate( content=form.content.data, author=current_user)
        db.session.add(donate)
        db.session.commit()
        flash('Your donation has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_donate.html', title='donot waste, Donate it',
                           form=form, legend='donation')


@app.route("/donate/<int:donate_id>")
def donate(donate_id):
    donate = Donate.query.get_or_404(donate_id)
    return render_template('donate.html', donate=donate)


@app.route("/donate/<int:donate_id>/update", methods=['GET', 'POST'])
@login_required
def update_donate(donate_id):
    donate = Donate.query.get_or_404(donate_id)
    if donate.author != current_user:
        abort(403)
    form = DonateForm()
    if form.validate_on_submit():
        donate.content = form.content.data
        db.session.commit()
        flash('Your donation has been updated!', 'success')
        return redirect(url_for('donate', donate_id=donate.id))
    elif request.method == 'GET':
        form.content.data = donate.content
    return render_template('create_donate.html', title='Update donation',
                           form=form, legend='Update donation')


@app.route("/donate/<int:donate_id>/delete", methods=['POST'])
@login_required
def delete_donate(donate_id):
    donate= Donate.query.get_or_404(donate_id)
    if donate.author != current_user:
        abort(403)
    db.session.delete(donate)
    db.session.commit()
    flash('Your donate has been deleted!', 'success')
    return redirect(url_for('home'))



@app.route("/help_desk")
def help_desk():
    return render_template('help_desk.html', title='Help-Desk')



