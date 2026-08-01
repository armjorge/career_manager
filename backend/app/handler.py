"""AWS Lambda entrypoint — wraps the FastAPI ASGI app with Mangum."""

from mangum import Mangum

from app.main import app

handler = Mangum(app, lifespan="off")
