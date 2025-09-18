from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import os
from dotenv import load_dotenv
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
    return render_template("login.html")

@app.route("/signup", methods = ["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]
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
    return "<h2>Restaurants Page</h2>"
 
@app.route("/accommodation")
def accommodation():
    return "<h2>Accommodation Page</h2>"

@app.route("/flights")
def flights():
    return "<h2>Flights Page</h2>"
        
if __name__ == "__main__":
    app.run(debug=True)