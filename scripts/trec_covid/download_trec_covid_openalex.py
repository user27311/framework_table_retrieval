import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import ir_datasets

from cord19_plus.downloadpdf.downloaders import OpenAlex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def chunk_list(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def reqest_func(openalex: OpenAlex, chunk):
    urls = openalex.bulk_find_pdf_url(chunk)
    time.sleep(1)  # at 5 max workers no more then 5 req per seconds can be made so wait 1 sek after each request
    return urls


def main():
    dataset = ir_datasets.load("cord19/trec-covid")
    base_path = Path("")  # set path
    json_path = base_path / Path("pdf_urls.json")

    open_alex = OpenAlex()

    dois = [doc.doi for doc in dataset.docs_iter()]
    chunks = list(chunk_list(dois, 50))
    logging.info(f"Number of requests: {len(chunks)}")

    results_chunk = []
    idx = 0
    with ThreadPoolExecutor(max_workers=5) as ex:
        future = [ex.submit(reqest_func, open_alex, chunk) for chunk in chunks]

        for f in future:
            path_tmp = json_path / Path(f"req_{idx}.json")
            results_chunk.append(f.result())
            if idx % 10 == 0:
                logging.info(f"Number of past requests: {idx}")

            if idx > 1 and idx % 100 == 0:
                path_tmp = base_path / Path(f"req_{idx-100}-{idx}.json")
                json.dump(results_chunk, open(path_tmp, "w"))
                results_chunk.clear()

            idx += 1

        path_tmp = base_path / Path(f"req_{idx-len(results_chunk)}-{idx}.json")
        json.dump(results_chunk, open(path_tmp, "w"))


if __name__ == "__main__":
    main()
