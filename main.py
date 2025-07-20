from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, select
from dotenv import load_dotenv
import requests
import os
from random import choice

load_dotenv()

app = Flask(__name__)
API_KEY = os.environ.get('GOOGLE_API_KEY')

# CREATE DB
class Base(DeclarativeBase):
    pass
# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Cafe TABLE Configuration
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

def to_dict(self):
    return {column.name: getattr(self, column.name) for column in self.__table__.columns}

is_checked = []

@app.route('/', methods=['GET', 'POST'])
def home():
    global is_checked
    cafes = [to_dict(cafe) for cafe in Cafe.query.order_by(Cafe.id).all()]
    req_list = ['has_wifi', 'has_sockets', 'has_toilet', 'can_take_calls', 'Has Reliable Wifi', 'Has Power Sockets',
                'Has Restrooms', 'Takes Calls']

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

    return render_template("index.html", cafes=cafes, len=len, int=int, req_list=req_list, search=False, is_checked=is_checked, check_req=check_req)

@app.route('/search', methods=["GET"])
def search():
    cafes = [to_dict(cafe) for cafe in Cafe.query.order_by(Cafe.id).all()]
    req_list = ['has_wifi', 'has_sockets', 'has_toilet', 'can_take_calls', 'Has Reliable Wifi', 'Has Power Sockets',
                'Has Restrooms', 'Takes Calls']

    new_cafes = []

    if request.method == "GET":
        query = request.args.get('q')
        for cafe in cafes:
            words = [word for word in cafe['name'].lower().split()]
            chars = []
            for word in words:
                chars_ = [char for char in word]
                chars.append(chars_)

            q_chars = [char for char in query.lower()]
            for charset in chars:
                word_len = len(q_chars)
                count = 0
                for char in range(word_len):
                    try:
                        if q_chars[char] == charset[char]:
                            count += 1
                    except IndexError:
                        pass
                if count == word_len:
                    new_cafes.append(cafe)

    return render_template('index.html', cafes=new_cafes, len=len, req_list=req_list, search=True, query=query.lower())

@app.route('/cafe/<int:cafe_id>')
def show_cafe(cafe_id):
    req_list = ['has_wifi', 'has_sockets', 'has_toilet', 'can_take_calls', 'have reliable wifi', 'have power sockets',
                'have restrooms', 'take calls']

    cafe = to_dict(db.session.get(Cafe, cafe_id))
    if not cafe:
        abort(404, description='Cafe not found')
    else:
        url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        params = {
            "input": cafe['name'],
            "inputtype": "textquery",
            "fields": "place_id",
            "key": API_KEY
        }

        response = requests.get(url, params=params).json()
        try:
            map_url = f'https://www.google.com/maps/embed/v1/place?key={API_KEY}&q=place_id:{response['candidates'][0]['place_id']}'
            found = True
        except IndexError:
            map_url = f'https://www.google.com/maps/embed/v1/place?key={API_KEY}&q=London'
            found = False

        return render_template('cafe.html', cafe=cafe, url=map_url, int=int, len=len, found=found, req_list=req_list)

# # HTTP POST - Create Record
# @app.route("/add", methods=["POST"])
# def add():
#     if request.method == "POST":
#         try:
#             new_cafe = Cafe(
#                 name=request.form.get("name"),
#                 map_url=request.form.get("map_url"),
#                 img_url=request.form.get("img_url"),
#                 location=request.form.get("loc"),
#                 has_sockets=bool(request.form.get("sockets")),
#                 has_toilet=bool(request.form.get("toilet")),
#                 has_wifi=bool(request.form.get("wifi")),
#                 can_take_calls=bool(request.form.get("calls")),
#                 seats=request.form.get("seats"),
#                 coffee_price=request.form.get("coffee_price")
#             )
#             db.session.add(new_cafe)
#             db.session.commit()
#
#             response = {"success": "Successfully added the new cafe."}
#             return jsonify(response=response)
#
#         except:
#             error = {"fail": "Failed to add new cafe. Possibly missing field(s)?"}
#             return jsonify(error=error)
#
# # HTTP PUT/PATCH - Update Record
# @app.route("/update-price/<int:cafe_id>", methods=["PATCH"])
# def update_price(cafe_id):
#     new_price = request.args.get("new-price")
#     try:
#         cafe = db.session.get(Cafe, cafe_id)
#     except AttributeError:
#         return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404
#     else:
#         cafe.coffee_price = new_price
#         db.session.commit()
#         return jsonify(response={"success": "Successfully updated the price."}), 200
#
# # HTTP DELETE - Delete Record
# @app.route("/report-closed/<int:cafe_id>", methods=["DELETE"])
# def delete(cafe_id):
#     api_key = request.args.get("api-key")
#     if not api_key == "TopSecretAPIKey":
#         return jsonify(error={"Access Denied": "You do not have permission to access this. Make sure "
#                                                "you have the correct API key."})
#     else:
#         try:
#             cafe = db.session.get(Cafe, cafe_id)
#             db.session.delete(cafe)
#             db.session.commit()
#             return jsonify(response={"success": "Successfully deleted cafe from the database."})
#         except AttributeError:
#             return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."})

if __name__ == '__main__':
    app.run(debug=True)
