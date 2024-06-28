from marshmallow import Schema, fields
from nesis.api.core.util.constants import DEFAULT_DATETIME_FORMAT


class TaskParameter(Schema):
    task_id = fields.Str()


class TaskReqSchema(Schema):
    name = fields.Str()
    description = fields.Str()
    enabled = fields.Boolean()
    type = fields.Str()
    schedule = fields.Str()
    parent_id = fields.Str()
    definition = fields.Dict()


class TaskResSchema(TaskReqSchema):
    id = fields.Str()
    status = fields.Str()
    create_date = fields.DateTime(DEFAULT_DATETIME_FORMAT)
    update_date = fields.DateTime(DEFAULT_DATETIME_FORMAT)


class TasksSchema(Schema):
    items = fields.List(fields.Nested(TaskResSchema))
    count = fields.Int()
