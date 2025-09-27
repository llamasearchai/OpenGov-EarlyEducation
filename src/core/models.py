#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pydantic models for OpenEarlyEducation.

Defines all data models with comprehensive validation,
research-based constraints, and detailed documentation.
"""

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional

from dateutil.parser import isoparse
from pydantic import BaseModel, Field, field_validator, model_validator


class DevelopmentalDomain(str, Enum):
    """Developmental domains aligned with Head Start ELOF."""

    social_emotional = "social_emotional"
    cognitive = "cognitive"
    language = "language"
    literacy = "literacy"
    mathematics = "mathematics"
    scientific_reasoning = "scientific_reasoning"
    physical = "physical"
    creative_arts = "creative_arts"
    perceptual_motor = "perceptual_motor"

    @classmethod
    def all(cls) -> List[str]:
        """Get all developmental domains."""
        return [e.value for e in cls]


class LearningApproach(str, Enum):
    """Learning approaches aligned with multiple intelligences and UDL."""

    visual = "visual"
    auditory = "auditory"
    kinesthetic = "kinesthetic"
    tactile = "tactile"
    multimodal = "multimodal"

    @classmethod
    def all(cls) -> List[str]:
        """Get all learning approaches."""
        return [e.value for e in cls]


class CollaborationType(str, Enum):
    """Types of collaborative learning structures."""

    peer_tutoring = "peer_tutoring"
    think_pair_share = "think_pair_share"
    group_investigation = "group_investigation"
    jigsaw = "jigsaw"
    team_games = "team_games"
    collaborative_projects = "collaborative_projects"

    @classmethod
    def all(cls) -> List[str]:
        """Get all collaboration types."""
        return [e.value for e in cls]


class LearningObjectiveModel(BaseModel):
    """Model for learning objectives with research-based validation."""

    domain: DevelopmentalDomain = Field(
        ..., description="Developmental domain aligned with Head Start ELOF."
    )
    objective_text: str = Field(
        ..., description="Objective phrased with measurable action verb (Bloom)."
    )
    measurable_outcome: str = Field(..., description="Observable outcome criteria.")
    assessment_method: str = Field(
        ..., description="Assessment approach (anecdotal note, checklist, work sample)."
    )
    bloom_level: str = Field(
        ...,
        description="Bloom's Taxonomy level (remember, understand, apply, analyze, evaluate, create).",
    )
    age_group: str = Field(..., description="Age band such as '2-3', '3-4', '4-5'.")
    prerequisite_skills: List[str] = Field(
        default_factory=list, description="Skills that should be in place before this objective."
    )

    @field_validator("bloom_level")
    def validate_bloom_level(cls, v: str) -> str:
        """Validate Bloom's taxonomy level."""
        valid_levels = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
        if v.lower() not in valid_levels:
            raise ValueError(f"Bloom level must be one of {valid_levels}")
        return v.lower()

    @field_validator("age_group")
    def validate_age_group(cls, v: str) -> str:
        """Validate age group format."""
        if v not in ["2-3", "3-4", "4-5"]:
            raise ValueError("Age group must be '2-3', '3-4', or '4-5'")
        return v


class ActivityModel(BaseModel):
    """Model for individual activities with comprehensive validation."""

    name: str = Field(..., description="Activity name")
    duration_minutes: int = Field(..., ge=1, le=120, description="Duration in minutes")
    materials: List[str] = Field(..., description="Required materials")
    instructions: List[str] = Field(..., description="Step-by-step instructions")
    learning_approach: LearningApproach = Field(..., description="Primary learning approach")
    collaboration_type: Optional[CollaborationType] = Field(
        None, description="Type of collaboration if applicable"
    )
    differentiation_strategies: Dict[str, str] = Field(
        ..., description="Strategies for different learners"
    )
    safety_considerations: List[str] = Field(..., description="Safety and supervision notes")
    engagement_hooks: List[str] = Field(..., description="Ways to engage children")
    transition_strategy: str = Field(..., description="How to transition to/from this activity")

    @field_validator("learning_approach")
    def validate_learning_approach(cls, v: str) -> str:
        """Validate learning approach."""
        if v not in LearningApproach.all():
            raise ValueError(f"Learning approach must be one of {LearningApproach.all()}")
        return v

    @field_validator("collaboration_type")
    def validate_collaboration_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate collaboration type."""
        if v and v not in CollaborationType.all():
            raise ValueError(f"Collaboration type must be one of {CollaborationType.all()}")
        return v

    @field_validator("instructions")
    def validate_instructions(cls, v: List[str]) -> List[str]:
        """Validate instructions are provided."""
        if not v or len(v) == 0:
            raise ValueError("At least one instruction must be provided")
        return v

    @field_validator("materials")
    def validate_materials(cls, v: List[str]) -> List[str]:
        """Validate materials are provided."""
        if not v or len(v) == 0:
            raise ValueError("At least one material must be specified")
        return v


class LessonPlanModel(BaseModel):
    """Complete lesson plan model with comprehensive validation."""

    title: str = Field(..., description="Lesson plan title")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    age_group: str = Field(..., description="Age group")
    theme: str = Field(..., description="Lesson theme")
    duration_total_minutes: int = Field(..., ge=30, le=480, description="Total duration in minutes")
    objectives: List[LearningObjectiveModel] = Field(..., description="Learning objectives")
    materials_needed: List[str] = Field(..., description="All materials needed for the lesson")
    vocabulary_words: List[str] = Field(..., description="Key vocabulary to introduce")
    activities: List[ActivityModel] = Field(..., description="Planned activities")
    assessment_strategies: List[str] = Field(..., description="Assessment methods")
    family_engagement_suggestions: List[str] = Field(
        ..., description="Suggestions for family involvement"
    )
    modifications_for_inclusion: Dict[str, str] = Field(..., description="Inclusive modifications")
    social_emotional_focus: str = Field(..., description="SEL focus area")
    empathy_building_elements: List[str] = Field(..., description="Empathy-building activities")
    reflection_questions: List[str] = Field(..., description="Reflection questions for educators")

    @field_validator("date")
    def validate_date(cls, v: str) -> str:
        """Validate date format and ensure it's not in the past."""
        try:
            parsed_date = isoparse(v).date()
            # Enforce not in the past for application usage; tests rely on future dates where applicable
            if parsed_date < date.today():
                raise ValueError("Date cannot be in the past")
            return v
        except Exception as e:
            raise ValueError("Date must be in ISO format YYYY-MM-DD") from e

    @field_validator("age_group")
    def validate_lesson_age_group(cls, v: str) -> str:
        """Validate age group."""
        if v not in ["2-3", "3-4", "4-5"]:
            raise ValueError("Age group must be '2-3', '3-4', or '4-5'")
        return v

    @model_validator(mode="after")
    def validate_total_duration(self) -> "LessonPlanModel":
        """Validate that activity durations sum to total duration."""
        total_activity_time = sum(activity.duration_minutes for activity in (self.activities or []))
        if total_activity_time > self.duration_total_minutes * 1.2:
            raise ValueError("Total activity time cannot exceed 120% of total duration")
        return self

    @model_validator(mode="after")
    def validate_age_consistency(self) -> "LessonPlanModel":
        """Validate that all objectives match the age group."""
        for objective in self.objectives or []:
            if objective.age_group != self.age_group:
                raise ValueError("All objectives must match the lesson plan age group")
        return self


