import argparse
import sys
from pathlib import Path


working_dir = [
    str(Path(__file__).parent.absolute()),
    str(Path(__file__).parent.parent.absolute()),
    str(Path(__file__).parent.parent.parent.absolute()),
    str(Path(__file__).parent.parent.parent.parent.absolute()),
]
sys.path += working_dir

from nesis.api.core.controllers import app
from nesis.api.core.controllers.apps_controller import operate_apps
from nesis.api.core.controllers.management import (
    operate_roles,
    operate_role,
    operate_users,
    operate_user,
    operate_sessions,
)

from nesis.api.core.controllers.datasources import (
    operate_datasources,
    operate_datasource,
)
from nesis.api.core.controllers.predictions import operate_module_predictions
from nesis.api.core.controllers.tasks_controller import operate_tasks, operate_task
from nesis.api.spec import spec

with app.test_request_context():
    spec.path(view=operate_sessions)
    spec.path(view=operate_users)
    spec.path(view=operate_user)
    spec.path(view=operate_apps)
    spec.path(view=operate_tasks)
    spec.path(view=operate_task)
    spec.path(view=operate_roles)
    spec.path(view=operate_role)
    spec.path(view=operate_datasources)
    spec.path(view=operate_datasource)
    spec.path(view=operate_module_predictions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Nesis API Spec")
    parser.add_argument(
        "--destination", type=str, help="Destination file", required=True
    )

    args = parser.parse_args()

    Path(args.destination).write_text(spec.to_yaml())
