# Logging

By default, the server loads its logging configuration from
`data/server/logging_config.json`. This file describes how the server logs its events and
messages and to where. Modify it to change the logging level, format, destination,
rotation, and retention of the server's logs.

```json title="logging_config.json"
{
    "level": "INFO",
    "log_file": "data/server/logs/{time}.log",
    "rotation": null,
    "retention": 1,
    "colorize": true
}
```

| Field       | Description                                                                                                                                                                   | Default Value                   |
|-------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------|
| `level`     | The minimum logging level for messages to be logged. One of: `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, or `SUCCESS`.                                          | `"INFO"`                        |
| `log_file`  | The file path where log files will be written. Supports dynamic placeholders like `{time}` for timestamps.                                                                    | `"data/server/logs/{time}.log"` |
| `rotation`  | The condition for rotating log files. A file size (e.g. `"10 MB"`), a time period (e.g. `"1 day"`), a specific time (e.g. `"00:00"`), or `null` to disable rotation.          | `null`                          |
| `retention` | The number of log files to retain before deletion, or a time period (e.g. `"1 week"`). An integer or string, or `null` to keep all logs indefinitely.                        | `1`                             |
| `colorize`  | Whether to enable colorized output in the terminal/console. `true` to enable colored log messages in stdout, or `false` to disable.                                          | `true`                          |

To load a logging configuration file from a different location, use the `-l/--logging-config`
flag when starting the server. Passing `--debug` at startup overrides `level` and raises it
to `DEBUG` for that run.

```shell
uv run consortium.py server -l path/to/custom_logging_config.json
```

??? note "More on logging configuration"
    Internally Consortium uses the `Loguru` logging library. For more information about the
    logging configuration options, refer to the
    [Loguru documentation](https://loguru.readthedocs.io/en/stable/api/logger.html#configuration).
