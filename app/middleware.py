from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from dotenv import load_dotenv
import os
import base64

# env
load_dotenv()
_username = os.getenv('USERNAME')
_password = os.getenv('PASSWORD')

class BasicAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed=None):
        super().__init__(app)
        self.allowed = set(allowed or [])
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            # Allow OPTIONS requests to proceed without authentication
            if request.method == "OPTIONS" or request.url.path in self.allowed:
                return await call_next(request)
            
            authorization: str = request.headers.get("Authorization")
            if not authorization:
                return JSONResponse({"detail": "Authorization required"}, status_code=401)

            scheme, _, credentials = authorization.partition(' ')
            if not scheme or scheme.lower() != 'basic' or not credentials:
                return JSONResponse({"detail": "Invalid authentication credentials"}, status_code=401)

            decoded_credentials = base64.b64decode(credentials).decode("ascii")
            username, _, password = decoded_credentials.partition(':')
            if username != _username or password != _password:
                return JSONResponse({"detail": "Invalid username or password"}, status_code=401)

            response = await call_next(request)
            return response
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)