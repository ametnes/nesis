from flask import Flask
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)


def error_message(message, message_type="ERROR"):
    return {"type": message_type, "message": message}
