from flask import Flask, render_template, redirect, url_for, request, make_response
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
import requests
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisissecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:0823@localhost:5432/piton4asmnt'
app.config['SQLALCHEMY TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class Client(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def addToDb(self):
        db.session.add(self)
        db.session.commit()

class Nft(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    
    def addToDb(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def checkInDb(cls, nft_address):
        return cls.query.filter_by(address = nft_address).first()

@login_manager.user_loader
def load_user(user_id):
    return Client.query.get(int(user_id))

with app.app_context():
    db.create_all()

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=100)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=100)])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = Client.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('nft_page'))
            
        return '<h1>Invalid username or password</h1>'
    
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = Client(username=form.username.data, email=form.email.data, password=hashed_password)
        Client.addToDb(new_user)

        return '<h1>New user has been created!</h1>'

    return render_template('signup.html', form=form)


@app.route('/nft_page', methods=['GET'])
@login_required
def nft_page():
    return render_template('nft_page.html', name=current_user.username)


@app.route('/nft_search', methods=['GET'])
def nft_search():
    args = request.args['args']
   
    url = f"https://solana-gateway.moralis.io/nft/mainnet/{args}/metadata"

    headers = {

        "accept": "application/json",

        "X-API-Key": "ehP9BUwX165OuRbiGBRu1CoJzKC9hI3IaTTBGSb3MjJ139NS6T6wcWrHBK7P25SD"

    }

    response = requests.get(url, headers=headers)

    nft = Nft()                                     
    dbExist = nft.checkInDb(args)


    if dbExist:
        payload = dbExist
        return make_response(render_template('nft_result.html', payload=payload))

    response2 = response.json()
   
    
    payload = {
        "name": response2["name"],
        "description": response2["metaplex"]["metadataUri"],
        "address": response2["mint"]

    }

    nft = Nft(**payload)

    nft.addToDb()
    
    return make_response(render_template('nft_result.html', payload=payload))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
