from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from peewee import IntegrityError, fn
from config import User, Message, Like, db


app = Flask(__name__)
app.secret_key = "secret"  # 秘密鍵
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)


@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # データの検証
        if not request.form["name"] or not request.form["password"] or not request.form["email"]:
            flash("未入力の項目があります。")
            return redirect(request.url)
        if User.select().where(User.name == request.form["name"]):
            flash("その名前はすでに使われています。")
            return redirect(request.url)
        if User.select().where(User.email == request.form["email"]):
            flash("そのメールアドレスはすでに使われています。")
            return redirect(request.url)

        try:
            User.create(
                name=request.form["name"],
                email=request.form["email"],
                password=generate_password_hash(request.form["password"]),
            )
            return redirect(url_for("login"))
        except IntegrityError as e:
            flash(f"{e}")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # データの検証
        if not request.form["password"] or not request.form["email"]:
            flash("未入力の項目があります。")
            return redirect(request.url)

        # ここでユーザーを認証し、OKならログインする
        user = User.select().where(User.email == request.form["email"]).first()
        if user is not None and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            flash(f"ようこそ！ {user.name}さん")
            return redirect(url_for("index"))

        # NGならフラッシュメッセージ��設定
        flash("認証に失敗しました")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("ログアウトしました！")
    return redirect(url_for("index"))


@app.route("/unregister")
@login_required
def unregister():
    current_user.delete_instance()
    logout_user()
    return redirect(url_for("index"))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST" and current_user.is_authenticated:
        Message.create(user=current_user, content=request.form["content"])

    sort = request.args.get("sort", "new")  # デフォルトは新着順
    if sort == "likes":
        messages = (
            Message.select()
            .where(Message.reply_to.is_null(True))
            .order_by(Message.likes_count.desc(), Message.pub_date.desc())
        )
    else:
        messages = (
            Message.select()
            .where(Message.reply_to.is_null(True))
            .order_by(Message.pub_date.desc(), Message.id.desc())
        )

    top_users = User.select().order_by(User.likes_count.desc()).limit(5)

    return render_template("index.html", messages=messages, top_users=top_users, current_sort=sort, Like=Like)


@app.route("/messages/<message_id>/delete", methods=["POST"])
@login_required
def delete(message_id):
    if Message.select().where((Message.id == message_id) & (Message.user == current_user)).first():
        Message.delete_by_id(message_id)
    else:
        flash("無効な操作です")
    return redirect(request.referrer)


@app.route("/messages/<message_id>/")
def show(message_id):
    messages = (
        Message.select()
        .where((Message.id == message_id) | (Message.reply_to == message_id))
        .order_by(Message.pub_date.desc())
    )
    if messages.count() == 0:
        return redirect(url_for("index"))
    return render_template("show.html", messages=messages, message_id=message_id, Like=Like)


@app.route("/messages/<message_id>/", methods=["POST"])
@login_required
def reply(message_id):
    Message.create(user=current_user, content=request.form["content"], reply_to=message_id)
    return redirect(url_for("show", message_id=message_id))


@app.route("/messages/<message_id>/like", methods=["POST"])
@login_required
def like_message(message_id):
    message = Message.get_by_id(message_id)
    try:
        with db.atomic():
            Like.create(user=current_user, message=message)
            message.likes_count += 1
            message.save()
            message.user.likes_count += 1
            message.user.save()
        flash("いいねしました！")
    except IntegrityError:
        flash("すでにいいねしています")
    return redirect(request.referrer or url_for("index"))


@app.route("/messages/<message_id>/unlike", methods=["POST"])
@login_required
def unlike_message(message_id):
    message = Message.get_by_id(message_id)
    like = Like.get_or_none(user=current_user, message=message)
    if like:
        with db.atomic():
            like.delete_instance()
            message.likes_count -= 1
            message.save()
            message.user.likes_count -= 1
            message.user.save()
        flash("いいねを取り消しました")
    return redirect(request.referrer or url_for("index"))


if __name__ == "__main__":
    app.run(port=8000, debug=True)
