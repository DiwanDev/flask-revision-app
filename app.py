from flask import Flask, render_template, request, session, redirect, url_for
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("MYSQL_PASSWORD"),
    database="flask_db"
)

if db.is_connected():
    print("Connected to MySQL successfully!")

app.secret_key = "mysecretkey"

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/dashboard")
def dashboard():

    username = session.get("username")

    if username is None:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        username=username
    )
@app.route("/logout")
def logout():

    session.pop("username", None)

    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "":
            return render_template(
                "login.html",
                message="Username is required"
            )

        if password == "":
            return render_template(
                "login.html",
                message="Password is required"
            )

        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE username = %s AND password = %s",
            (username, password)
        )

        user = cursor.fetchone()

        cursor.close()

        if user:
            session["username"] = user["username"]

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            message="Invalid Username or Password"
        )

    return render_template("login.html")
@app.route("/test-db")
def test_db():
    cursor = db.cursor()

    cursor.execute("SELECT * FROM students")

    students = cursor.fetchall()

    cursor.close()

    return str(students)
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "":
            return render_template(
                "signup.html",
                message="Username is required"
            )

        if password == "":
            return render_template(
                "signup.html",
                message="Password is required"
            )

        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE username = %s",
            (username,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()

            return render_template(
                "signup.html",
                message="Username already exists"
            )

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password)
        )

        db.commit()
        cursor.close()

        session["username"] = username

        return redirect(url_for("dashboard"))

    return render_template("signup.html")
@app.route("/products")
def products():
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products ORDER BY created_at DESC")

    product_list = cursor.fetchall()

    cursor.close()

    return render_template(
        "products.html",
        products=product_list
    )


app.run(debug=True)
