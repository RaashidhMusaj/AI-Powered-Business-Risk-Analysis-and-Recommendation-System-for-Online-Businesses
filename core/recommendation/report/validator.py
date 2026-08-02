"""
Report Validator Component.
Validates SelectionResult structure before report assembly.
"""

import logging
from core.recommendation.selector.models import SelectionResult
from core.recommendation.report.exceptions import ReportValidationError

logger = logging.getLogger(__name__)


class ReportValidator:
    """
    Validates SelectionResult containers for non-null and non-empty selections.
    """

    def __init__(self):
        logger.info("Initializing ReportValidator component")

    def validate_selection_result(self, selection_result: SelectionResult) -> None:
        """
        Validates that SelectionResult contains valid selected recommendations.
        
        :param selection_result: SelectionResult container to validate.
        :raises ReportValidationError: If SelectionResult is null or contains no recommendations.
        """
        if not selection_result or not isinstance(selection_result, SelectionResult):
            raise ReportValidationError("Invalid or null SelectionResult supplied for report building.")

        if not selection_result.selected or selection_result.recommendation_count == 0:
            raise ReportValidationError("SelectionResult contains no selected recommendations. Cannot build empty report.")

        logger.info(f"SelectionResult validation passed for {selection_result.recommendation_count} recommendations.")
