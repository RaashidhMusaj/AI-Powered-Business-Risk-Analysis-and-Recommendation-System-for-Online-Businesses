from uuid import UUID
from typing import Optional
from core.history.exceptions import InvalidProductOwnershipError, HistoryError


class HistoryValidator:
    """
    Validates domain business rules for history and comparison operations.
    """

    @staticmethod
    def validate_product_ownership(product_owner_id: UUID, requesting_user_id: UUID) -> None:
        """
        Ensures the product belongs to the requesting user.
        """
        if str(product_owner_id) != str(requesting_user_id):
            raise InvalidProductOwnershipError()

    @staticmethod
    def validate_comparison_ids(from_id: str, to_id: str) -> None:
        """
        Ensures two distinct analysis IDs are provided for side-by-side comparison.
        """
        if not from_id or not to_id:
            raise HistoryError("Both 'from' and 'to' analysis IDs must be provided for comparison.")
        if from_id == to_id:
            raise HistoryError("Comparison requires two distinct analysis records.")
