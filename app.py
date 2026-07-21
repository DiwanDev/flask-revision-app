from flask import Flask, render_template, request, session, redirect, url_for
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "mysecretkey"

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("MYSQL_PASSWORD"),
    database="flask_db"
)

if db.is_connected():
    print("Connected to MySQL successfully!")


@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("products"))

    return render_template("login.html")


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


@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("products"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return render_template(
                "login.html",
                message="Username is required"
            )

        if not password:
            return render_template(
                "login.html",
                message="Password is required"
            )

        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username = %s AND password = %s
            """,
            (username, password)
        )

        user = cursor.fetchone()
        cursor.close()

        if user:
            session["username"] = user["username"]

            if "cart" not in session:
                session["cart"] = []

            return redirect(url_for("products"))

        return render_template(
            "login.html",
            message="Invalid Username or Password"
        )

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "username" in session:
        return redirect(url_for("products"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return render_template(
                "signup.html",
                message="Username is required"
            )

        if not password:
            return render_template(
                "signup.html",
                message="Password is required"
            )

        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username = %s
            """,
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
            """
            INSERT INTO users (username, password)
            VALUES (%s, %s)
            """,
            (username, password)
        )

        db.commit()
        cursor.close()

        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/products")
def products():
    if "username" not in session:
        return redirect(url_for("login"))

    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products")

    product_list = cursor.fetchall()

    cursor.close()

    return render_template(
        "products.html",
        products=product_list,
        username=session["username"]
    )


@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    if "username" not in session:
        return redirect(url_for("login"))

    product_id = request.form.get("product_id")

    if not product_id:
        return redirect(url_for("products"))

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id, stock
        FROM products
        WHERE id = %s
        """,
        (product_id,)
    )

    product = cursor.fetchone()
    cursor.close()

    if not product:
        return redirect(url_for("products"))

    if product["stock"] <= 0:
        return redirect(url_for("products"))

    cart = session.get("cart", [])

    cart.append(product_id)

    session["cart"] = cart

    return redirect(url_for("products"))


@app.route("/cart")
def cart():
    if "username" not in session:
        return redirect(url_for("login"))

    cart_ids = session.get("cart", [])
    cart_products = []
    total_price = 0

    cursor = db.cursor(dictionary=True)

    for product_id in cart_ids:
        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE id = %s
            """,
            (product_id,)
        )

        product = cursor.fetchone()

        if product:
            cart_products.append(product)
            total_price += float(product["price"])

    cursor.close()

    return render_template(
        "cart.html",
        cart_products=cart_products,
        total_price=total_price
    )


@app.route("/checkout")
def checkout():
    if "username" not in session:
        return redirect(url_for("login"))

    cart_ids = session.get("cart", [])

    if not cart_ids:
        return redirect(url_for("cart"))

    cart_products = []
    total_price = 0

    cursor = db.cursor(dictionary=True)

    for product_id in cart_ids:
        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE id = %s
            """,
            (product_id,)
        )

        product = cursor.fetchone()

        if product:
            cart_products.append(product)
            total_price += float(product["price"])

    cursor.close()

    if not cart_products:
        session["cart"] = []
        return redirect(url_for("cart"))

    return render_template(
        "checkout.html",
        cart_products=cart_products,
        total_price=total_price
    )


@app.route("/place-order", methods=["POST"])
def place_order():
    if "username" not in session:
        return redirect(url_for("login"))

    cart_ids = session.get("cart", [])

    if not cart_ids:
        return redirect(url_for("cart"))

    full_name = request.form.get("full_name")
    phone = request.form.get("phone")
    pincode = request.form.get("pincode")
    house = request.form.get("house")
    area = request.form.get("area")
    landmark = request.form.get("landmark")
    city = request.form.get("city")
    state = request.form.get("state")
    country = request.form.get("country")
    instructions = request.form.get("instructions")
    payment_method = request.form.get("payment_method")

    if not full_name:
        return redirect(url_for("checkout"))

    if not phone:
        return redirect(url_for("checkout"))

    if not pincode:
        return redirect(url_for("checkout"))

    if not house:
        return redirect(url_for("checkout"))

    if not area:
        return redirect(url_for("checkout"))

    if not city:
        return redirect(url_for("checkout"))

    if not state:
        return redirect(url_for("checkout"))

    if not country:
        return redirect(url_for("checkout"))

    if not payment_method:
        return redirect(url_for("checkout"))

    cursor = db.cursor(dictionary=True)

    try:
        for product_id in cart_ids:
            cursor.execute(
                """
                SELECT id, name, stock
                FROM products
                WHERE id = %s
                FOR UPDATE
                """,
                (product_id,)
            )

            product = cursor.fetchone()

            if not product or product["stock"] <= 0:
                db.rollback()
                cursor.close()

                return render_template(
                    "order_failed.html",
                    message="One of your products is currently out of stock."
                )

            cursor.execute(
                """
                UPDATE products
                SET stock = stock - 1
                WHERE id = %s
                """,
                (product_id,)
            )

        db.commit()

    except mysql.connector.Error as error:
        db.rollback()
        cursor.close()

        print("Order error:", error)

        return render_template(
            "order_failed.html",
            message="Something went wrong while placing your order."
        )

    cursor.close()

    session["cart"] = []

    return render_template(
        "order_success.html",
        full_name=full_name,
        phone=phone,
        pincode=pincode,
        house=house,
        area=area,
        landmark=landmark,
        city=city,
        state=state,
        country=country,
        instructions=instructions,
        payment_method=payment_method
    )


@app.route("/logout")
def logout():
    session.clear()

    return redirect(url_for("login"))


@app.route("/test-db")
def test_db():
    cursor = db.cursor()

    cursor.execute("SELECT * FROM students")

    students = cursor.fetchall()

    cursor.close()

    return str(students)


if __name__ == "__main__":
    app.run(debug=True)