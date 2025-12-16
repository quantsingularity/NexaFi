from database.manager import BaseModel


class User(BaseModel):
    table_name = "users"


class OAuthClient(BaseModel):
    table_name = "oauth_clients"


class AuthorizationCode(BaseModel):
    table_name = "oauth_authorization_codes"


class AccessToken(BaseModel):
    table_name = "oauth_access_tokens"


class RegisteredDevice(BaseModel):
    table_name = "registered_devices"
