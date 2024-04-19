GET: str = "GET"
POST: str = "POST"
DELETE: str = "DELETE"
PUT: str = "PUT"

from .api import app

from . import datasources, predictions, settings, management, tasks_controller
