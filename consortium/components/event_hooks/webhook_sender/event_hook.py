import asyncio
import json

import aiohttp
import jsonschema

from consortium.framework.event_hooks import BaseEventHook, EventType


class EventHook(BaseEventHook):
    label = "consortium.event_hooks.webhook_sender"
    name = "Webhook sender"
    description = (
        "This event hook forwards event content for any set of specific events to any set "
        "of arbitrarily specified webhooks. The particular events it listens for and "
        "webhooks it sends content to are configured through the `config.json` file in "
        "the event hook's project folder. Currently supports Discord, Slack, and "
        "generic HTTP POST webhooks."
    )
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"Sekiun (github.com/not-sekiun)"}
    event_types = {"STOP_SERVER", "START_SERVER"}

    async def on_event_hook_setup(self) -> None:
        try:
            with (self.event_hook_project_folder / "config.json").open(
                "r",
            ) as config_file:
                config = json.load(config_file)
        except FileNotFoundError:
            self.logger.error(
                "Failed to load webhook sender event hook configuration file. "
                "Configuration file `config.json` not found at the event hook's "
                f"project folder `{self.event_hook_project_folder}`.",
            )
            return
        except json.decoder.JSONDecodeError:
            self.logger.error(
                "Failed to load webhook sender event hook configuration "
                "file. The configuration file does not contain valid JSON "
                "content.",
            )
            return

        config_json_schema = {
            "type": "object",
            "properties": {
                "events": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "webhooks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "platform": {
                                "type": "string",
                                "enum": ["discord", "slack", "generic"],
                            },
                            "url": {"type": "string", "format": "uri"},
                        },
                    },
                },
                "max_retries": {
                    "type": "integer",
                    "minimum": 0,
                },
                "retry_delay_seconds": {
                    "type": "integer",
                    "minimum": 0,
                },
            },
        }
        try:
            jsonschema.validate(config, config_json_schema)
        except jsonschema.ValidationError as exc:
            self.logger.error(
                "Failed to load webhook sender event hook configuration "
                "file. The configuration file's format does not match the "
                "expected configuration file JSON schema: {}",
                exc.message,
            )
            return

        for event in config["events"]:
            if event not in EventType:
                self.logger.warning(
                    "The provided string '{}' in the set of event types to send is not "
                    "a valid event type.",
                    event,
                )
                continue
            self.event_types.add(event)

        self.environment.config = config

    async def _post_to_webhook_with_retries(
        self,
        client_session: aiohttp.ClientSession,
        webhook_url: str,
        data: dict,
    ) -> None:
        max_retries = self.environment.config.get("max_retries", 3)
        retry_delay_seconds = self.environment.config.get("retry_delay_seconds", 5)
        for i in range(max_retries):
            try:
                async with client_session.post(
                    webhook_url,
                    json=data,
                ) as response:
                    if response.status == 200 or response.status == 204:
                        return
                    else:
                        self.logger.warning(
                            "Failed to send event content to webhook at '{}'. "
                            "Received unexpected status code {}. "
                            "Retrying... (Attempt {}/{})",
                            webhook_url,
                            response.status,
                            i + 1,
                            max_retries,
                        )
            except aiohttp.ClientError as exc:
                self.logger.warning(
                    "Failed to send event content to webhook at '{}'. "
                    "Error: {}. Retrying... (Attempt {}/{})",
                    webhook_url,
                    str(exc),
                    i + 1,
                    max_retries,
                )
            await asyncio.sleep(retry_delay_seconds)

    async def on_event_hook_triggered(self, event):
        async with aiohttp.ClientSession() as client_session:
            for webhook in self.environment.config["webhooks"]:
                event_dict = event.to_json()
                stringified_event_dict = {
                    "event_type": str(event_dict["event_type"]),
                    "content": event_dict["content"],
                }  # convert `event_type` enum to str
                if webhook["platform"] == "discord":
                    data = {"content": str(stringified_event_dict)}
                elif webhook["platform"] == "slack":
                    data = {"text": str(stringified_event_dict)}
                else:
                    data = stringified_event_dict
                await self._post_to_webhook_with_retries(
                    client_session=client_session,
                    webhook_url=webhook["url"],
                    data=data,
                )
