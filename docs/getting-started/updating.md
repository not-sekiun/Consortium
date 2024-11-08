## Updating Consortium

To update Consortium, pull any new changes from the GitHub repository and install the
updated Python dependencies using Poetry.

1. Navigate to the root directory of the Consortium repository.
    ```shell
    cd path/to/Consortium
    ```

2. Pull the latest changes from the GitHub repository.
    ```shell
    git pull
    ```

3. Install any updated or newly added Python dependencies using Poetry.
    ```shell
    poetry install
    ```

## Enabling Auto-updating for Consortium

If you want the Consortium server to perform its own automatic checking/installation of
updates from the GitHub repository, you can enable the `auto_updater` plugin that is
bundled by default with the framework. To enable the `auto_updater` plugin, navigate to
the plugins configuration file at
`consortium/framework/plugins/auto_updater/plugin_project_manifest.json` and set the
`enabled` field to `true`.

```json hl_lines="14" title="plugin_project_manifest.json"
{
    "listener": {
        "filepath": "listener.py",
        "symbol": "Listener"
    },
    "listener_template": {
        "filepath": "listener_template.py",
        "symbol": "ListenerTemplate"
    },
    "listener_type": {
        "filepath": "listener_type.py",
        "symbol": "LISTENER_TYPE"
    },
    "enabled": true
}
```

Now, whenever the server starts, it will check for updates from the GitHub repository
and attempt to install them.

For more information about plugins and how to create your own, refer to the
[Plugins]() section of the documentation.
