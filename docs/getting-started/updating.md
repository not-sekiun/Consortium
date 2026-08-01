## Updating Consortium

To update Consortium, pull any new changes from the GitHub repository and install the
updated dependencies.

=== "Manual install"

    ```shell
    cd path/to/Consortium
    git pull
    uv sync --all-packages
    ```

=== "Docker install"

    ```shell
    cd path/to/Consortium
    git pull
    docker compose up -d --build
    ```

    Rebuilding installs the updated dependencies into a new image and recreates the
    server from it. Everything under `data/` is bind mounted from the host and is left
    untouched by the rebuild.

## Enabling Auto-updating for Consortium

!!! note
    Auto-updating applies to a manual install. It updates the server from its Git
    checkout, which a Docker install's image does not contain. Update a Docker install by
    rebuilding it, as shown above.

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
[Plugins](../framework-api/plugins/plugins-overview.md) section.
