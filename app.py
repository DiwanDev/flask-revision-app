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


# =========================================
# HOME
# =========================================

@app.route("/")
def home():

    if "username" in session:
        return redirect(url_for("products"))

    return render_template("login.html")


# =========================================
# ABOUT
# =========================================

@app.route("/about")
def about():

    return render_template("about.html")


# =========================================
# CONTACT
# =========================================

@app.route("/contact")
def contact():

    return render_template("contact.html")


# =========================================
# DASHBOARD
# =========================================

@app.route("/dashboard")
def dashboard():

    username = session.get("username")

    if username is None:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        username=username
    )


# =========================================
# LOGIN
# =========================================

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
            WHERE username = %s
            AND password = %s
            """,
            (username, password)
        )

        user = cursor.fetchone()

        cursor.close()

        if user:

            session["username"] = user["username"]

            # The cart is stored as a dictionary:
            # product_id -> quantity
            #
            # Example:
            # {
            #     "7": 2,
            #     "8": 1
            # }

            if "cart" not in session:
                session["cart"] = {}

            # Convert an old list-format cart into a dictionary.
            if not isinstance(session["cart"], dict):
                session["cart"] = {}

            return redirect(url_for("products"))

        return render_template(
            "login.html",
            message="Invalid Username or Password"
        )

    return render_template("login.html")


# =========================================
# SIGNUP
# =========================================

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


# =========================================
# PRODUCTS AND SEARCH
# =========================================

@app.route("/products")
def products():

    if "username" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    cursor = db.cursor(dictionary=True)

    if search and category:

        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE
                (store_type IS NULL OR store_type != 'eyewear')
            AND
                (
                    name LIKE %s
                    OR description LIKE %s
                    OR category LIKE %s
                )
            AND category = %s
            ORDER BY id
            LIMIT 10
            """,
            (
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%",
                category
            )
        )

    elif search:

        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE
                (store_type IS NULL OR store_type != 'eyewear')
            AND
                (
                    name LIKE %s
                    OR description LIKE %s
                    OR category LIKE %s
                )
            ORDER BY id
            LIMIT 10
            """,
            (
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%"
            )
        )

    elif category:

        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE
                (store_type IS NULL OR store_type != 'eyewear')
            AND category = %s
            ORDER BY id
            LIMIT 10
            """,
            (category,)
        )

    else:

        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE id IN (
                1, 2, 3, 7, 8,
                9, 11, 12, 13, 14
            )
            ORDER BY FIELD(
                id,
                1, 2, 3, 7, 8,
                9, 11, 12, 13, 14
            )
            """
        )

    products_data = cursor.fetchall()

    cursor.close()

    return render_template(
        "products.html",
        products=products_data,
        search=search,
        category=category
    )


# =========================================
# ADD TO CART
# =========================================

@app.route(
    "/add-to-cart/<int:product_id>",
    methods=["POST"]
)
def add_to_cart(product_id):

    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

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

    if product is None:
        cursor.close()
        return redirect(url_for("products"))

    cursor.execute(
        """
        SELECT quantity
        FROM cart
        WHERE username = %s
        AND product_id = %s
        """,
        (username, product_id)
    )

    cart_item = cursor.fetchone()

    if cart_item:

        if cart_item["quantity"] < product["stock"]:

            cursor.execute(
                """
                UPDATE cart
                SET quantity = quantity + 1
                WHERE username = %s
                AND product_id = %s
                """,
                (username, product_id)
            )

    else:

        if product["stock"] > 0:

            cursor.execute(
                """
                INSERT INTO cart (
                    username,
                    product_id,
                    quantity
                )
                VALUES (%s, %s, 1)
                """,
                (username, product_id)
            )

    db.commit()
    cursor.close()

    return redirect(url_for("cart"))
# =========================================
# VIEW CART
# =========================================
@app.route("/increase-cart/<int:product_id>", methods=["POST"])
def increase_cart(product_id):

    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT cart.quantity, products.stock
        FROM cart
        JOIN products
        ON cart.product_id = products.id
        WHERE cart.username = %s
        AND cart.product_id = %s
        """,
        (username, product_id)
    )

    item = cursor.fetchone()

    if item and item["quantity"] < item["stock"]:

        cursor.execute(
            """
            UPDATE cart
            SET quantity = quantity + 1
            WHERE username = %s
            AND product_id = %s
            """,
            (username, product_id)
        )

        db.commit()

    cursor.close()

    return redirect(url_for("cart"))
