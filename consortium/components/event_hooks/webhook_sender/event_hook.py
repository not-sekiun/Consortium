import json

import aiohttp
import jsonschema

from consortium.framework.event_hooks import base_event_hook, event_type


class EventHook(base_event_hook.BaseEventHook):
    name = "Webhook sender"
    description = (
        "This event hook forwards event data for any set of specific events to any set "
        "of arbitrarily specified webhooks through an HTTP POST request. The particular "
        "events it listens for and webhooks it sends data to are configure through the "
        "`config.json` file in the event hook's project folder."
    )

    async def on_event_hook_triggered(self, event):
        # Set a flag to perform initial setup when an event hook is first called
        if not hasattr(self.environment, "already_performed_setup"):
            self.environment.already_performed_setup = True
            self.environment.events_to_send = []
            self.environment.webhooks_to_send_to = []

            try:
                with (self.event_hook_project_folder / "config.json").open(
                    "r",
                ) as config_file:
                    try:
                        config = json.load(config_file)
                    except json.decoder.JSONDecodeError:
                        self.event_hook_logger.error(
                            "Failed to load webhook sender event hook configuration "
                            "file. The configuration file does not contain valid JSON "
                            "data.",
                        )
                        return

                    config_json_schema = {
                        "type": "object",
                        "properties": {
                            "events_to_send": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                },
                            },
                            "webhooks_to_send_to": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                },
                            },
                        },
                    }
                    try:
                        jsonschema.validate(config, config_json_schema)
                    except jsonschema.ValidationError as exc:
                        self.event_hook_logger.error(
                            "Failed to load webhook sender event hook configuration "
                            "file. The configuration file's format does not match the "
                            "expected configuration file JSON schema :",
                            exc.message,
                        )
                        return

                    for event in config["events_to_send"]:
                        if event not in event_type.EventType:
                            self.event_hook_logger.warning(
                                "Failed to load webhook sender event hook configuration "
                                f"file. The provided string '{event}' in the set of "
                                "event types to send is not a valid event type.",
                            )
                            continue
                        self.event_types.add(event)
                    self.environment.webhooks_to_send_to = config["webhooks_to_send_to"]
            except FileNotFoundError:
                self.event_hook_logger.error(
                    "Failed to load webhook sender event hook configuration file. "
                    "Configuration file `config.json` not found at the event hook's "
                    f"project folder `{self.event_hook_project_folder}`.",
                )

        async with aiohttp.ClientSession() as client_session:
            for webhook in self.environment.webhooks_to_send_to:
                await client_session.post(
                    webhook,
                    json=event.to_json(),
                )
