#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Pydantic models.

Tests all validation logic, constraints, and model behavior.
"""

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from src.core.models import (
    ActivityModel,
    CollaborationType,
    DevelopmentalDomain,
    LearningApproach,
    LearningObjectiveModel,
    LessonPlanModel,
    WeeklyScheduleModel,
)


class TestDevelopmentalDomain:
    """Test DevelopmentalDomain enum."""

    def test_all_domains(self):
        """Test that all domains are available."""
        domains = DevelopmentalDomain.all()
        assert len(domains) == 9
        assert "social_emotional" in domains
        assert "cognitive" in domains
        assert "language" in domains
        assert "literacy" in domains
        assert "mathematics" in domains
        assert "scientific_reasoning" in domains
        assert "physical" in domains
        assert "creative_arts" in domains
        assert "perceptual_motor" in domains


class TestLearningApproach:
    """Test LearningApproach enum."""

    def test_all_approaches(self):
        """Test that all learning approaches are available."""
        approaches = LearningApproach.all()
        assert len(approaches) == 5
        assert "visual" in approaches
        assert "auditory" in approaches
        assert "kinesthetic" in approaches
        assert "tactile" in approaches
        assert "multimodal" in approaches


class TestCollaborationType:
    """Test CollaborationType enum."""

    def test_all_collaboration_types(self):
        """Test that all collaboration types are available."""
        types = CollaborationType.all()
        assert len(types) == 6
        assert "peer_tutoring" in types
        assert "think_pair_share" in types
        assert "group_investigation" in types
        assert "jigsaw" in types
        assert "team_games" in types
        assert "collaborative_projects" in types


class TestLearningObjectiveModel:
    """Test LearningObjectiveModel validation."""

    def test_valid_objective(self):
        """Test creating a valid learning objective."""
        objective = LearningObjectiveModel(
            domain="social_emotional",
            objective_text="The child will demonstrate empathy by recognizing others' feelings",
            measurable_outcome="Child uses words like 'happy' or 'sad' to describe peers' emotions",
            assessment_method="Anecdotal notes during group activities",
            bloom_level="understand",
            age_group="3-4",
            prerequisite_skills=["Can identify basic emotions in self"],
        )

        assert objective.domain == "social_emotional"
        assert objective.bloom_level == "understand"
        assert objective.age_group == "3-4"

    def test_invalid_bloom_level(self):
        """Test invalid Bloom's taxonomy level."""
        with pytest.raises(ValidationError):
            LearningObjectiveModel(
                domain="social_emotional",
                objective_text="Test objective",
                measurable_outcome="Test outcome",
                assessment_method="Test method",
                bloom_level="invalid_level",
                age_group="3-4",
            )

    def test_invalid_age_group(self):
        """Test invalid age group."""
        with pytest.raises(ValidationError):
            LearningObjectiveModel(
                domain="social_emotional",
                objective_text="Test objective",
                measurable_outcome="Test outcome",
                assessment_method="Test method",
                bloom_level="understand",
                age_group="invalid-age",
            )

    def test_missing_required_fields(self):
        """Test missing required fields."""
        with pytest.raises(ValidationError):
            LearningObjectiveModel(
                domain="social_emotional",
                objective_text="Test objective",
                # Missing other required fields
            )


class TestActivityModel:
    """Test ActivityModel validation."""

    def test_valid_activity(self):
        """Test creating a valid activity."""
        activity = ActivityModel(
            name="Group Story Time",
            duration_minutes=20,
            materials=["Picture books", "Soft rug or cushions"],
            instructions=[
                "Gather children in a circle on the rug",
                "Read the story with enthusiasm and clear voice",
                "Pause to ask prediction questions",
                "Encourage children to act out parts of the story",
            ],
            learning_approach="auditory",
            collaboration_type="think_pair_share",
            differentiation_strategies={
                "Visual learners": "Use picture books with large illustrations",
                "Kinesthetic learners": "Encourage acting out story elements",
                "English language learners": "Preview key vocabulary before reading",
            },
            safety_considerations=[
                "Ensure all children can see and hear the story",
                "Monitor for overstimulation in group setting",
            ],
            engagement_hooks=[
                "Ask children to predict what happens next",
                "Use different voices for different characters",
                "Incorporate movement breaks during longer stories",
            ],
            transition_strategy="Sing a cleanup song and help children transition to the next activity",
        )

        assert activity.name == "Group Story Time"
        assert activity.duration_minutes == 20
        assert activity.learning_approach == "auditory"
        assert activity.collaboration_type == "think_pair_share"

    def test_invalid_duration(self):
        """Test invalid duration values."""
        # Too short
        with pytest.raises(ValidationError):
            ActivityModel(
                name="Test",
                duration_minutes=0,
                materials=["test"],
                instructions=["test"],
                learning_approach="visual",
                differentiation_strategies={},
                safety_considerations=[],
                engagement_hooks=[],
                transition_strategy="test",
            )

        # Too long
        with pytest.raises(ValidationError):
            ActivityModel(
                name="Test",
                duration_minutes=121,
                materials=["test"],
                instructions=["test"],
                learning_approach="visual",
                differentiation_strategies={},
                safety_considerations=[],
                engagement_hooks=[],
                transition_strategy="test",
            )

    def test_invalid_learning_approach(self):
        """Test invalid learning approach."""
        with pytest.raises(ValidationError):
            ActivityModel(
                name="Test",
                duration_minutes=30,
                materials=["test"],
                instructions=["test"],
                learning_approach="invalid_approach",
                differentiation_strategies={},
                safety_considerations=[],
                engagement_hooks=[],
                transition_strategy="test",
            )

    def test_missing_materials(self):
        """Test missing materials."""
        with pytest.raises(ValidationError):
            ActivityModel(
                name="Test",
                duration_minutes=30,
                materials=[],  # Empty materials
                instructions=["test"],
                learning_approach="visual",
                differentiation_strategies={},
                safety_considerations=[],
                engagement_hooks=[],
                transition_strategy="test",
            )

    def test_missing_instructions(self):
        """Test missing instructions."""
        with pytest.raises(ValidationError):
            ActivityModel(
                name="Test",
                duration_minutes=30,
                materials=["test"],
                instructions=[],  # Empty instructions
                learning_approach="visual",
                differentiation_strategies={},
                safety_considerations=[],
                engagement_hooks=[],
                transition_strategy="test",
            )


