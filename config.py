import datetime
from flask_login import UserMixin
from peewee import SqliteDatabase, Model, IntegerField, CharField, TextField, TimestampField, ForeignKeyField

db = SqliteDatabase("db.sqlite")


class User(UserMixin, Model):
    id = IntegerField(primary_key=True)
    name = CharField(unique=True)
    email = CharField(unique=True)
    password = TextField()
    likes_count = IntegerField(default=0)

    class Meta:
        database = db
        table_name = "users"


class Message(Model):
    id = IntegerField(primary_key=True)
    user = ForeignKeyField(User, backref="messages", on_delete="CASCADE")
    content = TextField()
    pub_date = TimestampField(default=datetime.datetime.now)
    reply_to = ForeignKeyField("self", backref="messages", on_delete="CASCADE", null=True)
    likes_count = IntegerField(default=0)

    class Meta:
        database = db
        table_name = "masseages"


class Like(Model):
    user = ForeignKeyField(User, backref='likes', on_delete="CASCADE")
    message = ForeignKeyField(Message, backref='liked_by', on_delete="CASCADE")
    created_at = TimestampField(default=datetime.datetime.now)

    class Meta:
        database = db
        table_name = "likes"
        indexes = (
            (('user', 'message'), True),
        )


db.create_tables([User, Message, Like])
db.pragma('foreign_keys', 1, permanent=True)
