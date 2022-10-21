from ssl import VerifyMode
from urllib import response
from flask import Flask, render_template,request,session,redirect,flash,url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import json,os,math
from  flask_mail import Mail

with open('config.json','r') as c:
    params = json.load(c)["params"]

local_server=True
app = Flask(__name__)
app.secret_key="super-secret-key"
app.config.update(
    MAIL_SERVER = 'smtp.office365.com',
    MAIL_PORT = '587',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)
app.config["UPLOAD_FOLDER"] = params['upload_location']
mail = Mail(app)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg'}
if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params["local_uri"]
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["prod_uri"]

db = SQLAlchemy()
db.init_app(app)



class Contact(db.Model):
    # sno,name,phn_num,msg,date,email
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phn_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)


class Posts(db.Model):
    # sno,name,phn_num,msg,date,email
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(25), nullable=True)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    if page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    
    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)



    posts = Posts.query.filter_by().all()[1:params['no_of_posts']]
    return render_template('index.html',params=params,posts=posts)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():

    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)


    elif(request.method=='POST'):
        username = request.form.get('uname')
        password = request.form.get('pass')
        if(username==params['admin_user'] and password==params['admin_pass']):  
            #set the secret key
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params)
            
        else:
            flash("Invalid Credentials")

    return render_template("login.html",params=params)

@app.route("/edit/<string:sno>", methods = ['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            if img_file==None:
                img_file = "about-bg.jpg"
            date = datetime.now()

            if sno == '0':
                post = Posts(title=box_title, slug=slug, content=content, tagline=tagline, img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tagline
                post.img_file = img_file
                db.session.commit()
                return redirect('/edit/'+ str(post.sno))

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params,post=post)

@app.route("/delete/<string:sno>", methods = ['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')





@app.route("/post/<string:slug>",methods = ['GET'])
def post_route(slug):
    post = Posts.query.filter_by(slug=slug).first()
    return render_template('post.html',params=params,post=post)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
#create a upload route
@app.route("/uploader",methods = ['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if (request.method == 'POST'):
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                return redirect('/dashboard')
    return redirect(request.url)

@app.route("/about")
def about():
    return render_template('about.html',params=params)

@app.route("/contact",methods=["GET","POST"])
def contact():
    if (request.method=="POST"):
        name = request.form.get('name')
        email = request.form.get('email')
        phn_num = request.form.get('phn_num')
        msg = request.form.get('msg')
        entry = Contact(name=name,phn_num=phn_num,msg=msg,date=datetime.now(),email=email)
        db.session.add(entry)
        db.session.commit()
        import smtplib, ssl
        port = 587  # For starttls
        receiver_email = "omkaredgaonkar@gmail.com"
        smtp_server = "smtp.office365.com"
        sender_email = "omkaredgaonkar@outlook.com"
        password = "Omkarae@07"
        message = 'New message from blog'
        #  + msg + 'from' + name + 'email' + email + 'phone number' + phn_num
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
        # mail.send_message('New message from blog',
        #                     sender=email,
        #                     recipients=[params['gmail-user']],
        #                     body=msg + "\n" + phn_num 
        #                 )
    return render_template('contact.html',params=params)

    
app.run(port=5001,debug=True)