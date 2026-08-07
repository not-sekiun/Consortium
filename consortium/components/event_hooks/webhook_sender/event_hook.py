import asyncio
import json

import aiohttp
import jsonschema

from consortium.framework.event_hooks import BaseEventHook, EventType


class EventHook(BaseEventHook):
    label = "consortium.event_hooks.webhook_sender"
    name = "Webhook sender"
    description = (
        "This event hook forwards event data for any set of specific events to any set "
        "of arbitrarily specified webhooks. The particular events it listens for and "
        "webhooks it sends data to are configured through the `config.json` file in "
        "the event hook's root directory. Currently supports Discord, Slack, and "
        "generic HTTP POST webhooks."
    )
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0a1"
    authors = {"Sekiun (github.com/not-sekiun)"}
    event_types = {"STOP_SERVER", "START_SERVER", "AGENT_REGISTERED"}

    async def on_setup(self) -> None:
        # The hook stays subscribed to its default event types even when configuration
        # fails to load, so `on_triggered` still runs. Establish the disabled state up
        # front so every failure path below can simply return and leave the hook inert
        # rather than raising on the first event that fires.
        self.environment.config = None
        self.environment.warned_about_missing_config = False

        try:
            with (self.root_directory / "config.json").open(
                "r",
            ) as config_file:
                config = json.load(config_file)
        except FileNotFoundError:
            self.event_logger.failure(
                "Failed to load webhook sender event hook configuration file. "
                "Configuration file `config.json` not found at the event hook's "
                f"root directory `{self.root_directory}`. Copy `config.example.json` "
                "to `config.json` to configure it. No events will be forwarded.",
            )
            return
        except json.decoder.JSONDecodeError:
            self.event_logger.failure(
                "Failed to load webhook sender event hook configuration "
                "file. The configuration file does not contain valid JSON "
                "data. No events will be forwarded.",
            )
            return

        # `events` and `webhooks` are marked required (as are the fields of each webhook
        # entry) because both are indexed directly further down. Without this an empty
        # object would validate and then raise `KeyError` instead of being reported as
        # a configuration problem.
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
                        "required": ["platform", "url"],
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
            "required": ["events", "webhooks"],
        }
        try:
            jsonschema.validate(config, config_json_schema)
        except jsonschema.ValidationError as exc:
            self.event_logger.failure(
                "Failed to load webhook sender event hook configuration "
                "file. The configuration file's format does not match the "
                f"expected configuration file JSON schema: {exc.message}. No events "
                "will be forwarded.",
            )
            return

        for event in config["events"]:
            if event not in EventType:
                self.event_logger.warning(
                    f"The provided string '{event}' in the set of event types to send "
                    "is not a valid event type.",
                )
                continue
            self.subscribe_to_event_type(event)

        if not config["webhooks"]:
            self.event_logger.warning(
                "The webhook sender event hook has no webhooks configured. Events will "
                "be received but not forwarded anywhere.",
            )

        self.environment.config = config

    async def _post_to_webhook_with_retries(
        self,
        client_session: aiohttp.ClientSession,
        webhook_url: str,
        data: dict,
    ) -> None:
        max_retries = self.environment.config.get("max_retries", 3)
        retry_delay_seconds = self.environment.config.get("retry_delay_seconds", 5)
        # A configured value of 0 leaves the loop body unreached, which would silently
        # discard the event. Treat it as a single attempt so the webhook is always tried
        # at least once.
        attempts = max(max_retries, 1)
        for i in range(attempts):
            is_last_attempt = i == attempts - 1
            retry_suffix = (
                "" if is_last_attempt else f" Retrying... (Attempt {i + 1}/{attempts})"
            )
            try:
                async with client_session.post(
                    webhook_url,
                    json=data,
                ) as response:
                    if response.status == 200 or response.status == 204:
                        return
                    else:
                        self.event_logger.warning(
                            f"Failed to send event data to webhook at '{webhook_url}'. "
                            f"Received unexpected status code {response.status}."
                            f"{retry_suffix}",
                        )
            # `TimeoutError` is not an `aiohttp.ClientError`, so it has to be named
            # explicitly or a slow webhook would propagate out of `on_triggered`.
            except (aiohttp.ClientError, TimeoutError) as exc:
                self.event_logger.warning(
                    f"Failed to send event data to webhook at '{webhook_url}'. "
                    f"Error: {exc}.{retry_suffix}",
                )
            # Sleeping after the final attempt only delays the remaining webhooks.
            if not is_last_attempt:
                await asyncio.sleep(retry_delay_seconds)

        self.event_logger.failure(
            f"Giving up on sending event data to webhook at '{webhook_url}' after "
            f"{attempts} attempt(s). The event was dropped.",
        )

    async def on_triggered(self, event):
        # Configuration failed to load during setup. Drop the event instead of raising,
        # and say so only once so a broken configuration does not flood the event log
        # with one entry per event fired.
        if self.environment.config is None:
            if not self.environment.warned_about_missing_config:
                self.event_logger.warning(
                    "The webhook sender event hook is not forwarding events because "
                    "its configuration failed to load. Fix `config.json` and reload "
                    "the event hook, or disable it in `manifest.json`.",
                )
                self.environment.warned_about_missing_config = True
            return

        event_dict = event.to_json()

        async with aiohttp.ClientSession() as client_session:
            for webhook in self.environment.config["webhooks"]:
                # TODO: Consider having per-webhook event type data formatting options
                #  for better compatibility with different webhook platforms
                if webhook["platform"] == "discord":
                    embed = {
                        "title": f"Event: {event_dict['event_type']}",
                        "description": event_dict["message"],
                    }
                    data = {"embeds": [embed]}
                elif webhook["platform"] == "slack":
                    data = {
                        "attachments": [
                            {
                                "title": event_dict["event_type"],
                                "text": event_dict["message"],
                            }
                        ]
                    }
                else:
                    data = {
                        "event_type": str(event_dict["event_type"]),
                        "message": event_dict["message"],
                        "data": event_dict["data"],
                    }
                # Webhooks are independent destinations, so an unexpected failure
                # against one must not stop the event reaching the others.
                try:
                    await self._post_to_webhook_with_retries(
                        client_session=client_session,
                        webhook_url=webhook["url"],
                        data=data,
                    )
                except Exception as exc:
                    self.event_logger.failure(
                        "Unexpected error while sending event data to webhook at "
                        f"'{webhook['url']}': {exc!r}. Continuing with the remaining "
                        "webhooks.",
                    )
