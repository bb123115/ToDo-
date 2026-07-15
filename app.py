import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

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
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("必須項目を入力してください")
            return render_template("register.html")

        password_hash = generate_password_hash(password)
        connection = None

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

        except sqlite3.IntegrityError:
            if connection is not None:
                connection.rollback()

            flash("このメールアドレスはすでに登録されています")
            return render_template("register.html")

        finally:
            if connection is not None:
                connection.close()

        flash("登録が完了しました")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("メールアドレスとパスワードを入力してください")
            return render_template("login.html")

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, username, email, password
            FROM users
            WHERE email = ?
            """,
            (email,)
        )

        user = cursor.fetchone()
        connection.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["username"] = user[1]

            flash("ログインしました")
            return redirect(url_for("todo_list"))

        flash("メールアドレスまたはパスワードが正しくありません")

    return render_template("login.html")

@app.route("/todos")
def todo_list():
    if "user_id" not in session:
        flash("ログインしてください")
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, title, content, due_date, status, created_at
        FROM todos
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (session["user_id"],)
    )

    todos = cursor.fetchall()
    connection.close()

    return render_template(
        "todos.html",
        username=session["username"],
        todos=todos
    )

@app.route("/todos/add", methods=["POST"])
def add_todo():
    if "user_id" not in session:
        flash("ログインしてください")
        return redirect(url_for("login"))

    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    due_date = request.form.get("due_date", "").strip()

    if not title:
        flash("タイトルを入力してください")
        return redirect(url_for("todo_list"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO todos (user_id, title, content, due_date)
        VALUES (?, ?, ?, ?)
        """,
        (
            session["user_id"],
            title,
            content,
            due_date if due_date else None
        )
    )

    connection.commit()
    connection.close()

    flash("ToDoを追加しました")
    return redirect(url_for("todo_list"))

@app.route("/todos/<int:todo_id>/toggle", methods=["POST"])
def toggle_todo(todo_id):
    if "user_id" not in session:
        flash("ログインしてください")
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE todos
        SET status =
            CASE
                WHEN status = '未完了' THEN '完了'
                ELSE '未完了'
            END
        WHERE id = ? AND user_id = ?
        """,
        (todo_id, session["user_id"])
    )

    connection.commit()
    connection.close()

    return redirect(url_for("todo_list"))


@app.route("/todos/<int:todo_id>/delete", methods=["POST"])
def delete_todo(todo_id):
    if "user_id" not in session:
        flash("ログインしてください")
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM todos
        WHERE id = ? AND user_id = ?
        """,
        (todo_id, session["user_id"])
    )

    connection.commit()
    connection.close()

    return redirect(url_for("todo_list"))

@app.route("/todos/<int:todo_id>/edit", methods=["GET", "POST"])
def edit_todo(todo_id):
    if "user_id" not in session:
        flash("ログインしてください")
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, title, content, due_date, status
        FROM todos
        WHERE id = ? AND user_id = ?
        """,
        (todo_id, session["user_id"])
    )

    todo = cursor.fetchone()

    if todo is None:
        connection.close()
        flash("指定されたToDoが見つかりません")
        return redirect(url_for("todo_list"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        due_date = request.form.get("due_date", "").strip()

        if not title:
            connection.close()
            flash("タイトルを入力してください")
            return render_template("edit_todo.html", todo=todo)

        cursor.execute(
            """
            UPDATE todos
            SET title = ?, content = ?, due_date = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                title,
                content,
                due_date if due_date else None,
                todo_id,
                session["user_id"]
            )
        )

        connection.commit()
        connection.close()

        flash("ToDoを編集しました")
        return redirect(url_for("todo_list"))

    connection.close()
    return render_template("edit_todo.html", todo=todo)

@app.route("/logout")
def logout():
    session.clear()
    flash("ログアウトしました")
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)