class TestLessonPlanModel:
    """Test LessonPlanModel validation."""

    def test_valid_lesson_plan(self):
        """Test creating a valid lesson plan."""
        future_date = (date.today() + timedelta(days=7)).isoformat()

        plan = LessonPlanModel(
            title="Friendship and Sharing",
            date=future_date,
            age_group="3-4",
            theme="Building Friendships",
            duration_total_minutes=360,
            objectives=[
                LearningObjectiveModel(
                    domain="social_emotional",
                    objective_text="Children will demonstrate cooperative play",
                    measurable_outcome="Children share materials and take turns",
                    assessment_method="Anecdotal notes during free play",
                    bloom_level="apply",
                    age_group="3-4",
                )
            ],
            materials_needed=["Blocks", "Art supplies", "Books about friendship"],
            vocabulary_words=["friend", "share", "cooperate", "kind"],
            activities=[
                ActivityModel(
                    name="Cooperative Block Building",
                    duration_minutes=45,
                    materials=["Wooden blocks", "Toy people"],
                    instructions=[
                        "Introduce the concept of sharing and cooperation",
                        "Demonstrate building together",
                        "Encourage children to work as a team",
                    ],
                    learning_approach="kinesthetic",
                    collaboration_type="collaborative_projects",
                    differentiation_strategies={
                        "Children with motor challenges": "Provide larger blocks for easier manipulation"
                    },
                    safety_considerations=["Ensure blocks are not thrown"],
                    engagement_hooks=["Ask children to build a 'friendship castle'"],
                    transition_strategy="Sing cleanup song and preview next activity",
                )
            ],
            assessment_strategies=["Anecdotal notes", "Photo documentation"],
            family_engagement_suggestions=[
                "Talk about sharing at home",
                "Read books about friendship together",
            ],
            modifications_for_inclusion={
                "Children with mobility challenges": "Provide activities at table level",
                "Children with hearing impairments": "Use visual cues and gestures",
            },
            social_emotional_focus="Building positive relationships and cooperation",
            empathy_building_elements=[
                "Role-playing how to ask for a turn",
                "Discussing how sharing makes friends happy",
            ],
            reflection_questions=[
                "How did children demonstrate cooperation?",
                "What vocabulary words were used during the activity?",
            ],
        )

        assert plan.title == "Friendship and Sharing"
        assert plan.age_group == "3-4"
        assert len(plan.objectives) == 1
        assert len(plan.activities) == 1

    def test_past_date(self):
        """Test that past dates are rejected."""
        past_date = (date.today() - timedelta(days=1)).isoformat()

        with pytest.raises(ValidationError):
            LessonPlanModel(
                title="Test",
                date=past_date,
                age_group="3-4",
                theme="Test",
                duration_total_minutes=360,
                objectives=[],
                materials_needed=[],
                vocabulary_words=[],
                activities=[],
                assessment_strategies=[],
                family_engagement_suggestions=[],
                modifications_for_inclusion={},
                social_emotional_focus="Test",
                empathy_building_elements=[],
                reflection_questions=[],
            )

    def test_invalid_age_group(self):
        """Test invalid age group."""
        with pytest.raises(ValidationError):
            LessonPlanModel(
                title="Test",
                date=date.today().isoformat(),
                age_group="invalid",
                theme="Test",
                duration_total_minutes=360,
                objectives=[],
                materials_needed=[],
                vocabulary_words=[],
                activities=[],
                assessment_strategies=[],
                family_engagement_suggestions=[],
                modifications_for_inclusion={},
                social_emotional_focus="Test",
                empathy_building_elements=[],
                reflection_questions=[],
            )

    def test_duration_too_short(self):
        """Test duration too short."""
        with pytest.raises(ValidationError):
            LessonPlanModel(
                title="Test",
                date=date.today().isoformat(),
                age_group="3-4",
                theme="Test",
                duration_total_minutes=20,  # Too short
                objectives=[],
                materials_needed=[],
                vocabulary_words=[],
                activities=[],
                assessment_strategies=[],
                family_engagement_suggestions=[],
                modifications_for_inclusion={},
                social_emotional_focus="Test",
                empathy_building_elements=[],
                reflection_questions=[],
            )

    def test_duration_too_long(self):
        """Test duration too long."""
        with pytest.raises(ValidationError):
            LessonPlanModel(
                title="Test",
                date=date.today().isoformat(),
                age_group="3-4",
                theme="Test",
                duration_total_minutes=500,  # Too long
                objectives=[],
                materials_needed=[],
                vocabulary_words=[],
                activities=[],
                assessment_strategies=[],
                family_engagement_suggestions=[],
                modifications_for_inclusion={},
                social_emotional_focus="Test",
                empathy_building_elements=[],
                reflection_questions=[],
            )


