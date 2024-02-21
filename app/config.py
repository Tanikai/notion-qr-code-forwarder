from pydantic_settings import BaseSettings
from pydantic import BaseModel
from typing import List
import json


class DatabaseConfig(BaseModel):
    name: str
    database_id: str
    forward_column_name: str = "ID"


class Configuration(BaseModel):
    """
    Application config
    """
    auth: str = ""
    lazy_load: bool = False  # true: load databases on first request, false: load databases on startup
    databases: List[DatabaseConfig]


class EnvFile(BaseSettings):
    NFWD_CONFIG_PATH: str = "./config.json"


env_file = EnvFile()


def _load_config():
    with open(env_file.NFWD_CONFIG_PATH) as f:
        json_file = json.load(f)
        return Configuration(**json_file)


configuration = _load_config()


def get_configuration():
    return configuration
