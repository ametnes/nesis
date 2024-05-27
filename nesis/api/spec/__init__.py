from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from .schemas.apps import *
from .schemas.datasources import (
    DatasourceReqSchema,
    DatasourceResSchema,
    DatasourcesSchema,
)
from .schemas.predictions import (
    PredictionReqSchema,
    PredictionResSchema,
    PredictionsSchema,
)
from .schemas.sessions import SessionReqSchema, SessionResSchema
from .schemas.tasks import *
from .schemas.roles import *
from .schemas.users import *


spec = APISpec(
    title="Nesis API",
    version="0.1.1",
    openapi_version="3.0.2",
    info=dict(
        description="Nesis API helps you extend your existing and legacy applications easily giving them AI capabilities."
        "First create a role for you App, then create an App assigning the role to it. The API key returned can then be used"
        "as the `Authorization` token.",
        version="0.1.1",
    ),
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)


class MessageSchema(Schema):
    type = fields.Str()
    message = fields.Str()


# Apps
spec.components.schema("AppReq", schema=AppReqSchema)
spec.components.schema("AppRes", schema=AppResSchema)
spec.components.schema("Apps", schema=AppsSchema)

# Tasks
spec.components.schema("TaskReq", schema=TaskReqSchema)
spec.components.schema("TaskRes", schema=TaskResSchema)
spec.components.schema("Tasks", schema=TasksSchema)

# Roles
spec.components.schema("RoleReq", schema=RoleReqSchema)
spec.components.schema("RoleRes", schema=RoleResSchema)
spec.components.schema("Roles", schema=RolesSchema)

# Users
spec.components.schema("UserReq", schema=UserReqSchema)
spec.components.schema("UserRes", schema=UserResSchema)
spec.components.schema("Users", schema=UsersSchema)

# Datasources
spec.components.schema("DatasourceReq", schema=DatasourceReqSchema)
spec.components.schema("DatasourceRes", schema=DatasourceResSchema)
spec.components.schema("Datasources", schema=DatasourcesSchema)

# Predictions
spec.components.schema("PredictionReq", schema=PredictionReqSchema)
spec.components.schema("PredictionRes", schema=PredictionResSchema)
spec.components.schema("Predictions", schema=PredictionsSchema)

# Sessions
spec.components.schema("SessionReq", schema=SessionReqSchema)
spec.components.schema("SessionRes", schema=SessionResSchema)

# Error
spec.components.schema("Message", schema=MessageSchema)
