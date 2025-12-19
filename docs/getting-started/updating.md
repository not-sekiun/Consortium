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
    uv sync
    ```

## Enabling Auto-updating for Consortium

If you want the Consortium server to perform its own automatic checking/installation of
updates from the GitHub repository, you can enable the `auto_updater` plugin that is
bundled by default with the framework. Navigate to
the plugin configuration file at
`consortium/components/plugins/auto_updater/manifest.json` and set the
`enabled` field to `true`.

```json hl_lines="3" title="manifest.json"
{
    "entry_point": "plugin:Plugin",
    "enabled": true
}
```

Now, whenever the server starts, it will check for updates from the GitHub repository
and attempt to install them.

For more information about plugins and plugin development, refer to the
[Plugins]() section.
