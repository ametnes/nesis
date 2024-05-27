from marshmallow import Schema, fields
from nesis.api.core.util.constants import DEFAULT_DATETIME_FORMAT


class AppParameter(Schema):
    app_id = fields.Str()


class AppReqSchema(Schema):
    name = fields.Str()
    description = fields.Str()


class AppResSchema(AppReqSchema):
    id = fields.Str()
    enabled = fields.Boolean()
    create_date = fields.DateTime(DEFAULT_DATETIME_FORMAT)


class AppPostResSchema(AppResSchema):
    secret = fields.Str()


class AppsSchema(Schema):
    items = fields.List(fields.Nested(AppResSchema))
    count = fields.Int()