class WeeklyScheduleModel(BaseModel):
    """Model for weekly schedules."""

    week_start_date: str = Field(..., description="Week start date (Monday)")
    age_group: str = Field(..., description="Age group")
    weekly_theme: str = Field(..., description="Overall weekly theme")
    monday_plan: LessonPlanModel = Field(..., description="Monday lesson plan")
    tuesday_plan: LessonPlanModel = Field(..., description="Tuesday lesson plan")
    wednesday_plan: LessonPlanModel = Field(..., description="Wednesday lesson plan")
    thursday_plan: LessonPlanModel = Field(..., description="Thursday lesson plan")
    friday_plan: LessonPlanModel = Field(..., description="Friday lesson plan")
    special_events: Dict[str, str] = Field(
        default_factory=dict, description="Special events during the week"
    )
    parent_communication_notes: str = Field(..., description="Notes for parent communication")
    staff_assignments: Dict[str, List[str]] = Field(
        default_factory=dict, description="Staff assignments and responsibilities"
    )

    @field_validator("week_start_date")
    def validate_week_start_date(cls, v: str) -> str:
        """Validate that week starts on Monday."""
        try:
            parsed_date = isoparse(v).date()
            if parsed_date.weekday() != 0:  # Monday = 0
                raise ValueError("Week start date must be a Monday")
            return v
        except Exception as e:
            raise ValueError("Week start date must be ISO format YYYY-MM-DD and be a Monday") from e

    @field_validator("age_group")
    def validate_weekly_age_group(cls, v: str) -> str:
        """Validate age group."""
        if v not in ["2-3", "3-4", "4-5"]:
            raise ValueError("Age group must be '2-3', '3-4', or '4-5'")
        return v

    @model_validator(mode="after")
    def validate_weekly_consistency(self) -> "WeeklyScheduleModel":
        """Validate that all daily plans match the weekly age group and theme."""
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            plan = getattr(self, f"{day}_plan", None)
            if plan:
                if plan.age_group != self.age_group:
                    raise ValueError(
                        f"All daily plans must match the weekly age group: {self.age_group}"
                    )
                if self.weekly_theme not in plan.theme:
                    raise ValueError(
                        f"Daily theme should relate to weekly theme: {self.weekly_theme}"
                    )
        return self


# Request/Response models for API
class LessonPlanRequest(BaseModel):
    """Request model for lesson plan generation."""

    date: str
    age_group: str
    theme: str
    duration_minutes: int = 360
    social_emotional_focus: Optional[str] = None
    collaboration_emphasis: Optional[str] = None


class WeeklyScheduleRequest(BaseModel):
    """Request model for weekly schedule generation."""

    week_start_date: str
    age_group: str
    weekly_theme: str
    duration_minutes: int = 360


class AssessmentRecordRequest(BaseModel):
    """Request model for recording assessments."""

    child_id: str
    date: str
    domain: DevelopmentalDomain
    observation: str
    next_steps: Optional[str] = ""


class ProgressReportRequest(BaseModel):
    """Request model for progress reports."""

    child_id: str
    start_date: str
    end_date: str


# Response models
class APIResponse(BaseModel):
    """Generic API response model."""

    success: bool
    message: str
    data: Optional[Any] = None


class LessonPlanResponse(APIResponse):
    """Response model for lesson plans."""

    data: Optional[LessonPlanModel] = None


class WeeklyScheduleResponse(APIResponse):
    """Response model for weekly schedules."""

    data: Optional[WeeklyScheduleModel] = None


class AssessmentResponse(APIResponse):
    """Response model for assessments."""

    pass


class ProgressReportResponse(APIResponse):
    """Response model for progress reports."""

    data: Optional[Dict[str, Any]] = None
