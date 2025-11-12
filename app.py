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
            flash("Restaurant reservation created successfully", "success")
            return redirect(url_for("welcome"))

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

@app.route("/my_accommodation_reservations")
def my_accommodation_reservations():
    if "user_id" not in session:
        flash("You need to login to view your reservations", "warning")
        return redirect(url_for("login"))
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
    select 
        o.id as reservation_id,
        a.city as accommodation_name,
        r.room_number,
        r.room_type,
        r.number_of_beds,
        o.entry_date,
        o.leave_date,
        r.price_per_night
    from occupied_rooms o 
    join rooms r on o.room_id = r.id
    join accommodations a on r.accommodation_id = a.id
    where o.user_id = %s
    order by o.entry_date desc
    """
    cursor.execute(query, (user_id,))
    reservations = cursor.fetchall()
    conn.close()
    return render_template("my_accommodation_reservations.html", reservations = reservations)
    
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

@app.route("/reserve_accommodation/<int:accommodation_id>", methods = ["GET", "POST"])
def reserve_accommodation(accommodation_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("select distinct room_type, number_of_beds from rooms where accommodation_id = %s and occupied = 0", (accommodation_id,))
    available_options = cursor.fetchall()
    if request.method == "POST":
        room_type = request.form["room_type"]
        number_of_beds = request.form["number_of_beds"]
        entry_date = request.form["entry_date"]
        leave_date = request.form["leave_date"]
        user_id = session.get("user_id")
        if not user_id:
            flash("You must be logged in to reserve accommodation")
            return redirect(url_for("login"))
        cursor.execute("select id from rooms where accommodation_id = %s and room_type = %s and number_of_beds = %s and occupied = 0 order by price_per_night asc limit 1", (accommodation_id, room_type, number_of_beds,))
        room = cursor.fetchone()
        if room:
            room_id = room["id"]
            cursor.execute("""
                INSERT INTO occupied_rooms (user_id, room_id, entry_date, leave_date)
                VALUES (%s, %s, %s, %s)
            """, (user_id, room_id, entry_date, leave_date))
            cursor.execute("update rooms set occupied = 1 where id = %s", (room_id,))
            conn.commit()
            flash("Accommodation Reserved Successfully", "success")
            return redirect(url_for("welcome"))

        else:
            flash("No Available Rooms Match Your Selection")
    conn.close()
    return render_template("reserve_accommodation.html", options = available_options)

@app.route("/delete_accommodation_reservation/<int:reservation_id>", methods = ["POST"])
def delete_accommodation_reservation(reservation_id):
    if "user_id" not in session:
        flash("You need to login to cancel your reservations", "warning")
        return redirect(url_for("login"))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("select room_id from occupied_rooms where id = %s", (reservation_id,))
        room = cursor.fetchone()
        if room:
            room_id = room[0]
            cursor.execute("delete from occupied_rooms where id = %s", (reservation_id,))
            cursor.execute("update rooms set occupied = 0 where id = %s", (room_id,))
            conn.commit()
            flash("Reservation successfully canceled", "success")
        else:
            flash("Reservation not found", "danger")
        cursor.close()
        conn.close()
    except Exception as e:
        logging.error("Error cancelling reservation: %s", e)
        flash("An error occurred while cancelling the reservation.", "danger")
    return redirect(url_for("my_accommodation_reservations"))

@app.route("/reserve_flight/<int:flight_id>", methods=["GET", "POST"])
def reserve_flight(flight_id):
    if "user_id" not in session:
        flash("You must login to reserve a flight", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db_connection()
    conn.autocommit = False
    cursor = conn.cursor(dictionary=True)

    try:
        # --- Fetch the flight ---
        cursor.execute("SELECT * FROM flights WHERE id = %s", (flight_id,))
        flight = cursor.fetchone()
        if not flight:
            flash("Flight not found", "danger")
            return redirect(url_for("flights"))

        # --- Fetch available seats ---
        cursor.execute("""
            SELECT id, seat_number
            FROM seats
            WHERE flight_id = %s AND occupied = 0
            ORDER BY seat_number
        """, (flight_id,))
        available_seats = cursor.fetchall()

        # --- Handle POST (reservation) ---
        if request.method == "POST":
            chosen_seat_id = request.form.get("seat_id")

            # Check if user already reserved THIS flight
            cursor.execute(
                "SELECT id FROM tickets WHERE user_id = %s AND flight_id = %s",
                (user_id, flight_id)
            )
            if cursor.fetchone():
                flash("You already reserved this flight.", "warning")
                return redirect(url_for("my_flight_reservations"))

            # Lock the seat
            if chosen_seat_id:
                cursor.execute(
                    "SELECT id FROM seats WHERE id = %s AND flight_id = %s AND occupied = 0 FOR UPDATE",
                    (chosen_seat_id, flight_id)
                )
            else:
                cursor.execute(
                    "SELECT id FROM seats WHERE flight_id = %s AND occupied = 0 ORDER BY id LIMIT 1 FOR UPDATE",
                    (flight_id,)
                )

            seat_row = cursor.fetchone()
            if not seat_row:
                conn.rollback()
                flash("No available seats for this flight (or selected seat was taken).", "danger")
                return redirect(url_for("flights"))

            seat_id = seat_row["id"]
            # Insert the new ticket for THIS flight only
            cursor.execute(
                "INSERT INTO tickets (user_id, flight_id, seat_id) VALUES (%s, %s, %s)",
                (user_id, flight_id, seat_id)
            )

            # Update seat & flight occupancy
            cursor.execute("UPDATE seats SET occupied = 1 WHERE id = %s", (seat_id,))
            cursor.execute("UPDATE flights SET occupied_number = occupied_number + 1 WHERE id = %s", (flight_id,))

            conn.commit()
            flash("Flight reserved successfully!", "success")
            return redirect(url_for("my_flight_reservations"))

    except Exception as e:
        conn.rollback()
        flash(f"Error during reservation: {e}", "danger")

    finally:
        cursor.close()
        conn.close()

    return render_template("reserve_flight.html", flight=flight, available_seats=available_seats)


@app.route("/my_flight_reservations")
def my_flight_reservations():
    if "user_id" not in session:
        flash("You must login to view your flight reservations", "warning")
        return redirect(url_for("login"))
    user_id = session["user_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                t.id AS reservation_id,
                f.id AS flight_id,
                f.flight_number,
                f.plane_model,
                f.departure_time,
                f.arrival_time,
                f.flight_time,
                f.origin,
                f.destination,
                f.gate,
                f.price,
                f.return_ticket,
                s.seat_number
            FROM tickets t
            JOIN flights f ON t.flight_id = f.id
            LEFT JOIN seats s ON t.seat_id = s.id
            WHERE t.user_id = %s
            ORDER BY f.departure_time DESC
        """, (user_id,))
        reservations = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template("my_flight_reservations.html", reservations = reservations)
    except Exception as e:
        logging.error("Error fetching flight reservations: %s", e)
        flash("Something went wrong please try again later", "danger")
        return redirect(url_for("flights"))

