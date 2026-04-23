import json

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import *
import math



app = Flask(__name__)

with open("config.json") as c:
    param = json.load(c)["parameters"]

if param["local_server"]:
    app.config["SQLALCHEMY_DATABASE_URI"] = param["local_uri"]
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = param["prod_uri"]

app.config["SECRET_KEY"] = param["secret_key"]
db = SQLAlchemy(app)

loginManager = LoginManager()
loginManager.login_view = "login"
loginManager.init_app(app)

class Contact(db.Model):

    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(1000), nullable=False)
    date = db.Column(db.String(50), nullable=False)

class Posts(db.Model):
    post_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    subtitle = db.Column(db.String(500), nullable=False)
    author = db.Column(db.String(500), nullable=False)
    date = db.Column(db.Date)
    location = db.Column(db.String(500), nullable=False)
    image = db.Column(db.String(500), nullable=False)
    content_1 = db.Column(db.Text, nullable=False)
    content_2 = db.Column(db.Text, nullable=False)
    slug = db.Column(db.String(500), unique=True)

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

@app.route('/')
def home():
    post_data = Posts.query.all()
    n = 2
    last = math.ceil(len(post_data)/n)

    page = request.args.get('page')

    if page is None:
        page = 1

    next = "/?page=" + str(int(page)+1)
    prev = "/?page=" + str(int(page)-1)

    if int(page) == last:
        next = "/?page=" + str(1)
        prev = "/?page=" + str(int(page) - 1)
    if int(page) == 1:
        next = "/?page=" + str(int(page) + 1)
        prev = "/?page=" + str(1)
    j = (int(page)-1)*n

    posts = post_data[j : j+n]
    return render_template("index.html", param=param, posts = posts, next=next, prev=prev)

@app.route('/about')
def about():
    return render_template("about.html", param=param)

@loginManager.user_loader
def load_user(user):
    return Users.query.get(int(user))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Users.query.filter_by(username=username).first()
        if user and password == user.password:
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password")
            return render_template("login.html", param=param)
    return render_template("login.html", param=param)

@app.route('/contact', methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        entry = Contact(name=name, email=email, message=message, date=datetime.today().date())
        db.session.add(entry)
        db.session.commit()
    return render_template("contact.html", param=param)

@app.route('/post/<url_slug>')
def slug(url_slug):
    single = Posts.query.filter_by(slug=url_slug).first()
    return render_template("post.html", param=param, post = single)

@app.route('/admin')
@login_required
def dashboard():
    user = current_user.name

    posts = Posts.query.all()
    contact = Contact.query.all()
    return render_template("admin/index.html", param=param, posts = posts, contact = contact, user = user)

@app.route('/editpost/<post_id>', methods=["POST", "GET"])
def edit(post_id):
    if request.method == "POST":
        title = request.form.get("title")
        subtitle = request.form.get("subtitle")
        location = request.form.get("location")
        author = request.form.get("author")
        image = request.form.get("image")
        date = request.form.get("date")
        content_1 = request.form.get("content_1")
        content_2 = request.form.get("content_2")
        slug = request.form.get("slug")
        if post_id == "0":
            entry = Posts(title = title, subtitle = subtitle, location = location, author = author, image = image, date = date, content_1 = content_1, content_2 = content_2, slug = slug)
            db.session.add(entry)
            db.session.commit()
        else:
            post = db.session.query(Posts).filter_by(post_id=post_id).first()
            post.title = title
            post.subtitle = subtitle
            post.location = location
            post.author = author
            post.image = image
            post.date = date
            post.content_1 = content_1
            post.content_2 = content_2
            post.slug = slug
            db.session.commit()
            return redirect(url_for("dashboard"))

    post = db.session.query(Posts).filter_by(post_id=post_id).first()
    return render_template("admin/editpost.html", param=param, post=post)

@app.route('/delete/<post_id>')
def delete(post_id):
    post = db.session.query(Posts).filter_by(post_id=post_id).first()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        user = Users.query.filter_by(email=email).first()
        if user:
            flash("Email already exists")
        else:
            user = Users(name=name, username=username, email=email, password=password)
            db.session.add(user)
            db.session.commit()
    return render_template("admin/signup.html", param=param)
if __name__=='__main__':
    with app.app_context():

        db.create_all()
    app.run(debug=True,port='8082')