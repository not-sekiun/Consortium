import hashlib
import os
import pathlib
import subprocess
import sys

import tomlkit


# Before server starts up, we need to resolve all declared component python
# dependencies against the project root. Then checks for any changes to decide whether
# we restart.
def main():
    consortium_root_path = pathlib.Path(__file__).resolve().parents[2]
    uv_lock_file = consortium_root_path / "uv.lock"
    pyproject_toml_file = consortium_root_path / "pyproject.toml"
    components_path = pathlib.Path(__file__).resolve().parents[1] / "components"

    # Store hash of uv lock file first to detect if any changes were made to it
    old_uv_lock_hash = hashlib.md5(uv_lock_file.read_bytes()).hexdigest()

    with pyproject_toml_file.open("rb") as f:
        pyproject_toml_data = tomlkit.parse(f.read())

    # Walk the components directory recursively looking for any components that declare
    # third party python packages. These must be directories that contain a
    # manifest.json with a pyproject.toml declared adjaecent to it
    for path in components_path.glob("**/manifest.json"):
        pyproject_toml_path = path.parent / "pyproject.toml"
        # Add the component directory as a workspace in the root project uv lock file
        # so uv can see it
        if pyproject_toml_path.exists():
            pyproject_toml_data["tool"]["uv"]["workspace"].append(
                str(path.parent.relative_to(consortium_root_path))
            )

    # Write changes back to uv
    with pyproject_toml_file.open("w") as f:
        f.write(tomlkit.dumps(pyproject_toml_data))

    # chdir to repository root to run uv syncing commands against it in case the server
    # is started from a different directory
    old_path = pathlib.Path(".")
    os.chdir(consortium_root_path)

    # After walking sync all dependencies
    subprocess.run(["uv", "lock"])

    new_uv_lock_hash = hashlib.md5(uv_lock_file.read_bytes()).hexdigest()

    # Syncing dependencies caused a change, install the new packages and restart the
    # server
    if new_uv_lock_hash != old_uv_lock_hash:
        subprocess.run(["uv", "sync", "--all-packages"])
        subprocess.Popen(["uv", "run", "consortiun.py", "server"])  # start new process
        sys.exit(0)  # exit current one

    # Change back to the original directory
    os.chdir(old_path)
