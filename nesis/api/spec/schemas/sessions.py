from marshmallow import Schema, fields
import nesis.api.spec as spec


class SessionReqSchema(Schema):
    email = fields.Email()
    password = fields.Str()


class SessionResSchema(Schema):
    token = fields.Str()
    user = fields.Dict()
