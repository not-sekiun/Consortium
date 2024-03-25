import json
from typing import Type

from pydantic import BaseModel, ValidationError


# This utility function is used at server startup to load data from JSON files into
# instantiated pydantic models to be used by the framework. Error handling is not
# delegated to the function caller but done in the function itself (where error messages
# are just printed) because if this function fails to load the JSON file properly for
# any reason the server will simply refuse to start
def load_json_file_as_pydantic_model(
    json_file_path: str,
    pydantic_model: Type[BaseModel],
) -> tuple[bool, BaseModel | None]:
    try:
        with open(json_file_path, "r") as f:
            data = f.read()
        json_data = json.loads(data)
        instantiated_model = pydantic_model(**json_data)
        return True, instantiated_model
    except FileNotFoundError:
        print(f"Could not find file: {json_file_path} (Does the file exist?)")
    except json.JSONDecodeError:
        print(
            "Could not load the file's JSON contents: {json_file_path} (Does the file contain valid JSON data?)",
        )
    except ValidationError:
        print(
            "Failed to validate the file's JSON contents: {json_file_path} (Does the file contain JSON data conforming to the expected JSON schema?)",
        )
    return False, None
