import json
from pathlib import Path


def load_jsons(folder_in: str | Path):
    """
    Load parsed documents from json-files to a list

        :param folder_in:
        :return: list[dict]
    """
    folder_in = Path(folder_in)
    jsons = []
    for f_name in sorted(folder_in.glob("*.json")):
        with open(f_name, "r") as f:
            _json = json.load(f)
            jsons.append(_json)
    return jsons
