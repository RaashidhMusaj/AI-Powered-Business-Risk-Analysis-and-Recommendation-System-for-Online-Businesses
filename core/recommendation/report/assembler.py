"""
Report Assembler Component.
Coordinates section rendering via TemplateManager and compiles RecommendationReport objects.
"""

import logging
from datetime import datetime, timezone
from typing import List

from core.recommendation.selector.models import SelectionResult, SelectedRecommendation
from core.recommendation.templates.manager import TemplateManager
from core.recommendation.templates.exceptions import TemplateError
from core.recommendation.report.models import RecommendationReport
from core.recommendation.report.resolver import TemplateResolver
from core.recommendation.report.exceptions import ReportBuildError

logger = logging.getLogger(__name__)


class ReportAssembler:
    """
    Assembles structured recommendation reports from SelectionResult containers.
    Stateless and thread-safe.
    """

    def __init__(self):
        logger.info("Initializing ReportAssembler component")

    def assemble(
        self,
        selection_result: SelectionResult,
        template_manager: TemplateManager,
        resolver: TemplateResolver,
    ) -> RecommendationReport:
        """
        Assembles a RecommendationReport by coordinating template rendering for all sections.
        
        :param selection_result: Validated SelectionResult object.
        :param template_manager: Initialized TemplateManager facade.
        :param resolver: TemplateResolver instance.
        :return: Immutable RecommendationReport.
        """
        logger.info("Starting report assembly process...")

        try:
            # 1. Primary aspect for summary lookup
            first_item: SelectedRecommendation = selection_result.selected[0]
            primary_aspect = first_item.aspect

            # 2. Render Summary Section
            summary_tmpl_id = resolver.resolve_summary(
                highest_priority=selection_result.highest_priority,
                aspect=primary_aspect
            )
            summary_text = template_manager.render_summary(
                template_id=summary_tmpl_id,
                values={"aspect": primary_aspect.capitalize()}
            )

            # 3. Render Insights Section (preserving selector candidate order)
            insights_list: List[str] = []
            seen_insights = set()

            for item in selection_result.selected:
                insight_tmpl_id = resolver.resolve_insight(aspect=item.aspect, risk_level=item.risk_level)
                try:
                    tmpl_insight = template_manager.render_insight(template_id=insight_tmpl_id, values={})
                    if tmpl_insight not in seen_insights:
                        seen_insights.add(tmpl_insight)
                        insights_list.append(tmpl_insight)
                except TemplateError:
                    # Fallback to rule description if template lookup fails
                    if item.rule.description and item.rule.description not in seen_insights:
                        seen_insights.add(item.rule.description)
                        insights_list.append(item.rule.description)

            # 4. Render Actions Section (preserving selector candidate order)
            actions_list: List[str] = []
            seen_actions = set()

            for item in selection_result.selected:
                action_tmpl_id = resolver.resolve_action(aspect=item.aspect, risk_level=item.risk_level)
                try:
                    tmpl_action = template_manager.render_action(
                        template_id=action_tmpl_id,
                        values={"aspect": item.aspect.capitalize()}
                    )
                    if tmpl_action not in seen_actions:
                        seen_actions.add(tmpl_action)
                        actions_list.append(tmpl_action)
                except TemplateError:
                    pass

                # Append rule's specific action bullet points
                for act in item.rule.actions:
                    if act not in seen_actions:
                        seen_actions.add(act)
                        actions_list.append(act)

            # 5. Timestamp and Immutable Report Construction
            generated_at = datetime.now(timezone.utc)

            report = RecommendationReport(
                summary=summary_text,
                insights=tuple(insights_list),
                actions=tuple(actions_list),
                highest_priority=selection_result.highest_priority,
                recommendation_count=selection_result.recommendation_count,
                generated_at=generated_at
            )

            logger.info(f"Report assembly completed successfully. Generated report at {generated_at.isoformat()}")
            return report

        except Exception as ex:
            if isinstance(ex, ReportBuildError):
                raise ex
            raise ReportBuildError(f"Failed to assemble recommendation report: {str(ex)}")
