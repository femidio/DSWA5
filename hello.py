import os
import requests
from flask import Flask, render_template, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mailgun configuration
MAILGUN_API_KEY = 'c201a58e2dcd66893f96e619ca21fdb3'
MAILGUN_DOMAIN = 'sandboxXYZ.mailgun.org'  # Replace with your Mailgun sandbox domain

bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username

class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    role = SelectField(u'Role?:', choices=[('Administrator'), ('Moderator'), ('User')])
    submit = SubmitField('Submit')

def send_email(subject, recipient, body):
    return requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={"from": "Flask App <mailgun@{MAILGUN_DOMAIN}>",
              "to": recipient,
              "subject": subject,
              "text": body})

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    user_all = User.query.all()
    role_all = Role.query.all()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user_role = Role.query.filter_by(name=form.role.data).first()
            user = User(username=form.name.data, role=user_role)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
            
            # Send email notification
            email_subject = "New User Registration"
            email_body = f"User {form.name.data} has registered with role {form.role.data}."
            recipients = ["flaskaulasweb@zohomail.com", "emidio.francisco@aluno.ifsp.edu.br"]
            for recipient in recipients:
                send_email(email_subject, recipient, email_body)
            
            flash(f"Emails sent to {recipients}", "success")

        else:
            session['known'] = True
        
        session['name'] = form.name.data
        return redirect(url_for('index'))

    return render_template('index.html', form=form, name=session.get('name'),
                           known=session.get('known', False),
                           user_all=user_all, role_all=role_all)

if __name__ == '__main__':
    app.run(debug=True)
