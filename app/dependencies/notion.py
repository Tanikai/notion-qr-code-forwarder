from notion_client import AsyncClient
from notion_client.helpers import async_iterate_paginated_api
from typing import List, Dict
import asyncio

from ..config import DatabaseConfig, configuration
from ..model.mappings import ForwardedDatabase, ForwardUrls
import logging

config = configuration
logger = logging.getLogger("uvicorn")


def plain_from_rich_object(rich_text: dict):
    return "".join(
        map(lambda rich_object: rich_object["text"]["content"], rich_text)
    )


async def populate_database(
        db: DatabaseConfig, notion_client: AsyncClient
) -> ForwardedDatabase:
    f_db = ForwardedDatabase(
        name=db.name,
        database_id=db.database_id,
        forward_column_name=db.forward_column_name,
        forwarding_dict={},
    )

    async for item in async_iterate_paginated_api(
            notion_client.databases.query, database_id=f_db.database_id
    ):
        properties = item["properties"]

        forward_id = properties[f_db.forward_column_name]
        forward_id_plain = plain_from_rich_object(forward_id["rich_text"])

        if forward_id_plain in f_db.forwarding_dict:
            f_db.forwarding_dict[forward_id_plain].urls.append(item["url"])
        else:
            f_db.forwarding_dict[forward_id_plain] = ForwardUrls(urls=[item["url"]])

    return f_db


async def populate_forwarded_databases(
        databases: List[DatabaseConfig], notion_client: AsyncClient
) -> List[ForwardedDatabase]:
    tasks = []
    for db in databases:
        task = populate_database(db, notion_client)
        tasks.append(task)

    return list(asyncio.gather(*tasks))


class NotionForwarder:
    def __init__(self, client: AsyncClient):
        self.client = client
        self.database_config = config.databases
        self.forwardings: Dict[str, ForwardedDatabase] = {}

    async def populate_config(self):
        logger.info("Populating forwarding config...")
        forwarding_list = await populate_forwarded_databases(
            self.database_config, notion_client=self.client
        )
        self.forwardings = {f.name: f for f in forwarding_list}
        logger.info(f"Configured forwardings for databases: {list(self.forwardings.keys())}")

    async def get_url(self, database_id: str, item_id: str):
        urls = self.forwardings[database_id].forwarding_dict[item_id].urls
        return ""


_notion_client = AsyncClient(auth=config.auth)
_forwarder = NotionForwarder(client=_notion_client)


def get_notion_forwarder():
    return _forwarder
