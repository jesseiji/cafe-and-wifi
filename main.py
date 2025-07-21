from flask import Flask, render_template, request, redirect, url_for, abort
from flask_bootstrap import Bootstrap4
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, URL
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from dotenv import load_dotenv
import requests
import os
from random import choice

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
API_KEY = os.environ.get('GOOGLE_API_KEY')
Bootstrap4(app)

class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

with app.app_context():
    db.create_all()

class CafeForm(FlaskForm):
    name = StringField('Cafe Name', validators=[DataRequired()])
    location = StringField('Location/City', validators=[DataRequired()])
    map_url = StringField('Google Map URL', validators=[DataRequired(), URL()])
    seats = SelectField('Amount of Seats', choices=['0-10', '10-20', '20-30', '40-50', '50+'], validators=[DataRequired()])
    coffee_price = StringField('Average Coffee Price (GBP)', validators=[DataRequired()])
    has_wifi = SelectField('Has Wifi', choices=['True', 'False'], validators=[DataRequired()])
    has_sockets = SelectField('Has Power Sockets', choices=['True', 'False'], validators=[DataRequired()])
    has_toilet = SelectField('Has Bathrooms', choices=['True', 'False'], validators=[DataRequired()])
    can_take_calls = SelectField('Takes Phone Calls', choices=['True', 'False'], validators=[DataRequired()])
    submit = SubmitField('Submit Post')

class Delete(FlaskForm):
    sure = SelectField('Are You Sure?', choices=['Yes', 'No'], validators=[DataRequired()])
    submit = SubmitField('Submit')

def to_dict(self):
    return {column.name: getattr(self, column.name) for column in self.__table__.columns}

is_checked = []
req_list = ['has_wifi', 'has_sockets', 'has_toilet', 'can_take_calls', 'Has Reliable Wifi', 'Has Power Sockets',
                'Has Restrooms', 'Takes Calls']

@app.route('/', methods=['GET', 'POST'])
def home():
    global is_checked, req_list
    cafes = [to_dict(cafe) for cafe in Cafe.query.order_by(Cafe.id).all()]

    if request.method == 'POST':
        for req in req_list[:4]:
            if req in request.form:
                if req not in is_checked:
                    is_checked.append(req)
            else:
                if req in is_checked:
                    is_checked.remove(req)

    def check_req(checklist:list, cafe:dict):
        target = len(checklist)
        count = 0
        for check in checklist:
            if cafe[check]:
                count += 1

        if count == target:
            return True
        else:
            return False

    return render_template('index.html', cafes=cafes, len=len, int=int, req_list=req_list, search=False, is_checked=is_checked, check_req=check_req)

@app.route('/search', methods=['GET'])
def search():
    global req_list
    cafes = [to_dict(cafe) for cafe in Cafe.query.order_by(Cafe.id).all()]

    new_cafes = []

    if request.method == 'GET':
        query = request.args.get('q')
        for cafe in cafes:
            words = [word for word in cafe['name'].lower().split()]
            chars = []
            for word in words:
                chars_ = [char for char in word]
                chars.append(chars_)

            q_charsets = [charset for charset in query.lower().split()]
            word_count = len(q_charsets)
            correct_words = 0

            for q_charset in q_charsets:
                for charset in chars:
                    word_len = len(q_charset)
                    count = 0
                    for char in range(word_len):
                        try:
                            if charset[char] == q_charset[char]:
                                count += 1
                        except IndexError:
                            pass
                    if count == word_len and cafe not in new_cafes:
                        correct_words += 1
                        if correct_words == word_count:
                            new_cafes.append(cafe)

    return render_template('index.html', cafes=new_cafes, len=len, req_list=req_list, search=True, query=query.lower(), int=int)

@app.route('/cafe/<int:cafe_id>')
def show_cafe(cafe_id):
    global req_list
    cafe = to_dict(db.session.get(Cafe, cafe_id))

    if not cafe:
        abort(404, description='Cafe not found')
    else:
        url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json'
        params = {
            'input': cafe['name'],
            'inputtype': 'textquery',
            'fields': 'place_id',
            'key': API_KEY
        }

        response = requests.get(url, params=params).json()
        try:
            map_url = f'https://www.google.com/maps/embed/v1/place?key={API_KEY}&q=place_id:{response['candidates'][0]['place_id']}'
            found = True
        except IndexError:
            map_url = f'https://www.google.com/maps/embed/v1/place?key={API_KEY}&q=London'
            found = False

        return render_template('cafe.html', cafe=cafe, cafes=[to_dict(cafe) for cafe in Cafe.query.order_by(Cafe.id).all()], url=map_url, int=int, len=len, found=found, req_list=req_list)

@app.route('/add', methods=['GET', 'POST'])
def add():
    form = CafeForm()

    def check_bool(q):
        return q == 'True'

    if form.validate_on_submit():
        new_cafe = Cafe(
            name=request.form.get('name'),
            map_url=request.form.get('map_url'),
            location=request.form.get('location'),
            has_sockets=check_bool(request.form.get('has_sockets')),
            has_toilet=check_bool(request.form.get('has_toilet')),
            has_wifi=check_bool(request.form.get('has_wifi')),
            can_take_calls=check_bool(request.form.get('can_take_calls')),
            seats=request.form.get('seats'),
            coffee_price=f'£{request.form.get('coffee_price')}'
        )
        db.session.add(new_cafe)
        db.session.commit()

        return redirect(url_for('show_cafe', cafe_id=new_cafe.id))

    return render_template('add.html', form=form)

@app.route('/delete/<int:cafe_id>', methods=['GET', 'POST'])
def delete(cafe_id):
    form = Delete()
    cafe = db.session.get(Cafe, cafe_id)

    if form.validate_on_submit():
        if request.form.get('sure') == 'Yes':
            db.session.delete(cafe)
            db.session.commit()

        return redirect(url_for('home'))

    return render_template('delete.html', form=form, cafe=cafe)

if __name__ == '__main__':
    app.run(debug=True)
