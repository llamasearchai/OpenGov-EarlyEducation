#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Curriculum engine for orchestrating lesson plan and schedule generation.

Coordinates the AI assistant with curriculum design principles,
progressive SEL development, and research-based practices.
"""

import datetime as dt
import textwrap
from typing import Any, Dict, List

from src.core.assistant import AssistantManager
from src.core.database import DatabaseManager
from src.core.models import LessonPlanModel, WeeklyScheduleModel


class CurriculumEngine:
    """
    Enhanced curriculum engine for generating research-based lesson plans and schedules.

    Features:
    - Progressive SEL development across the week
    - Age-appropriate activity sequencing
    - Research-based curriculum design
    - Integration with AI assistant
    """

    def __init__(self, assistant_manager: AssistantManager, db: DatabaseManager) -> None:
        self.assistant_manager = assistant_manager
        self.db = db

    def generate_day_plan(
        self, date: dt.date, age_group: str, theme: str, duration_minutes: int = 360
    ) -> LessonPlanModel:
        """Generate a single day lesson plan."""
        # Get progressive focus for the day
        day_index = (date.weekday() + 1) % 5  # Convert to 0-4 (Mon-Fri)
        sel_focus = self._get_sel_progression(day_index)
        collaboration_focus = self._get_collaboration_progression(day_index)

        # Generate plan using assistant
        plan_data = self._generate_lesson_plan(
            date=date.isoformat(),
            age_group=age_group,
            theme=theme,
            duration_minutes=duration_minutes,
            sel_focus=sel_focus,
            collaboration_focus=collaboration_focus,
        )

        # Validate and return
        plan = LessonPlanModel(**plan_data)
        self.db.upsert_lesson_plan(plan.model_dump())
        return plan

    def generate_weekly_schedule(
        self, week_start: dt.date, age_group: str, weekly_theme: str, duration_minutes: int = 360
    ) -> WeeklyScheduleModel:
        """Generate a complete weekly schedule."""
        if week_start.weekday() != 0:
            raise ValueError("Week start must be a Monday")

        # Generate daily themes
        daily_themes = self._expand_weekly_theme(weekly_theme)

        # Generate daily plans
        daily_plans: Dict[str, LessonPlanModel] = {}
        for day_index in range(5):
            date = week_start + dt.timedelta(days=day_index)
            day_name = ["monday", "tuesday", "wednesday", "thursday", "friday"][day_index]
            daily_theme = daily_themes[day_index]

            plan = self.generate_day_plan(
                date=date, age_group=age_group, theme=daily_theme, duration_minutes=duration_minutes
            )
            daily_plans[f"{day_name}_plan"] = plan

        # Create weekly schedule
        weekly_schedule = WeeklyScheduleModel(
            week_start_date=week_start.isoformat(),
            age_group=age_group,
            weekly_theme=weekly_theme,
            monday_plan=daily_plans["monday_plan"],
            tuesday_plan=daily_plans["tuesday_plan"],
            wednesday_plan=daily_plans["wednesday_plan"],
            thursday_plan=daily_plans["thursday_plan"],
            friday_plan=daily_plans["friday_plan"],
            special_events=self._get_default_events(week_start),
            parent_communication_notes=self._generate_parent_note(weekly_theme, age_group),
            staff_assignments=self._get_staff_assignments(),
        )

        self.db.upsert_weekly_schedule(weekly_schedule.model_dump())
        return weekly_schedule

    def _generate_lesson_plan(
        self,
        date: str,
        age_group: str,
        theme: str,
        duration_minutes: int,
        sel_focus: str,
        collaboration_focus: str,
    ) -> Dict[str, Any]:
        """Generate lesson plan using AI assistant."""
        prompt = self._build_lesson_plan_prompt(
            date, age_group, theme, duration_minutes, sel_focus, collaboration_focus
        )

        result = self.assistant_manager.run_with_tools(prompt)
        return result

    def _build_lesson_plan_prompt(
        self,
        date: str,
        age_group: str,
        theme: str,
        duration_minutes: int,
        sel_focus: str,
        collaboration_focus: str,
    ) -> str:
        """Build comprehensive prompt for lesson plan generation."""
        return textwrap.dedent(
            f"""
        Generate a developmentally appropriate, love/empathy/collaboration-centered LESSON PLAN as a single JSON object only.

        Requirements:
        - Date: {date}
        - Age Group: {age_group}
        - Theme: {theme}
        - Total Duration: {duration_minutes} minutes
        - Social-Emotional Focus: {sel_focus}
        - Collaboration Emphasis: {collaboration_focus}

        Research-based guidelines:
        - Developmentally Appropriate Practice (Copple & Bredekamp, 2009; NAEYC, 2020)
        - Social-Emotional Learning integration (Durlak et al., 2011; CASEL, 2020)
        - Play-based, child-centered learning (Hirsh-Pasek et al., 2009)
        - Constructivist learning with scaffolding (Vygotsky, 1978; Bruner, 1961)
        - Cooperative learning structures (Johnson & Johnson, 1999)
        - Universal Design for Learning (CAST, 2018)
        - Culturally responsive pedagogy (Gay, 2010)
        - Predictable routines and energy-aware sequencing (Ostrosky et al., 2008)

        Schema requirements:
        - Use valid domains: {', '.join([f'"{d}"' for d in ['social_emotional', 'cognitive', 'language', 'literacy', 'mathematics', 'scientific_reasoning', 'physical', 'creative_arts', 'perceptual_motor']])}
        - Use valid learning approaches: {', '.join([f'"{a}"' for a in ['visual', 'auditory', 'kinesthetic', 'tactile', 'multimodal']])}
        - Use valid collaboration types: {', '.join([f'"{c}"' for c in ['peer_tutoring', 'think_pair_share', 'group_investigation', 'jigsaw', 'team_games', 'collaborative_projects']])}
        - Include empathy-building elements and warm transitions
        - Provide inclusive modifications and differentiation strategies
        - Use measurable objectives with Bloom's taxonomy levels
        - Include authentic assessment strategies

        Call the available tools to get daily schedule templates and energy patterns for {age_group} to inform your activity sequencing and timing.

        Return ONLY the JSON object, no explanations or markdown formatting.
        """
        ).strip()

    @staticmethod
    def _get_sel_progression(day_index: int) -> str:
        """Get progressive SEL focus for the day."""
        progression = [
            "self-awareness and emotional recognition",
            "empathy and perspective-taking",
            "relationship skills and cooperation",
            "responsible decision-making",
            "social awareness and community contribution",
        ]
        return progression[day_index % len(progression)]

    @staticmethod
    def _get_collaboration_progression(day_index: int) -> str:
        """Get progressive collaboration focus for the day."""
        progression = [
            "partner turn-taking and shared materials",
            "small-group exploration and shared roles",
            "team problem-solving and consensus building",
            "collaborative creation and peer feedback",
            "whole-class celebration and presentations",
        ]
        return progression[day_index % len(progression)]

    @staticmethod
    def _expand_weekly_theme(weekly_theme: str) -> List[str]:
        """Expand weekly theme into daily themes using inquiry cycle."""
        return [
            f"{weekly_theme}: Wonder and Welcome",
            f"{weekly_theme}: Exploration and Discovery",
            f"{weekly_theme}: Investigation and Questions",
            f"{weekly_theme}: Creation and Sharing",
            f"{weekly_theme}: Reflection and Celebration",
        ]

    @staticmethod
    def _get_default_events(week_start: dt.date) -> Dict[str, str]:
        """Get default special events for the week."""
        return {
            (
                week_start + dt.timedelta(days=2)
            ).isoformat(): "Family story share (bring a favorite picture book).",
            (
                week_start + dt.timedelta(days=4)
            ).isoformat(): "Class kindness celebration and gallery walk.",
        }

    @staticmethod
    def _generate_parent_note(weekly_theme: str, age_group: str) -> str:
        """Generate warm parent communication note."""
        return textwrap.dedent(
            f"""
        This week, our {age_group} class is exploring "{weekly_theme}". We are focusing on empathy, cooperation,
        and caring communication during play and projects. At home, you can support by asking:
        - What kind act did you notice or do today?
        - How did you work with a friend to solve a problem?
        Try these words together: empathy, share, kind, patient, feelings. Thank you for partnering with us.
        """
        ).strip()

    @staticmethod
    def _get_staff_assignments() -> Dict[str, List[str]]:
        """Get default staff assignments."""
        return {
            "lead_teacher": [
                "curriculum implementation",
                "parent communication",
                "assessment and documentation",
            ],
            "assistant_teacher": [
                "material preparation",
                "small group support",
                "transition assistance",
            ],
            "support_staff": [
                "environment setup",
                "individual student support",
                "cleaning and organization",
            ],
        }
