from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:3306/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'YhHCK4QNG9yhqD'

# tables for database
class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    blogs =db.relationship('Blog', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.pw_hash = make_pw_hash(password)

#forces user to sign in before using site
@app.before_request
def require_login():
    allowed_routes = ['login', 'signup']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')

#home index page that list all blog users as links
@app.route('/index')
def index():
    users = User.query.all()
    return render_template('index.html', users=users, title="Blogz!")

#function to check user and password
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_pw_hash(password, user.pw_hash):
            session['email'] = email
            flash('Logged In', 'info')
            return redirect('/')   #redirect to main page
        else:   #return error if email/password is incorrect or registered
            flash('User name or password is incorrect or doesnt exist', 'danger')

    return render_template('login.html')

#signup new users
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    else:
        email =request.form['email']
        password = request.form['password']
        verify = request.form['verify']
        empty_error = ''
        email_error = ''
        password_error = ''
        verify_error = ''
        existing_user = User.query.filter_by(email=email).first()
#validating registration for new user
        if existing_user:
            empty_error = "An account with that email already exists."       
        if email.count('@') != 1 and '.com' not in email:
            email_error = "Please enter a vaild email"
            email = ''
        if len(password) < 6 or len(password) > 20:
            password_error = "Please select a password between 6 and 20 characters."
            password = ''
            if '' in password:
                password_error = "Please select a password between 6 and 20 characters."
                password = ''
        if password != verify:
            verify_error = "Be sure your passwords match!"
#creating new user and adding to database if no register errors
        if not existing_user and not empty_error and not email_error and not password_error and not verify_error:
            new_user = User(email, password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            return redirect('/newpost') # redirect to the main page
        else:# return registration errors
            return render_template('signup.html', email=email, empty_error=empty_error,email_error=email_error, password_error=password_error,verify_error=verify_error)

#user signout - deleting the session for user
@app.route('/logout', methods=['POST'])
def logout():
    del session['email']
    return redirect('/')

# this page displays blog entrys submitted by all website members
# main page after login 
@app.route('/blog', methods=['POST', 'GET'])
def blog_list():
    posts = Blog.query.all()
    blog_id = request.args.get('id')
    user_id = request.args.get('user')
    user = User.query.filter_by(email=user_id).first()
    user_posts = Blog.query.filter_by(owner=user).all()
    owner = User.query.filter_by(email=session['email']).first()
    owner_posts = Blog.query.filter_by(owner=owner).all()
    blog = Blog.query.filter_by(id=blog_id).first()

    #if no user is selected, show all blog posts
    if not blog_id and not user_id:
        return render_template('blog.html', title="Blogz!", posts=posts)
    #if a blog is selected, only show it
    elif blog_id:
        return render_template('posts.html', blog=blog, user=user, user_posts=user_posts)
    #if a user is selected, show all of their posts
    elif user_id:
        return render_template('entry.html', blog=blog, user=user, user_posts=user_posts)

#view just a list of your posts
@app.route('/myblog', methods=['POST','GET'])
def my_blog():
    posts = Blog.query.all()
    blog_id = request.args.get('id')
    owner = User.query.filter_by(email=session['email']).first()
    owner_posts = Blog.query.filter_by(owner=owner).all()
    blog = Blog.query.filter_by(id=blog_id).first()
    return render_template('myblog.html', blog=blog, owner=owner, owner_posts=owner_posts)

#this page is for new blog entry
#this page can be accessed from main page
@app.route('/newpost', methods=['POST', 'GET'])
def new_post():
    if request.method == 'POST':
        blog_title = request.form['title']
        blog_body = request.form['body']
        blog_owner = User.query.filter_by(email=session['email']).first()
        title_error = ''
        body_error = ''

        if not blog_title:
            title_error = "Please enter a blog title"
    
        if not blog_body:
            body_error = "Please enter a blog entry"

        if not body_error and not title_error:
            new_entry = Blog(blog_title, blog_body, blog_owner)     
            db.session.add(new_entry)
            db.session.commit()        
            return redirect('/blog?id={}'.format(new_entry.id)) 
        else:
            return render_template('newpost.html', title='New Entry', title_error=title_error, body_error=body_error, 
                blog_title=blog_title, blog_body=blog_body)
    
    return render_template('newpost.html', title='New Entry')

if __name__ == '__main__':
    app.run()