class CarouselExtractionError(Exception):
    """Base exception for carousel extraction errors."""
    pass

class CarouselNotFoundError(CarouselExtractionError):
    """Raised when no carousel is found in the HTML."""
    pass

class ListNameNotFoundError(CarouselExtractionError):
    """Raised when the list name cannot be extracted."""
    pass