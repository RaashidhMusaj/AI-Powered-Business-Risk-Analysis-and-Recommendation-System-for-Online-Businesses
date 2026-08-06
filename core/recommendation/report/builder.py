"""
Report Builder Public Facade Component.
Exposes lean, single-entrypoint API for report construction.
"""

import logging
from typing import Optional

from core.recommendation.selector.models import SelectionResult
from core.recommendation.templates.manager import TemplateManager
from core.recommendation.report.models import RecommendationReport
from core.recommendation.report.resolver import TemplateResolver
from core.recommendation.report.validator import ReportValidator
from core.recommendation.report.assembler import ReportAssembler

logger = logging.getLogger(__name__)


class ReportBuilder:
    """
    Public facade for the Report Builder component.
    Coordinates validation, template resolution, section rendering, and report assembly.
    Stateless and thread-safe for multi-tenant executions.
    """

    def __init__(
        self,
        template_manager: Optional[TemplateManager] = None,
        assembler: Optional[ReportAssembler] = None,
        validator: Optional[ReportValidator] = None,
        resolver: Optional[TemplateResolver] = None,
    ):
        """
        Initializes ReportBuilder facade with dependency injection.
        """
        logger.info("Initializing ReportBuilder facade instance")
        self.template_manager = template_manager
        self.assembler = assembler or ReportAssembler()
        self.validator = validator or ReportValidator()
        self.resolver = resolver or TemplateResolver()

    def build(self, selection_result: SelectionResult) -> RecommendationReport:
        """
        Transforms a SelectionResult into a complete, structured RecommendationReport.
        Single public entrypoint for the report builder component.
        
        :param selection_result: Validated SelectionResult object.
        :return: Immutable RecommendationReport object.
        :raises ReportValidationError: If SelectionResult is invalid or empty.
        :raises ReportBuildError: If report rendering or assembly fails.
        """
        logger.info("ReportBuilder.build() called")

        self.validator.validate_selection_result(selection_result)

        tm = self.template_manager
        if not tm:
            # Fallback to default initialized TemplateManager
            tm = TemplateManager()
            tm.initialize()

        return self.assembler.assemble(
            selection_result=selection_result,
            template_manager=tm,
            resolver=self.resolver
        )
