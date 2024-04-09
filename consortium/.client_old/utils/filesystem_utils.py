import os
import platform


def parse_system_environment_variables_in_filepaths(filepath: str) -> str:
    filepath = os.path.normpath(filepath)
    split_filepath = filepath.split(os.sep)

    for component_index, component in enumerate(split_filepath):
        if (
            component.startswith("%")
            and component.endswith("%")
            and platform.system() == "Windows"
        ):  # Windows cmd.exe
            env_var = component[1:-1]
            if env_var in os.environ:
                split_filepath[component_index] = os.environ[env_var]
        elif (
            component.startswith("$env:") and platform.system() == "Windows"
        ):  # Windows powershell.exe
            env_var = component[5:]
            print(env_var)
            if env_var in os.environ:
                split_filepath[component_index] = os.environ[env_var]
        elif (
            component.startswith("$") and platform.system() == "Linux"
        ):  # Linux bash like shells
            env_var = component[1:]
            if env_var in os.environ:
                split_filepath[component_index] = os.environ[env_var]

    return os.path.join(*split_filepath)
