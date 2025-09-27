#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report generation module for OpenEarlyEducation.

Provides comprehensive report generation capabilities including
markdown, PDF, and structured data exports.
"""

import textwrap
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from src.core.models import LessonPlanModel, WeeklyScheduleModel

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class ReportBuilder:
    """
    Enhanced report builder with multiple output formats.

    Features:
    - Markdown generation with research citations
    - PDF export with professional formatting
    - JSON exports for data integration
    - Template-based generation
    """

    def __init__(self, templates_dir: Optional[str] = None) -> None:
        self.templates_dir = (
            Path(templates_dir) if templates_dir else Path(__file__).parent / "templates"
        )
        self._ensure_templates()
        self.jinja_env = Environment(loader=FileSystemLoader(self.templates_dir))

    def _ensure_templates(self) -> None:
        """Ensure template directory and files exist."""
        self.templates_dir.mkdir(exist_ok=True)

        # Create lesson plan template
        lesson_template = self.templates_dir / "lesson_plan.md.j2"
        if not lesson_template.exists():
            lesson_template.write_text(self._get_lesson_template())

        # Create weekly schedule template
        weekly_template = self.templates_dir / "weekly_schedule.md.j2"
        if not weekly_template.exists():
            weekly_template.write_text(self._get_weekly_template())

    def _get_lesson_template(self) -> str:
        """Get lesson plan markdown template."""
        return textwrap.dedent(
            """
        # {{ plan.title }}

        **Date:** {{ plan.date }} | **Age Group:** {{ plan.age_group }} | **Theme:** {{ plan.theme }}
        **Duration:** {{ plan.duration_total_minutes }} minutes

        ## Learning Objectives

        {% for objective in plan.objectives %}
        ### {{ objective.domain | replace('_', ' ') | title }} Domain
        - **Objective:** {{ objective.objective_text }}
        - **Measurable Outcome:** {{ objective.measurable_outcome }}
        - **Assessment Method:** {{ objective.assessment_method }}
        - **Bloom's Level:** {{ objective.bloom_level | title }}
        - **Prerequisites:** {{ objective.prerequisite_skills | join(', ') or 'None specified' }}
        {% endfor %}

        ## Materials Needed

        {% for material in plan.materials_needed %}
        - {{ material }}
        {% endfor %}

        ## Key Vocabulary

        {% for word in plan.vocabulary_words %}
        - {{ word }}
        {% endfor %}

        ## Planned Activities

        {% for activity in plan.activities %}
        ### {{ activity.name }}
        **Duration:** {{ activity.duration_minutes }} minutes | **Learning Approach:** {{ activity.learning_approach | title }}
        {% if activity.collaboration_type %} | **Collaboration:** {{ activity.collaboration_type | replace('_', ' ') | title }}{% endif %}

        **Materials:**
        {% for material in activity.materials %}
        - {{ material }}
        {% endfor %}

        **Instructions:**
        {% for instruction in activity.instructions %}
        {{ loop.index }}. {{ instruction }}
        {% endfor %}

        **Differentiation Strategies:**
        {% for strategy, description in activity.differentiation_strategies.items() %}
        - **{{ strategy | title }}:** {{ description }}
        {% endfor %}

        **Safety Considerations:**
        {% for consideration in activity.safety_considerations %}
        - {{ consideration }}
        {% endfor %}

        **Engagement Hooks:**
        {% for hook in activity.engagement_hooks %}
        - {{ hook }}
        {% endfor %}

        **Transition Strategy:** {{ activity.transition_strategy }}

        {% endfor %}

        ## Assessment Strategies

        {% for strategy in plan.assessment_strategies %}
        - {{ strategy }}
        {% endfor %}

        ## Social-Emotional Focus

        {{ plan.social_emotional_focus }}

        ## Empathy-Building Elements

        {% for element in plan.empathy_building_elements %}
        - {{ element }}
        {% endfor %}

        ## Family Engagement Suggestions

        {% for suggestion in plan.family_engagement_suggestions %}
        - {{ suggestion }}
        {% endfor %}

        ## Reflection Questions for Educators

        {% for question in plan.reflection_questions %}
        - {{ question }}
        {% endfor %}

        ## Modifications for Inclusion

        {% for modification, strategy in plan.modifications_for_inclusion.items() %}
        - **{{ modification | title }}:** {{ strategy }}
        {% endfor %}

        ---
        *Generated by OpenEarlyEducation - Research-based early childhood curriculum planning*
        """
        ).strip()

    def _get_weekly_template(self) -> str:
        """Get weekly schedule markdown template."""
        return textwrap.dedent(
            """
        # Weekly Schedule: {{ schedule.weekly_theme }}

        **Week Starting:** {{ schedule.week_start_date }} | **Age Group:** {{ schedule.age_group }}

        ## Monday: {{ schedule.monday_plan.title }}
        **Theme:** {{ schedule.monday_plan.theme }}

        {{ schedule.monday_plan.social_emotional_focus }}

        ## Tuesday: {{ schedule.tuesday_plan.title }}
        **Theme:** {{ schedule.tuesday_plan.theme }}

        {{ schedule.tuesday_plan.social_emotional_focus }}

        ## Wednesday: {{ schedule.wednesday_plan.title }}
        **Theme:** {{ schedule.wednesday_plan.theme }}

        {{ schedule.wednesday_plan.social_emotional_focus }}

        ## Thursday: {{ schedule.thursday_plan.title }}
        **Theme:** {{ schedule.thursday_plan.theme }}

        {{ schedule.thursday_plan.social_emotional_focus }}

        ## Friday: {{ schedule.friday_plan.title }}
        **Theme:** {{ schedule.friday_plan.theme }}

        {{ schedule.friday_plan.social_emotional_focus }}

        ## Special Events

        {% for date, event in schedule.special_events.items() %}
        - **{{ date }}:** {{ event }}
        {% endfor %}

        ## Parent Communication Note

        {{ schedule.parent_communication_notes }}

        ## Staff Assignments

        {% for role, responsibilities in schedule.staff_assignments.items() %}
        ### {{ role | replace('_', ' ') | title }}
        {% for responsibility in responsibilities %}
        - {{ responsibility }}
        {% endfor %}
        {% endfor %}

        ---
        *Generated by OpenEarlyEducation - Research-based early childhood curriculum planning*
        """
        ).strip()

    def generate_lesson_markdown(self, plan: LessonPlanModel) -> str:
        """Generate markdown report for a lesson plan."""
        template = self.jinja_env.get_template("lesson_plan.md.j2")
        return template.render(plan=plan)

    def generate_weekly_markdown(self, schedule: WeeklyScheduleModel) -> str:
        """Generate markdown report for a weekly schedule."""
        template = self.jinja_env.get_template("weekly_schedule.md.j2")
        return template.render(schedule=schedule)

    def generate_lesson_json(self, plan: LessonPlanModel) -> str:
        """Generate JSON representation of a lesson plan."""
        return plan.model_dump_json(indent=2)

    def generate_weekly_json(self, schedule: WeeklyScheduleModel) -> str:
        """Generate JSON representation of a weekly schedule."""
        return schedule.json(indent=2, ensure_ascii=False)

    def export_lesson_pdf(self, plan: LessonPlanModel, output_path: str) -> bool:
        """Export lesson plan to PDF."""
        if not PDF_AVAILABLE:
            return False

        try:
            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                "CustomTitle", parent=styles["Heading1"], fontSize=24, spaceAfter=30
            )

            story = []

            # Title
            story.append(Paragraph(plan.title, title_style))
            story.append(Spacer(1, 0.2 * inch))

            # Header info
            header_text = f"Date: {plan.date} | Age Group: {plan.age_group} | Theme: {plan.theme} | Duration: {plan.duration_total_minutes} minutes"
            story.append(Paragraph(header_text, styles["Normal"]))
            story.append(Spacer(1, 0.3 * inch))

            # Objectives
            story.append(Paragraph("Learning Objectives", styles["Heading2"]))
            for objective in plan.objectives:
                obj_text = f"<b>{objective.domain.replace('_', ' ').title()}</b>: {objective.objective_text}"
                story.append(Paragraph(obj_text, styles["Normal"]))
                story.append(Spacer(1, 0.1 * inch))

            # Activities
            story.append(Paragraph("Activities", styles["Heading2"]))
            for activity in plan.activities:
                story.append(Paragraph(activity.name, styles["Heading3"]))

                # Activity details table
                activity_data = [
                    ["Duration", f"{activity.duration_minutes} minutes"],
                    ["Learning Approach", activity.learning_approach.title()],
                    ["Materials", ", ".join(activity.materials)],
                    [
                        "Instructions",
                        "; ".join(activity.instructions[:2])
                        + ("..." if len(activity.instructions) > 2 else ""),
                    ],
                    ["Transition", activity.transition_strategy],
                ]

                if activity.collaboration_type:
                    activity_data.insert(
                        2, ["Collaboration", activity.collaboration_type.replace("_", " ").title()]
                    )

                table = Table(activity_data)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (0, -1), "#f0f0f0"),
                            ("TEXTCOLOR", (0, 0), (-1, -1), "#000000"),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 10),
                            ("GRID", (0, 0), (-1, -1), 1, "#000000"),
                            ("PADDING", (0, 0), (-1, -1), 6),
                            ("TOPPADDING", (0, 0), (-1, -1), 12),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                        ]
                    )
                )
                story.append(table)
                story.append(Spacer(1, 0.2 * inch))

            # Social-emotional focus
            story.append(Paragraph("Social-Emotional Focus", styles["Heading2"]))
            story.append(Paragraph(plan.social_emotional_focus, styles["Normal"]))
            story.append(Spacer(1, 0.2 * inch))

            # Empathy elements
            story.append(Paragraph("Empathy-Building Elements", styles["Heading2"]))
            for element in plan.empathy_building_elements:
                story.append(Paragraph(f"• {element}", styles["Normal"]))
            story.append(Spacer(1, 0.2 * inch))

            # Family engagement
            story.append(Paragraph("Family Engagement Suggestions", styles["Heading2"]))
            for suggestion in plan.family_engagement_suggestions:
                story.append(Paragraph(f"• {suggestion}", styles["Normal"]))

            doc.build(story)
            return True

        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False

    def export_weekly_pdf(self, schedule: WeeklyScheduleModel, output_path: str) -> bool:
        """Export weekly schedule to PDF."""
        if not PDF_AVAILABLE:
            return False

        try:
            # Generate markdown first (if needed later for different export styles)
            self.generate_weekly_markdown(schedule)

            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=20,
                spaceAfter=20,
                alignment=1,  # Center
            )

            story = []

            # Title
            story.append(Paragraph(f"Weekly Schedule: {schedule.weekly_theme}", title_style))
            story.append(Spacer(1, 0.2 * inch))

            # Header info
            header_text = (
                f"Week Starting: {schedule.week_start_date} | Age Group: {schedule.age_group}"
            )
            story.append(Paragraph(header_text, styles["Normal"]))
            story.append(Spacer(1, 0.3 * inch))

            # Daily plans
            for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
                plan = getattr(schedule, f"{day}_plan")
                story.append(Paragraph(day.title(), styles["Heading2"]))

                day_info = f"<b>{plan.title}</b> - {plan.theme}"
                story.append(Paragraph(day_info, styles["Normal"]))
                story.append(Paragraph(plan.social_emotional_focus, styles["Normal"]))
                story.append(Spacer(1, 0.2 * inch))

            # Special events
            if schedule.special_events:
                story.append(Paragraph("Special Events", styles["Heading2"]))
                for date, event in schedule.special_events.items():
                    event_text = f"<b>{date}:</b> {event}"
                    story.append(Paragraph(event_text, styles["Normal"]))
                story.append(Spacer(1, 0.2 * inch))

            # Parent note
            story.append(Paragraph("Parent Communication Note", styles["Heading2"]))
            story.append(Paragraph(schedule.parent_communication_notes, styles["Normal"]))

            doc.build(story)
            return True

        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False

    def create_custom_template(self, template_name: str, template_content: str) -> None:
        """Create a custom template file."""
        template_file = self.templates_dir / f"{template_name}.md.j2"
        template_file.write_text(template_content)
        # Reload templates
        self.jinja_env = Environment(loader=FileSystemLoader(self.templates_dir))

    def list_available_templates(self) -> list:
        """List all available templates."""
        return [f.stem for f in self.templates_dir.glob("*.j2")]