@app.route("/cart")
def cart():

    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            products.*,
            cart.quantity
        FROM cart
        JOIN products
            ON cart.product_id = products.id
        WHERE cart.username = %s
        ORDER BY cart.id DESC
        """,
        (username,)
    )

    cart_items = cursor.fetchall()

    total = 0

    for item in cart_items:

        item["subtotal"] = (
            float(item["price"]) * item["quantity"]
        )

        total += item["subtotal"]

    cursor.close()

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total
    )
@app.route("/decrease-cart/<int:product_id>", methods=["POST"])
def decrease_cart(product_id):

    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT quantity
        FROM cart
        WHERE username = %s
        AND product_id = %s
        """,
        (username, product_id)
    )

    item = cursor.fetchone()

    if item:

        if item["quantity"] > 1:

            cursor.execute(
                """
                UPDATE cart
                SET quantity = quantity - 1
                WHERE username = %s
                AND product_id = %s
                """,
                (username, product_id)
            )

        else:

            cursor.execute(
                """
                DELETE FROM cart
                WHERE username = %s
                AND product_id = %s
                """,
                (username, product_id)
            )

        db.commit()

    cursor.close()

    return redirect(url_for("cart"))
# =========================================
# CHECKOUT
# =========================================

@app.route("/checkout")
def checkout():

    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            products.*,
            cart.quantity
        FROM cart
        JOIN products
            ON cart.product_id = products.id
        WHERE cart.username = %s
        ORDER BY cart.id DESC
        """,
        (username,)
    )

    cart_products = cursor.fetchall()

    total_price = 0

    for product in cart_products:

        product["subtotal"] = (
            float(product["price"])
            * product["quantity"]
        )

        total_price += product["subtotal"]

    cursor.close()

    if not cart_products:
        return redirect(url_for("cart"))

    return render_template(
        "checkout.html",
        cart_products=cart_products,
        total_price=total_price
    )
# =========================================
# PLACE ORDER
# =========================================

@app.route("/place-order", methods=["POST"])
def place_order():

    if "username" not in session:
        return redirect(url_for("login"))

    cart_data = session.get("cart", {})

    if not isinstance(cart_data, dict):
        cart_data = {}
        session["cart"] = {}

    if not cart_data:
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

    ordered_products = []

    try:

        for product_id, quantity in cart_data.items():

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    price,
                    stock,
                    image_url
                FROM products
                WHERE id = %s
                FOR UPDATE
                """,
                (product_id,)
            )

            product = cursor.fetchone()

            if product is None:

                db.rollback()
                cursor.close()

                return render_template(
                    "order_failed.html",
                    message="One of your products was not found."
                )

            if product["stock"] < quantity:

                db.rollback()
                cursor.close()

                return render_template(
                    "order_failed.html",
                    message=(
                        product["name"]
                        + " does not have enough stock."
                    )
                )

            cursor.execute(
                """
                UPDATE products
                SET stock = stock - %s
                WHERE id = %s
                """,
                (quantity, product_id)
            )

            product["quantity"] = quantity

            product["subtotal"] = (
                float(product["price"]) * quantity
            )

            ordered_products.append(product)

        db.commit()

    except mysql.connector.Error as error:

        db.rollback()
        cursor.close()

        print("Order error:", error)

        return render_template(
            "order_failed.html",
            message=(
                "Something went wrong while "
                "placing your order."
            )
        )

    cursor.close()

    # Clear the cart after a successful order.
    session["cart"] = {}
    session.modified = True

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
        payment_method=payment_method,
        ordered_products=ordered_products
    )


# =========================================
# ORDERS PAGE
# =========================================

@app.route("/orders")
def orders():

    if "username" not in session:
        return redirect(url_for("login"))

    cursor = db.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT *
            FROM orders
            WHERE username = %s
            ORDER BY id DESC
            """,
            (session["username"],)
        )

        orders_data = cursor.fetchall()

    except mysql.connector.Error as error:

        print("Orders page error:", error)

        orders_data = []

    cursor.close()

    return render_template(
        "orders.html",
        orders=orders_data
    )


# =========================================
# CLEAR CART
# =========================================

@app.route("/clear-cart")
def clear_cart():

    if "username" not in session:
        return redirect(url_for("login"))

    session["cart"] = {}
    session.modified = True

    return redirect(url_for("products"))


# =========================================
# LOGOUT
# =========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================================
# TEST DATABASE
# =========================================

@app.route("/test-db")
def test_db():

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT *
        FROM students
        """
    )

    students = cursor.fetchall()

    cursor.close()

    return str(students)


# =========================================
# RUN FLASK
# =========================================
@app.route(
    "/remove-from-cart/<int:product_id>",
    methods=["POST"]
)
def remove_from_cart(product_id):

    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM cart
        WHERE username = %s
        AND product_id = %s
        """,
        (username, product_id)
    )

    db.commit()
    cursor.close()

    return redirect(url_for("cart"))
if __name__ == "__main__":
    app.run(debug=True)