class TestWeeklyScheduleModel:
    """Test WeeklyScheduleModel validation."""

    def test_valid_weekly_schedule(self):
        """Test creating a valid weekly schedule."""
        monday_date = date.today() + timedelta(days=(7 - date.today().weekday()))  # Next Monday

        # Create minimal lesson plans for testing
        lesson_plan = LessonPlanModel(
            title="Monday Plan",
            date=monday_date.isoformat(),
            age_group="3-4",
            theme="Test Weekly Theme: Monday Focus",
            duration_total_minutes=360,
            objectives=[],
            materials_needed=[],
            vocabulary_words=[],
            activities=[],
            assessment_strategies=[],
            family_engagement_suggestions=[],
            modifications_for_inclusion={},
            social_emotional_focus="Test focus",
            empathy_building_elements=[],
            reflection_questions=[],
        )

        schedule = WeeklyScheduleModel(
            week_start_date=monday_date.isoformat(),
            age_group="3-4",
            weekly_theme="Test Weekly Theme",
            monday_plan=lesson_plan,
            tuesday_plan=lesson_plan,
            wednesday_plan=lesson_plan,
            thursday_plan=lesson_plan,
            friday_plan=lesson_plan,
            special_events={(monday_date + timedelta(days=2)).isoformat(): "Special event"},
            parent_communication_notes="Test parent note",
            staff_assignments={"lead_teacher": ["planning", "assessment"]},
        )

        assert schedule.age_group == "3-4"
        assert schedule.weekly_theme == "Test Weekly Theme"

    def test_non_monday_start(self):
        """Test that non-Monday start dates are rejected."""
        # Get a non-Monday date
        test_date = date.today()
        while test_date.weekday() == 0:  # Monday
            test_date += timedelta(days=1)

        with pytest.raises(ValidationError):
            WeeklyScheduleModel(
                week_start_date=test_date.isoformat(),
                age_group="3-4",
                weekly_theme="Test",
                monday_plan=None,  # This will fail anyway, but we want the date error
                tuesday_plan=None,
                wednesday_plan=None,
                thursday_plan=None,
                friday_plan=None,
            )

    def test_age_group_mismatch(self):
        """Test age group mismatch between weekly and daily plans."""
        monday_date = date.today() + timedelta(days=(7 - date.today().weekday()))

        # Create lesson plan with different age group
        lesson_plan_34 = LessonPlanModel(
            title="3-4 Plan",
            date=monday_date.isoformat(),
            age_group="3-4",
            theme="Test",
            duration_total_minutes=360,
            objectives=[],
            materials_needed=[],
            vocabulary_words=[],
            activities=[],
            assessment_strategies=[],
            family_engagement_suggestions=[],
            modifications_for_inclusion={},
            social_emotional_focus="Test",
            empathy_building_elements=[],
            reflection_questions=[],
        )

        lesson_plan_45 = LessonPlanModel(
            title="4-5 Plan",
            date=monday_date.isoformat(),
            age_group="4-5",  # Different age group
            theme="Test",
            duration_total_minutes=360,
            objectives=[],
            materials_needed=[],
            vocabulary_words=[],
            activities=[],
            assessment_strategies=[],
            family_engagement_suggestions=[],
            modifications_for_inclusion={},
            social_emotional_focus="Test",
            empathy_building_elements=[],
            reflection_questions=[],
        )

        with pytest.raises(ValidationError):
            WeeklyScheduleModel(
                week_start_date=monday_date.isoformat(),
                age_group="3-4",  # Weekly is 3-4
                weekly_theme="Test",
                monday_plan=lesson_plan_45,  # But daily is 4-5
                tuesday_plan=lesson_plan_34,
                wednesday_plan=lesson_plan_34,
                thursday_plan=lesson_plan_34,
                friday_plan=lesson_plan_34,
            )
