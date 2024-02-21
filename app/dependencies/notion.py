from notion_client import AsyncClient
from notion_client.helpers import async_iterate_paginated_api
from typing import List, Dict
import asyncio

from ..config import DatabaseConfig, configuration
from ..model.mappings import ForwardedDatabase, ForwardUrls
import logging

config = configuration
logger = logging.getLogger("uvicorn")


class DatabaseNotFoundException(Exception):
    pass


class ItemNotFoundException(Exception):
    pass


def plain_from_rich_object(rich_text: dict):
    return "".join(
        map(lambda rich_object: rich_object["text"]["content"], rich_text)
    )


def create_database(db: DatabaseConfig):
    return ForwardedDatabase(
        name=db.name,
        database_id=db.database_id,
        forward_column_name=db.forward_column_name,
        forwarding_dict={},
    )


async def refresh_database(f_db: ForwardedDatabase, notion_client: AsyncClient) -> None:
    """
    Used to refresh the entries of an already existing Forwarded Database.
    """
    f_db.forwarding_dict = {}
    async for item in async_iterate_paginated_api(
            notion_client.databases.query, database_id=f_db.database_id
    ):
        append_forwarding_url(f_db, item)


def append_forwarding_url(f_db: ForwardedDatabase, notion_item: dict) -> None:
    properties = notion_item["properties"]

    forward_id = properties[f_db.forward_column_name]
    forward_id_plain = plain_from_rich_object(forward_id["rich_text"])

    if forward_id_plain in f_db.forwarding_dict:
        f_db.forwarding_dict[forward_id_plain].urls.append(notion_item["url"])
    else:
        f_db.forwarding_dict[forward_id_plain] = ForwardUrls(urls=[notion_item["url"]])


async def populate_database(
        db: DatabaseConfig, notion_client: AsyncClient
) -> ForwardedDatabase:
    """
    Used to initialize a Forwarded Database from a configuration.
    """
    f_db = create_database(db)
    await refresh_database(f_db, notion_client)
    return f_db


async def populate_forwarded_databases(
        databases: List[DatabaseConfig], notion_client: AsyncClient
) -> List[ForwardedDatabase]:
    tasks = []
    for db in databases:
        task = populate_database(db, notion_client)
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return list(results)


def create_forwarded_databases(
        databases: List[DatabaseConfig]
) -> List[ForwardedDatabase]:
    return [create_database(db) for db in databases]


class NotionForwarder:
    def __init__(self, client: AsyncClient):
        self._client = client
        self._database_config = config.databases
        self._forwardings: Dict[str, ForwardedDatabase] = {}

    async def create_databases(self, populate=False):
        logger.info("Creating forwarded databases...")

        if populate:
            forwarding_list = await populate_forwarded_databases(
                self._database_config, notion_client=self._client
            )
        else:
            forwarding_list = create_forwarded_databases(self._database_config)

        self._forwardings = {f.name: f for f in forwarding_list}
        logger.info(f"Configured forwardings for databases: {list(self._forwardings.keys())}")

    def get_forwarding_cached(self, database_name: str, item_id: str) -> List[str]:
        logger.info(f"Get cached forwarding for {database_name}/{item_id}...")
        if database_name not in self._forwardings:
            logger.info(f"Database not found")
            raise DatabaseNotFoundException(f"Database {database_name} not found")

        database: ForwardedDatabase = self._forwardings[database_name]
        if item_id not in database.forwarding_dict:
            logger.info(f"Item not found")
            raise ItemNotFoundException(f"Item ID {item_id} not found in database {database_name}")

        logger.info(f"Found {len(database.forwarding_dict[item_id].urls)} URLs in cache")
        return database.forwarding_dict[item_id].urls

    async def get_forwarding_refreshed(self, database_name: str, item_id: str) -> List[str]:
        try:
            return self.get_forwarding_cached(database_name, item_id)
        except ItemNotFoundException:
            return await self.get_forwarding_from_db(database_name, item_id)

    async def get_forwarding_from_db(self, database_name: str, item_id: str) -> List[str]:
        if database_name not in self._forwardings:
            raise Exception(f"Database {database_name} not found")
        database: ForwardedDatabase = self._forwardings[database_name]

        logger.info(f"Query forwarding for {database_name}/{item_id} from Notion API...")
        async for item in async_iterate_paginated_api(
                self._client.databases.query, **{
                    "database_id": database.database_id,
                    "filter": {
                        "property": database.forward_column_name,
                        "rich_text": {
                            "equals": item_id
                        }
                    }
                }
        ):
            append_forwarding_url(database, item)

        if item_id not in database.forwarding_dict:
            logger.info("Not found")
            raise ItemNotFoundException(f"Item ID {item_id} not found in database {database_name} (after refresh)")

        logger.info(f"Found")

        return database.forwarding_dict[item_id].urls


_notion_client = AsyncClient(auth=config.auth)
_forwarder = NotionForwarder(client=_notion_client)


def get_notion_forwarder():
    return _forwarder