@app.route("/delete_flight_reservation/<int:reservation_id>", methods=["POST"])
def delete_flight_reservation(reservation_id):
    if "user_id" not in session:
        flash("You must log in to delete reservations.", "warning")
        return redirect(url_for("login"))
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        cursor.execute("SELECT id, flight_id, seat_id, user_id FROM tickets WHERE id = %s FOR UPDATE", (reservation_id,))
        ticket = cursor.fetchone()
        if not ticket:
            conn.rollback()
            flash("Reservation not found.", "danger")
            return redirect(url_for("my_flight_reservations"))
        if ticket["user_id"] != user_id:
            conn.rollback()
            flash("You are not authorized to cancel this reservation.", "danger")
            return redirect(url_for("my_flight_reservations"))
        flight_id = ticket["flight_id"]
        seat_id = ticket["seat_id"] 
        cursor.execute("DELETE FROM tickets WHERE id = %s", (reservation_id,))
        if seat_id:
            cursor.execute("UPDATE seats SET occupied = 0 WHERE id = %s", (seat_id,))
        cursor.execute("UPDATE flights SET occupied_number = GREATEST(occupied_number - 1, 0) WHERE id = %s", (flight_id,))
        conn.commit()
        flash("Reservation successfully canceled.", "success")
        return redirect(url_for("my_flight_reservations"))
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        logging.error("Error cancelling flight reservation: %s", e)
        flash("An error occurred while cancelling the reservation. Please try again later.", "danger")
        return redirect(url_for("my_flight_reservations"))
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    app.run(debug=True)