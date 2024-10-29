from __future__ import annotations

import csv
import logging
import os
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Optional, Union
from .index import Index

import requests
import dotenv

from .errors import (
    NotInDataBaseError,
    NotOpenAccessError,
    OpenAlexError,
    OpenAlexRateLimitError,
    PDFNotAvailableError,
    RateLimitError,
    WileyQuoataException,
)

USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0"
]  # List of user agents to choose from when scraping

logger = logging.getLogger(__name__)

dotenv.load_dotenv()

WILEY_TDM_TOKEN = os.getenv("Wiley-TDM-Client-Token")

if not WILEY_TDM_TOKEN:
    logging.warning(f"No Wiley-TDM-Client-Token found in .env. Requests to the wiley API will not be possible")


class Downloader(ABC):
    """Interface for creating a Downloader"""

    @abstractmethod
    def request_pdf(self):
        """Method that downloads the content of a file."""
        pass

    @abstractmethod
    def bulk_request_pdf(self):
        """Method that downloads the contents of multiple files at once."""
        pass


class Cord19Reader:
    """Read Metadata from Cord19 and constructs an index of which PDFs are already downloaded.

    Args
    ----
    index_path : Union[Path, str]
        Path to the download index json file.

    csv_path : Union[Path, str]
        Path to the metadata csv file.

    Raises
    ------
    FileNotFoundError
        When specified CSV file could not be found.
    """

    def __init__(self, csv_path: Union[str, Path]) -> None:

        self.csv_path = Path(str(csv_path))

        if not self.csv_path.exists():
            raise FileNotFoundError("Specified CSV File could not be found.")

    def read_metadata(self, index: Index) -> Generator[dict]:
        """Read the metadata.csv file.

        Args
        ----
        index : Index
            Uses the index object to check wheater the record has already been requested.
        """
        with open(self.csv_path, "r") as fp:
            reader = csv.reader(fp)
            headers = next(reader)

            for row in reader:
                cord19_row = dict(zip(headers, row))
                cord19_row["doi"] = cord19_row["doi"].lower()
                if not cord19_row["doi"] or cord19_row["doi"] in index:
                    continue
                cord19_row["sha"] = str(cord19_row["sha"]).split(";")
                yield cord19_row


class OpenAlex:
    """Object to search the OpenAlex works api.

    Args
    ----
    email : str
        If supplied with an email OpenAlex will put you in the polite pool.
        Read more under https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication#the-polite-pool
    """

    def __init__(self, email: Optional[str] = None) -> None:
        self.email = email

    def find_pdf_url(self, doi: str) -> str:
        """Find the url to a pdf via DOI.

        Args
        ----
        doi : str
           DOI used to search a PDF Url.

        Raises
        ------
        NotOpenAccessError
            When the requested file has no known OpenAcess URL.

        FileNotFoundError
            When the requested DOI could not be found in OpenAlex.

        Returns
        -------
        str
            The PDF URL of the requested DOI."""

        entry = self._request_entry_openalex(doi)
        return self._find_oa_url(entry)

    def bulk_find_pdf_url(self, doi_list: list[str]) -> list[str, str]:
        results = self._batch_request_entry_openalex(doi_list)
        return_list = []
        for result in results:

            try:
                return_list.append((result["doi"], self._find_oa_url(result)))

            except NotOpenAccessError as e:
                pass
            except NotInDataBaseError as e:
                pass

        return return_list

    def _batch_request_entry_openalex(self, doi_list: set[str]) -> dict:

        if len(doi_list) > 50:
            raise OpenAlexError("Only alowed 50 DOIs per requets")

        params = {"per-page": 50, "filter": "doi:" + "|".join(doi_list)}

        if self.email:
            params["mailto"] = self.email

        req = requests.get("https://api.openalex.org/works", params=params)

        if req.status_code == 429:
            raise OpenAlexRateLimitError("Limit of 100.000 requests per day reached.")

        req_json = req.json()

        if req_json["meta"]["count"] != len(doi_list):
            pass

        return req_json["results"]

    def _request_entry_openalex(self, doi: str) -> dict:
        """Requests a single entry from OpenAlex by filtering the OpenAlex Works endpoint by DOI.

        Args
        ----
        doi : str
            DOI of the entry.

        Raises
        ------
        NotInDataBaseError
            When the requested DOI could not be found in OpenAlex.

        Returns
        -------
        dict
            JSON response from the OpenAlex API.
        """

        params = {"filter": "doi:" + doi}

        if self.email:
            params["mailto"] = self.email

        req = requests.get("https://api.openalex.org/works", params=params)

        if req.status_code == 429:
            raise OpenAlexRateLimitError("Limit of 100.000 requests per day reached.")

        if req.status_code != 200 or req.json()["meta"]["count"] == 0:
            raise NotInDataBaseError("No OpenAlex entry could be found for " + doi)

        result = req.json()["results"][0]

        if result["doi"].lower() == doi.lower():
            raise NotInDataBaseError("No OpenAlex entry could be found for " + doi)

        return result

    def _find_oa_url(self, res: dict) -> str:
        """Retrieves an Open Acess URL from the OpenAlex response if available.

        Args
        ----
        res : dict
            JSON representation of the OpenAlex entry.

        Raises
        ------
        NotOpenAccessError
            When the requested file has no known OpenAcess URL.

        Returns
        -------
        str
            OpenAccess URL.
        """

        if not res["open_access"]["is_oa"]:
            raise NotOpenAccessError("Could not find a OpenAccess URL for the requested DOI")

        if res["primary_location"]["is_oa"] and res["primary_location"]["pdf_url"]:
            return res["primary_location"]["pdf_url"]

        return res["open_access"]["oa_url"]


