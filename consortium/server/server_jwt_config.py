import datetime
import secrets

# JSON Web Token generation related config variables
JSON_WEB_TOKEN_SECRET_KEY = secrets.token_hex(32)
JSON_WEB_TOKEN_ALGORITHMS = ["HS256"]
JSON_WEB_TOKEN_EXPIRATION_DURATION = datetime.timedelta(hours=24)
