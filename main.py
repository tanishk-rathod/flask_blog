from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mysqldb import MySQL
import os,json,math
from flask_mail import Mail,Message



with open("config.json") as c:
	params=json.load(c)["Params"]

local_server = params['local_server']

app = Flask(__name__)

app.secret_key = params["secret_key"]
app.config['UPLOAD_FOLDER']=params['upload_location']


app.config['MAIL_SERVER'] = "smtp.googlemail.com"
app.config['MAIL_USERNAME'] = params['gmail-user']
app.config['MAIL_PORT'] = 587
app.config['MAIL_PASSWORD'] = params['gmail-pass']
app.config['MAIL_USE_TLS'] = True
mail = Mail(app)

if(local_server):
	app.config['SQLALCHEMY_DATABASE_URI'] = params['local_URI']
else:
	app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_URI']


db = SQLAlchemy(app)



class Contacts(db.Model):
	S_no = db.Column(db.Integer, primary_key=True)
	Name = db.Column(db.String(80), primary_key=False, nullable=False)
	Email = db.Column(db.String(20), nullable=False)
	Phone = db.Column(db.Integer, primary_key=False, nullable=False)
	Mes = db.Column(db.String(120), primary_key=False, nullable=False)
	Date = db.Column(db.String(12),primary_key=False,nullable=True)


class Posts(db.Model):
	S_no = db.Column(db.Integer,primary_key=True)
	Slug = db.Column(db.String(50),primary_key=False,nullable=False)
	Title = db.Column(db.String(80),primary_key=False,nullable=False)
	Sub_heading = db.Column(db.String(80),primary_key=False,nullable=False)
	Content = db.Column(db.String(500),primary_key=False,nullable=False)
	Author = db.Column(db.String(20),primary_key=False,nullable=False)
	Img_file = db.Column(db.String(80),primary_key=False,nullable=False)
	Date = db.Column(db.String(12),nullable=False,primary_key=False)



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
        nex = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        nex = "#"
    else:
        prev = "/?page="+ str(page-1)
        nex = "/?page="+ str(page+1)
    
    return render_template('index.html', params=params, posts=posts, prev=prev, next=nex)

@app.route("/about")
def about():
	return render_template("about.html",params=params)

@app.route("/contact", methods = ["GET","POST"])
def contact():
	if(request.method=="POST"):
		name=request.form.get("name")
		email=request.form.get("email")
		phone_num=request.form.get("phone_num")
		mes=request.form.get("message")

		entry = Contacts(Name = name,Phone=phone_num,Email = email,Mes = mes,Date=datetime.now())
		
		db.session.add(entry)
		db.session.commit()
		msg = Message("New Message form "+name, sender=email, recipients=[params['gmail-user']],body = mes+"\n"+phone_num)
		mail.send(msg)
		return redirect("/")

	return render_template("contact.html",params=params)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post(post_slug):
	post = Posts.query.filter_by(Slug=post_slug).first()
	return render_template("post.html",params=params, post=post)


@app.route("/login", methods=['GET', 'POST'])
def login():
	username=request.form.get("username")
	password=request.form.get("password")
	posts = Posts.query.filter_by().all()
	if("user" in session and session["user"]==params["admin_username"]):
		return render_template("dashboard.html", username=params["admin_username"], params=params,posts=posts)


	if(request.method=="POST"):
		if((username==params["admin_username"]) and (password==params["admin_password"])):
			session["user"] = username
			
			return render_template("dashboard.html", username=params["admin_username"], params=params, posts=posts)
	
	return render_template("login.html", params=params)
	return username


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):

	if("user" in session and session["user"]==params["admin_username"]):
		if(request.method=="POST"):
			slug=request.form.get("slug")
			title=request.form.get("title")
			sub_heading=request.form.get("sub_heading")
			content=request.form.get("content")
			author=request.form.get("author")
			img_file=request.form.get("img_file")
			if(sno=="0"):
				entry = Posts(Slug = slug,Title=title,Sub_heading = sub_heading,Content = content,Author=author,Img_file=img_file,Date=datetime.now())
				db.session.add(entry)
				db.session.commit()
				return redirect('/login')

			else:
				post = Posts.query.filter_by(S_no=sno).first()

				post.Slug = slug
				post.Title = title
				post.Sub_heading = sub_heading
				post.Content = content
				post.Author = author
				post.Img_file=img_file
				post.Date = datetime.now()
				
				db.session.commit()
				return redirect('/login')
		post = Posts.query.filter_by(S_no=sno).first()
		return render_template("edit.html", params=params, username=params["admin_username"],sno=sno,post=post)


@app.route('/upload',methods=['POST'])
def upload():
	if("user" in session and session["user"]==params["admin_username"]):
		if(request.method=="POST"):
			f = request.files['file1']
			f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
		return "Uploaded Successfully"

@app.route('/logout')
def logout():
	session.pop("user")
	return redirect("/login")

@app.route('/delete/<string:sno>',methods=['POST','GET'])
def delete(sno):
	if("user" in session and session["user"]==params["admin_username"]):
		post = Posts.query.filter_by(S_no=sno).first()
		db.session.delete(post)
		db.session.commit()
	return redirect("/login")


app.run(debug=True, port=8001)

