class HistoryError(Exception):
    """Base history domain exception."""
    pass


class HistoryNotFoundError(HistoryError):
    """Raised when an analysis history record is not found."""
    def __init__(self, message: str = "Analysis history record not found"):
        super().__init__(message)


class ProductNotFoundError(HistoryError):
    """Raised when a product is not found."""
    def __init__(self, message: str = "Product not found"):
        super().__init__(message)


class InvalidProductOwnershipError(HistoryError):
    """Raised when a user attempts to access a product they do not own."""
    def __init__(self, message: str = "Access denied: product does not belong to user"):
        super().__init__(message)
