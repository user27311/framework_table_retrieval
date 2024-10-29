import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import ir_datasets
from requests.exceptions import RequestException

from cord19_plus.downloadpdf.downloaders import Index, Status, URLDownloader
from cord19_plus.downloadpdf.errors import PDFNotAvailableError


logging.basicConfig()
logger = logging.getLogger(__name__)


def req_func(dl, index, doi):
    if doi[0] not in index.keys():
        try:
            pdf_bytes = dl.request_pdf(doi[1])
            index.save_file(pdf_bytes, doi[0], doi[1])

        except PDFNotAvailableError:
            index.add(doi[0], Status.UNAVAILABLE, None, doi[1])

        except RequestException as e:
            index.add(doi[0], Status.REQUEST_ERROR, None, doi[1])


if __name__ == "__main__":
    base_path = Path("")  # set path
    oa_requests_path = base_path / Path("oa-requests")
    index_path = base_path / Path("index.jsonl")
    pdfs_path = base_path / Path("pdfs")

    index = Index.from_jsonl(index_path, pdfs_path)

    all_dois = []

    for doc_path in oa_requests_path.iterdir():
        doc = json.load(open(doc_path, "r"))
        for req in doc:
            all_dois.extend(req)

    dl = URLDownloader()

    with ThreadPoolExecutor(max_workers=30) as ex:
        for idx, doi in enumerate(all_dois):
            if doi[0] not in index:
                ex.submit(req_func, dl, index, doi)
                if idx % 100:
                    logger.info(f"checked {idx} pdfs")
