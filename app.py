from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import os
from dotenv import load_dotenv
import logging
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

def get_db_connection():
    DB_HOST = os.getenv("DB_HOST")
    DB_USER = os.getenv("DB_USER")
    DB_NAME = os.getenv("DB_NAME")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    return mysql.connector.connect(
        host= DB_HOST,
        user= DB_USER,
        password= DB_PASSWORD,
        database= DB_NAME
    )

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary= True)
            cursor.execute("select * from users where email = %s and password = %s", (email, password))
            user = cursor.fetchone()
            conn.close()
            if user:
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                return redirect(url_for("welcome"))
            else:
                flash("Invalid email or password, please try again")
        except Exception as e:
            logging.error("Error during login: %s", e)
            flash("Something went wrong please try again later")
    return render_template("login.html")

@app.route("/signup", methods = ["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("select * from users where email = %s", (email,))
            existing = cursor.fetchone()
            if existing:
                flash("Email already registred, please login")
                conn.close()
                return redirect(url_for("login"))
            cursor.execute(
                "insert into users (name, email, password, phone_number) values (%s, %s, %s, %s)", (name, email, password, phone)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            session["user_id"] = user_id
            session["user_name"] = name
            flash("Account created succesfully ")
            return redirect(url_for("welcome"))
        except Exception as e:
            logging.error("Error during signup: %s", e)
            flash("Something went wrong please try again later")
    return render_template("signup.html")

@app.route("/welcome")
def welcome():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("welcome.html", name = session["user_name"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/restaurants")
def restaurants():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary= True)
        cursor.execute("select * from restaurants")
        all_restaurants = cursor.fetchall()
        conn.close()
        return render_template("restaurants.html", restaurants = all_restaurants)
    except Exception as e:
        logging.error("Error fetching restaurants: %s", e)
        flash("Something went wrong please try again later")
        return redirect(url_for("welcome"))
    
@app.route("/reserve_restaurant/<int:restaurant_id>", methods = ["GET", "POST"])
def reserve_restaurant(restaurant_id):
    if request.method == "POST":
        reservation_time = request.form["reservation_time"]
        number_of_seats = request.form["number_of_seats"]
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Reservations (user_id, restaurant_id, reservation_time, number_of_seats) VALUES (%s, %s, %s, %s)",
                (session["user_id"], restaurant_id, reservation_time, number_of_seats)
            )
            conn.commit()
            conn.close()
            flash("Restaurant reservation created successfully")
            return redirect(url_for("restaurants"))
        except Exception as e:
            logging.error("Error creating reservation: %s", e)
            flash("Something went wrong. Please try again later.")
            return redirect(url_for("restaurants"))
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary= True)
        cursor.execute("select * from restaurants where id = %s", (restaurant_id,))
        restaurant= cursor.fetchone()
        conn.close()
    except Exception as e:
        logging.error("Error fetching restaurant: %s", e)
        flash("Something went wrong please try again later")
        return redirect(url_for("restaurants"))
    return render_template("reserve_restaurant.html", restaurant = restaurant)
        
@app.route("/accommodation")
def accommodation():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary= True)
    cursor.execute("select * from accommodations")
    all_accommodations = cursor.fetchall()
    conn.close()
    return render_template("accommodations.html", accommodations = all_accommodations)

@app.route("/flights")
def flights():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("select * from flights")
        all_flights = cursor.fetchall()
        conn.close()
        return render_template("flights.html", flights = all_flights)
    except Exception as e:
        logging.error('Error Fetching Flights: %s', e)
        flash('Something went wrong please try again later')
        return redirect(url_for("welcome"))

@app.route("/accommodation_reservations")
def my_accommodation_reservations():
    return render_template("accommodation_reservations.html")

@app.route("/flight_reservations")
def my_flight_reservations():
    return render_template("flight_reservations.html")

@app.route("/my_restaurant_reservations")
def my_restaurant_reservations():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.id, res.name AS restaurant_name, r.reservation_time, r.number_of_seats
            FROM Reservations r
            JOIN Restaurants res ON r.restaurant_id = res.id
            WHERE r.user_id = %s
        """, (session["user_id"],))
        reservations = cursor.fetchall()
        conn.close()
        return render_template("my_restaurant_reservations.html", reservations = reservations)
    except Exception as e:
        logging.error("Error fetching restaurant reservation: %s", e)
        flash("Something went wrong, please try again later")
        return redirect(url_for("welcome"))
    
@app.route("/delete_restaurant_reservation/<int:reservation_id>", methods = ["POST"])
def delete_restaurant_reservation(reservation_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("delete from reservations where id = %s and user_id = %s", (reservation_id, session["user_id"]))
        conn.commit()
        conn.close()
        flash("Reservation deleted successfully")
    except Exception as e:
        logging.error("Error deleting restaurant reservation: %s", e)
        flash("Something went wrong, please try again later.")
    return redirect(url_for("my_restaurant_reservations"))


if __name__ == "__main__":
    app.run(debug=True)