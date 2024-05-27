from marshmallow import Schema, fields
from nesis.api.core.util.constants import DEFAULT_DATETIME_FORMAT


class DatasourceReqSchema(Schema):
    name = fields.Str()
    enabled = fields.Boolean()
    schedule = fields.Str()
    endpoint = fields.Str()


class DatasourceResSchema(DatasourceReqSchema):
    id = fields.Str()
    status = fields.Str()
    create_date = fields.DateTime(DEFAULT_DATETIME_FORMAT)


class DatasourcesSchema(Schema):
    items = fields.List(fields.Nested(DatasourceResSchema))
    count = fields.Int()
