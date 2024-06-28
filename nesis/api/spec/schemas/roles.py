from marshmallow import Schema, fields
from nesis.api.core.util.constants import DEFAULT_DATETIME_FORMAT


class RoleParameter(Schema):
    role_id = fields.Str()


class PolicyActionSchema(Schema):
    action: fields.Str()
    resource: fields.Str()


class RoleReqSchema(Schema):
    name: fields.Str()
    items = fields.List(fields.Nested(PolicyActionSchema))


class RoleResSchema(RoleReqSchema):
    id = fields.Str()
    create_date = fields.DateTime(DEFAULT_DATETIME_FORMAT)


class RolesSchema(Schema):
    items = fields.List(fields.Nested(RoleResSchema))
    count = fields.Int()
