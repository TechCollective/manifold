from pydantic import BaseModel

class ServerInfo(BaseModel):
    id: int
    name: str
    host: str
    port: int
    has_credentials: bool = False
