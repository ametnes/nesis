from flask import Flask

app = Flask(__name__)


def error_message(message, message_type="ERROR"):
    return {"type": message_type, "message": message}
