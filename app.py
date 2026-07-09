from flask import Flask, render_template, request, session, redirect, url_for
app = Flask(__name__)
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

        if username == "Diwan" and password == "12345":
            session["username"] = username
            return render_template(
                "login.html",
                message=f"Welcome {username}"
            )

        return render_template(
            "login.html",
            message="Invalid Username or Password"
        )

    return render_template("login.html")
app.run(debug=True)