class URLDownloader(Downloader):
    """Tries to download PDF's via a open-access URL.

    Methods
    -------
    request_pdf
        Downloads the open-access pdf and saves it into the download_dir folder.
    bulk_request_pdf
        Not yet implemented.
    """

    def request_pdf(self, pdf_url: str, return_full_request: bool = False) -> Union[bytes, requests.Request]:
        """Downloads the open-access pdf and saves it into the download_dir folder.

        Args
        ----
            pdf_url : str
                URL of pdf to download

        Raises
        ------
        PDFNotAvailableError
            Raised when the `Content-Type` header of the response does not contain `application/pdf`.

        Returns
        -------
        bytes
            PDF file as bytes.
        """
        req = requests.get(
            pdf_url,
            allow_redirects=True,
            timeout=5,
            headers={"User-Agent": random.choice(USER_AGENTS)},
        )

        if req.status_code == 429:
            raise RateLimitError(f"Rate limit for {pdf_url} reached.")

        if req.status_code != 200:
            raise PDFNotAvailableError(f"Request failed with error code {req.status_code}, {req.content}")
        allowed_content_type = ["application/pdf", "application/octet-stream"]
        type_ = req.headers["Content-Type"]
        if type_ not in allowed_content_type:
            raise PDFNotAvailableError(f"Response content type {type_} for {pdf_url}.")

        return req.content

    def bulk_request_pdf(self, pdf_urls: list[str]) -> list[bytes]:
        raise NotImplementedError("bulk_request_pdf is currently not implemented.")


class WileyURLDownloader(Downloader):
    """Tries to download PDF's via Wiley API.

    Methods
    -------
    request_pdf
        Downloads the pdf and saves it into the download_dir folder.
    bulk_request_pdf
        Not yet implemented.
    """

    def request_pdf(self, pdf_url: str, return_full_request: bool = False) -> Union[bytes, requests.Request]:
        """Downloads the open-access pdf and saves it into the download_dir folder.

        Args
        ----
            pdf_url : str
                URL of pdf to download

        Raises
        ------
        PDFNotAvailableError
            Raised when the `Content-Type` header of the response does not contain `application/pdf`.

        Returns
        -------
        bytes
            PDF file as bytes.
        """

        req = requests.get(
            pdf_url,
            allow_redirects=True,
            timeout=5,
            headers={"User-Agent": random.choice(USER_AGENTS), "Wiley-TDM-Client-Token": WILEY_TDM_TOKEN},
        )

        if req.status_code == 500:
            raise WileyQuoataException(f"Wiley QuoataViolation wait a few minutes and then continue.")

        if req.status_code == 429:
            raise RateLimitError(f"Rate limit for Wiley API reached.")

        if req.status_code != 200:
            raise PDFNotAvailableError(f"Request failed with error code {req.status_code}, {req.content}")
        allowed_content_type = ["application/pdf", "application/octet-stream"]
        type_ = req.headers["Content-Type"]
        if type_ not in allowed_content_type:
            raise PDFNotAvailableError(f"Response content type {type_} for.")

        return req.content

    def bulk_request_pdf(self, pdf_urls: list[str]) -> list[bytes]:
        raise NotImplementedError("bulk_request_pdf is currently not implemented.")

    def _doi_strip(self, doi: str):
        if doi.startswith("https://doi.org/"):
            return doi[len("https://doi.org/") :]
        else:
            return doi
