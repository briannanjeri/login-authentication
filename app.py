from flask import Flask,render_template, url_for, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired,Length,ValidationError
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, login_user, LoginManager, login_required,logout_user, current_user
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
import sys



app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://brian:brian@localhost:5432/login'
db=SQLAlchemy(app)
migrate=Migrate(app,db)
bcrypt=Bcrypt(app)
app.config['SECRET_KEY']='thisisasecretkey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view="login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename='user'
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(20), nullable=False, unique=True)
    password=db.Column(db.String(200), nullable=False)

    

      

class RegisterForm(FlaskForm):
    username=StringField(validators=[InputRequired(), Length(min=4, max=20)],
     render_kw={"placeholder":"username"})

    password=PasswordField(validators=[InputRequired(), Length(min=4, max=20)],
     render_kw={"placeholder":"password"})

    submit=SubmitField("Register")


    def validate_username(self, username):
        existing_username=User.query.filter_by(username=username.data).first()

        if existing_username:
            raise ValidationError("This username already exists. choose a different one")



class LoginForm(FlaskForm):
    username=StringField(validators=[InputRequired(), Length(min=4, max=20)],
     render_kw={"placeholder":"username"})

    password=PasswordField(validators=[InputRequired(), Length(min=4, max=20)],
     render_kw={"placeholder":"password"})

    submit=SubmitField("login")


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm()
    print("form>>>> ",form.data['username'])
    try:
        if form.validate_on_submit():
            user=User.query.filter_by(username=form.username.data).first()
            print(user.password)
            if user:
                if bcrypt.check_password_hash(user.password, form.password.data):
                    login_user(user) 
                    return redirect(url_for('dashboard'))

    except SQLAlchemyError as e:
        print("an error occured")
        print(e)
        print(sys.exc_info())
        db.session.rollback() 
    finally:
        db.session.close()            
    return render_template('login.html', form=form)

@app.route('/dashboard', methods=['GET','POST'])
@login_required 
def dashboard():
    return render_template('dash/index.html')

@app.route('/logout', methods=['GET','POST'])
@login_required
def logout():
    logout_user() 
    return redirect(url_for('login'))


@app.route('/register',methods=['GET','POST'])
def register():
    form=RegisterForm()
    try:
        if form.validate_on_submit():
            hashed_password= bcrypt.generate_password_hash(form.password.data).decode('utf8')
            new_user= User(username=form.username.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login'))
    except SQLAlchemyError as e:
        print(" an error occured")
        print(e)
        print(sys.exc_info())
        db.session.rollback()  
        abort(404)
    finally:
        db.session.close() 
    return render_template('register.html',form=form)


if __name__=='__main__':
    app.run(debug=True)   

     