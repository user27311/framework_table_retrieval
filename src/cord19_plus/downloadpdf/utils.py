from typing import Union
from pathlib import Path
import json


def read_open_alex_json_dump(oa_requests_path: Union[str, Path]) -> list[str, str]:
    oa_requests_path = Path(str(oa_requests_path))
    all_dois = []

    for doc_path in oa_requests_path.iterdir():
        doc = json.load(open(doc_path, "r"))
        for req in doc:
            all_dois.extend(req)

    return all_dois
