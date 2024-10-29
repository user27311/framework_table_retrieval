from cord19_plus.downloadpdf.downloaders import Index, Status, IndexRow
from typing import Union
from pathlib import Path
import requests
import pickle


# script requests all unavailable pdfs and saves the responses as pickle object files in a desired directory
def main(index_path: Path, download_dir_path: Path, pickle_dir_path: Path):
    index = Index.from_jsonl(index_path, download_dir_path)
    unavailable = filter_by_status(index, Status.UNAVAILABLE)

    for idx, entry in enumerate(unavailable):
        resp = requests.get(
            entry.pdf_url[0],
            allow_redirects=True,
            timeout=5,
            params={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0"},
        )
        save_path = pickle_dir_path / Path(f"{idx}.pickle")
        pickle.dump(resp, open(save_path, "wb"))


# funtion for filtering the index obj by status
def filter_by_status(index: Index, status: Union[Status, list[Status]]) -> list[IndexRow]:
    if not isinstance(status, list):
        status = [status]

    status = set([s.value for s in status])
    return [entry for doi, entry in index.items() if entry.status in status]


if __name__ == "__main__":
    # define paths
    base_path = Path("")  # add your base path
    index_path = base_path / Path("index.jsonl")
    download_dir_path = base_path / Path("pdfs")
    pickle_dir_path = base_path / Path("pickles")
    main(index_path, download_dir_path, pickle_dir_path)
