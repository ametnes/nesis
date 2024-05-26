from marshmallow import Schema, fields
from nesis.api.core.util.constants import DEFAULT_DATETIME_FORMAT


class UserParameter(Schema):
    user_id = fields.Str()


class UserReqSchema(Schema):
    name = fields.Str()
    email = fields.Str()
    password = fields.Str()


class UserResSchema(UserReqSchema):
    id = fields.Str()
    status = fields.Str()
    create_date = fields.DateTime(DEFAULT_DATETIME_FORMAT)


class UsersSchema(Schema):
    items = fields.List(fields.Nested(UserResSchema))
    count = fields.Int()
