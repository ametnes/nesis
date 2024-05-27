from marshmallow import Schema, fields
from nesis.api.core.util.constants import DEFAULT_DATETIME_FORMAT


class PredictionReqSchema(Schema):
    query = fields.Str()
    save = fields.Boolean()


class PredictionResSchema(PredictionReqSchema):
    id = fields.Str()
    data = fields.Dict()


class PredictionsSchema(Schema):
    items = fields.List(fields.Nested(PredictionResSchema))
    count = fields.Int()
