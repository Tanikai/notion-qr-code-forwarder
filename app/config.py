from pydantic_settings import BaseSettings
from pydantic import BaseModel
from typing import List
import json
import logging

class DatabaseConfig(BaseModel):
    name: str
    database_id: str
    forward_column_name: str = "ID"

class Configuration(BaseModel):
    """
    Application config
    """
    auth: str = ""
    lazy_load: bool = False # true: load databases on first request, false: load databases on startup
    databases: List[DatabaseConfig]

class EnvFile(BaseSettings):
    config_path: str = "./config.json"

env_file = EnvFile()

def get_config():
    with open(env_file.config_path) as f:
        json_file = json.load(f)
        return Configuration(**json_file)
    
configuration = get_config()