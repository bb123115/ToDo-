import sqlite3

from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from database import get_connection, init_db

app = Flask(__name__)
app.secret_key = "todo-secret-key"


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not email or not password:
            flash("必須項目を入力してください")
            return render_template("register.html")

        password_hash = generate_password_hash(password)

        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO users (username, email, password)
                VALUES (?, ?, ?)
                """,
                (username, email, password_hash)
            )

            connection.commit()
            connection.close()

            flash("登録完了しました")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("このメールアドレスはすでに登録されています")
            return render_template("register.html")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)