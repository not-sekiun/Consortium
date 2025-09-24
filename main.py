def _recursively_remove_plugin_from_plugin_dependency_graph(
    plugin: str,
    plugin_dependency_graph: dict[str, set[str]],
) -> set[str]:
    plugins_to_remove = {plugin}
    removed_plugins = set()

    while plugins_to_remove:
        plugin_to_remove = plugins_to_remove.pop()
        if plugin_to_remove in plugin_dependency_graph:
            del plugin_dependency_graph[plugin_to_remove]
            removed_plugins.add(plugin_to_remove)
            # Find plugins that depend on the removed plugin
            for dependent_plugin, dependencies in list(
                plugin_dependency_graph.items(),
            ):  # Iterate over a copy to allow deletion
                if plugin_to_remove in dependencies:
                    plugins_to_remove.add(dependent_plugin)

    return removed_plugins


def _remove_plugins_with_missing_dependencies(
    plugin_dependency_graph: dict[str, set[str]],
) -> None:
    plugins_to_remove = set()

    for plugin, dependencies in plugin_dependency_graph.items():
        for dependency in dependencies:
            if dependency not in plugin_dependency_graph:
                plugins_to_remove.add(plugin)

    for plugin in plugins_to_remove:
        removed_plugins = _recursively_remove_plugin_from_plugin_dependency_graph(
            plugin,
            plugin_dependency_graph,
        )
        if removed_plugins:
            print(
                f"The plugin dependency '{plugin}' that was not installed "
                f"either directly or indirectly caused the following plugins to be "
                f"removed: {", ".join([f"'{plugin}'" for plugin in removed_plugins])}",
            )


def _remove_plugins_with_circular_dependencies(
    plugin_dependency_graph: dict[str, set[str]],
) -> None:
    visited_nodes = set()
    dependency_path = []  # Holds our current recursion path through the graph.
    circular_dependencies = []

    def _visit_node(node: str) -> None:
        dependency_path.append(node)
        # Algorithm has arrived at a leaf node.
        if not plugin_dependency_graph[node]:
            dependency_path.pop()
            visited_nodes.add(node)
            return
        # There are more nodes to explore, so start checking them.
        for neighbor in plugin_dependency_graph[node]:
            # Skip fully explored nodes.
            if neighbor in visited_nodes:
                continue
            # Algorithm has found a circular dependency.
            if neighbor in dependency_path:
                circular_dependencies.append(
                    dependency_path[dependency_path.index(neighbor) :] + [neighbor],
                )
                continue
            _visit_node(neighbor)
        # After visiting all our neighbor nodes this current node is marked as fully
        # explored. We are about to return up one recursion level so we need to remove
        # the last node from the path as well.
        dependency_path.pop()
        visited_nodes.add(node)

    for plugin in plugin_dependency_graph:
        if plugin in visited_nodes:  # Skip fully explored nodes.
            continue
        _visit_node(plugin)

    # Remove plugins with circular dependencies.
    for cycle in circular_dependencies:
        unique_plugins = set(list(cycle))
        removed_plugins = []
        for plugin in unique_plugins:
            removed_plugins += _recursively_remove_plugin_from_plugin_dependency_graph(
                plugin,
                plugin_dependency_graph,
            )
        if removed_plugins:
            print(
                f"The detected circular plugin dependency "
                f"{" -> ".join([f"'{plugin}'" for plugin in cycle])} either directly "
                f"or indirectly caused the following plugins to be removed: "
                f"{", ".join([f"'{plugin}'" for plugin in removed_plugins])}",
            )


dependency_graph = {
    "a": {"b", "e"},
    "b": {"c", "f"},
    "c": {"d", "a"},
    "d": {"c"},
    "e": {"f"},
    "f": {"g", "b"},
    "g": {"f"},
}
_remove_plugins_with_circular_dependencies(dependency_graph)
