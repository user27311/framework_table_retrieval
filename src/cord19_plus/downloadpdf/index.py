import json
import logging
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PosixPath
from typing import Optional, Union

import urllib

logger = logging.getLogger(__name__)


class Status(Enum):
    """Used in the index to keep track if a filedownload has previously failed or succeeded."""

    UNAVAILABLE = 0
    DOWNLOADED = 1
    NOT_OPEN_ACCESS = 2
    NOT_IN_OPENALEX = 3
    RATE_LIMIT_ERROR = 4
    REQUEST_ERROR = 5


@dataclass
class IndexRow:
    """Dataclass representing one row inside the Index object."""

    status: Status
    pdf_path: Path = None
    pdf_url: str = None

    @staticmethod
    def from_json(json_dict: dict[str, Union[str, int]]):
        """Initiate a IndexRow from a raw json dictionary.

        Args
        ----
        json_dict : dict[str, Union[str, int]]
            Dictionary containing the following keys: doi (str), status (int), pdf_path (str), pdf_url (str)

        Returns
        -------
        IndexRow
            The constructed IndexRow object.
        """
        if json_dict["pdf_path"] == "None" or json_dict["pdf_path"] == "" or not json_dict["pdf_path"]:
            path = None
        else:
            path = Path(json_dict["pdf_path"])

        return IndexRow(
            Status(json_dict["status"]),
            path,
            json_dict["pdf_url"],
        )

    def to_json(self) -> dict[str, str]:
        """Convert an IndexRow into a json dictionary for storing.

        Returns
        -------
        dict[str, Union[str, int]]
            Dictionary representation of a IndexRow."""

        if self.pdf_path == "None" or self.pdf_path == "":
            path = None
        elif isinstance(self.pdf_path, Path):
            path = self.pdf_path.as_posix()
        elif isinstance(self.pdf_path, PosixPath):
            path = str(self.pdf_path)
        else:
            path = self.pdf_path
        return {
            "status": self.status.value,
            "pdf_path": path,
            "pdf_url": self.pdf_url,
        }


class Index(dict):
    """Index object that stores information about all PDF's which were already attempted to download.
    Each entry in the Index object is stored under a doi which links to a IndexRow object.
    Also handles the storing of PDF's.

    Attributes
    ----------
    index_path : Union[str, Path]
        Path to the .jsonl file that stores the index.

    download_dir : Union[str, Path]
        Directory to which the PDF's are downloaded.

    Methods
    -------
    load
        Reads and constructs the index from the jsonl file.

    from_jsonl
        Creates an Index object from the jsonl file.
    """

    def __init__(self, index_path: Union[str, Path], download_dir: Union[str, Path]):
        self.index_path = Path(str(index_path))
        self.download_dir = Path(str(download_dir))

        if not self.index_path.exists():
            self.index_path.touch()

        if not self.download_dir.is_dir():
            self.download_dir.mkdir()

        super().__init__(self)

    def load(self) -> None:
        """If not previously loaded via the Index.from_jsonl method, use this method to load the index.
        Clears the current index and reloads is from the jsonl file."""
        self.clear()
        with open(self.index_path, "r") as fp:
            line = fp.readline()
            while line != "":
                json_dict = json.loads(line)
                self[json_dict["doi"]] = IndexRow(**json_dict)
                line = fp.readline()

    @staticmethod
    def from_jsonl(index_path: Union[str, Path], download_dir: Union[str, Path]):
        """Read the index.jsonl file.

        Args
        ----
        index_path : Union[str, Path]
            Path to the .jsonl file that stores the index.

        download_dir : Union[str, Path]
            Directory that stores downloaded PDF's.

        Returns
        -------
        Index
            A constructed index, containing information about all downloaded pdf's."""

        index_path = Path(str(index_path))
        download_dir = Path(str(download_dir))

        index = Index(index_path, download_dir)

        with open(index_path, "r") as fp:
            line = fp.readline()
            while line != "":
                json_dict = json.loads(line)
                key = json_dict["key"]
                del json_dict["key"]
                indexRow = IndexRow.from_json(json_dict)
                if indexRow.pdf_path:
                    indexRow.pdf_path = download_dir / indexRow.pdf_path
                index[key] = indexRow

                line = fp.readline()
        return index

    def add(
        self,
        key: str,
        status: Union[Status, str],
        pdf_path: Optional[Union[str, Path]] = None,
        pdf_url: Optional[str] = None,
    ) -> None:
        """Add an entry to the index.

        Args
        ----
        doi : str
            doi of the entry.
        status : Status
            Status of the entry
        pdf_path : Optional[Union[str, Path]]
            If given path to the PDF
        pdf_url : Optional[str]
            If given URL to the PDF

        Returns
        -------
        None
        """
        if isinstance(status, int):
            status = Status(status)

        self[key] = IndexRow(status, pdf_path, pdf_url)
        with open(self.index_path, "a") as fp:
            self[key].pdf_path = self[key].pdf_path.name
            raw_json = self[key].to_json()
            raw_json["key"] = key
            fp.write(json.dumps(raw_json) + "\n")

    def save_file(self, content: bytes, key: str, pdf_url: str) -> None:
        """Saves a pdf to a specified path and writes the file to the Index.

        Args
        ----
        content : bytes
            Byte content of the requested PDF.

        key : str
            key of the pdf.

        pdf_url : str
            Url of the downloaded PDF.

        Returns
        -------
        None
        """
        name = key

        if not name.endswith(".pdf"):
            name = name + ".pdf"

        download_path = self.download_dir / Path(name)

        open(download_path, "wb").write(content)
        self.add(key, Status.DOWNLOADED, name, pdf_url)
        logger.info(f"Wrote file {name} to `{self.download_dir}/`")

    def overwrite(self, path=None):
        """Overwrites the complete index with the current state."""

        if not path:
            path = self.index_path

        with open(path, "w") as fp:
            for key in self.keys():
                if self[key].pdf_path:
                    self[key].pdf_path = self[key].pdf_path.name
                raw_json = self[key].to_json()
                raw_json["key"] = key
                fp.write(json.dumps(raw_json) + "\n")

    def get_info(self) -> dict:
        """Outputs meta information about the index"""
        return {"index_size": len(self.keys())}

    def get_dl_stats(self) -> dict[str, str]:
        status_list = [self[key].status for key in self.keys()]
        return Counter(status_list).most_common()

    def get_source_stats(self, most_common=20) -> dict:
        return Counter([urllib.parse.urlparse(self[key].pdf_url).netloc for key in self.keys()]).most_common(
            most_common
        )

    def get_rows_by_status(self, status: Status) -> list[IndexRow]:
        return [row for row in self.values() if row.status == status]
