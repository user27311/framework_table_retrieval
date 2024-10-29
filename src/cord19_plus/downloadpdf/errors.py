class PDFNotAvailableError(Exception):
    """Generic Error for when a PDF could not be found for various reasons."""

    def __init__(self, *args) -> None:
        super().__init__(*args)


class NotInDataBaseError(PDFNotAvailableError):
    """Raised when entry is not available in any db."""

    def __init__(self, *args) -> None:
        super().__init__(*args)


class NotOpenAccessError(PDFNotAvailableError):
    """Raised when PDF could not be found as OpenAccess."""

    def __init__(self, *args) -> None:
        super().__init__(*args)


class RateLimitError(PDFNotAvailableError):
    """Raised when PDF can not be downloaded because of RateLimits."""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class OpenAlexError(Exception):
    """Base class for OpenAlex exceptions"""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class OpenAlexRateLimitError(RateLimitError):
    """Raised when OpenAlex daily access limit is reached."""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class WileyQuoataException(RateLimitError):
    """Raised when too many consecutive requests have been called"""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
