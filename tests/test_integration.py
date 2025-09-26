#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration tests for OpenEarlyEducation.

Tests the interaction between different components and end-to-end functionality.
"""

import os
import tempfile
from datetime import date, timedelta
from unittest.mock import Mock, patch

import pytest

from src.core.assistant import AssistantManager
from src.core.config import Config
from src.core.database import DatabaseManager
from src.core.engine import CurriculumEngine
from src.core.models import LessonPlanModel, WeeklyScheduleModel


class TestCurriculumEngineIntegration:
    """Test integration between curriculum engine and other components."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        return Config(openai_api_key="test_key", openai_model="gpt-4o", database_path=":memory:")

    @pytest.fixture
    def db_manager(self):
        """Create database manager with in-memory database."""
        return DatabaseManager(":memory:")

    @pytest.fixture
    def mock_assistant(self, mock_config, db_manager):
        """Create mock assistant manager."""
        with patch("src.core.assistant.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            # Mock assistant creation
            mock_assistant = Mock()
            mock_assistant.id = "test_assistant_id"
            mock_client.beta.assistants.create.return_value = mock_assistant

            # Mock thread and run operations
            mock_thread = Mock()
            mock_thread.id = "test_thread_id"
            mock_client.beta.threads.create.return_value = mock_thread

            mock_run = Mock()
            mock_run.id = "test_run_id"
            mock_run.status = "completed"
            mock_client.beta.threads.runs.create.return_value = mock_run
            mock_client.beta.threads.runs.retrieve.return_value = mock_run

            # Mock message retrieval
            mock_message = Mock()
            mock_message.role = "assistant"
            mock_message.content = [Mock()]
            mock_message.content[0].text.value = (
                '{"title": "Test Plan", "date": "2024-12-25", "age_group": "3-4", "theme": "Test Theme", "duration_total_minutes": 360, "objectives": [], "materials_needed": ["test"], "vocabulary_words": ["test"], "activities": [], "assessment_strategies": ["test"], "family_engagement_suggestions": ["test"], "modifications_for_inclusion": {}, "social_emotional_focus": "test", "empathy_building_elements": ["test"], "reflection_questions": ["test"]}'
            )
            mock_client.beta.threads.messages.list.return_value = Mock(data=[mock_message])

            return AssistantManager(mock_config, db_manager)

    def test_curriculum_engine_creation(self, mock_assistant, db_manager):
        """Test curriculum engine creation."""
        engine = CurriculumEngine(mock_assistant, db_manager)
        assert engine.assistant_manager == mock_assistant
        assert engine.db == db_manager

    def test_generate_day_plan_integration(self, mock_assistant, db_manager):
        """Test generating a day plan with mocked AI."""
        engine = CurriculumEngine(mock_assistant, db_manager)

        future_date = date.today() + timedelta(days=7)

        # This would normally call the AI, but we've mocked it
        with patch.object(engine.assistant_manager, "run_with_tools") as mock_run:
            mock_run.return_value = {
                "title": "Test Lesson Plan",
                "date": future_date.isoformat(),
                "age_group": "3-4",
                "theme": "Test Theme",
                "duration_total_minutes": 360,
                "objectives": [],
                "materials_needed": ["test"],
                "vocabulary_words": ["test"],
                "activities": [],
                "assessment_strategies": ["test"],
                "family_engagement_suggestions": ["test"],
                "modifications_for_inclusion": {},
                "social_emotional_focus": "test",
                "empathy_building_elements": ["test"],
                "reflection_questions": ["test"],
            }

            plan = engine.generate_day_plan(future_date, "3-4", "Test Theme")

            assert isinstance(plan, LessonPlanModel)
            assert plan.title == "Test Lesson Plan"
            assert plan.age_group == "3-4"

    def test_sel_progression(self):
        """Test SEL progression logic."""
        # Test the static method
        progression_0 = CurriculumEngine._get_sel_progression(0)
        progression_1 = CurriculumEngine._get_sel_progression(1)

        assert progression_0 != progression_1  # Different days should have different focuses
        assert "awareness" in progression_0.lower()
        assert "empathy" in progression_1.lower()

    def test_collaboration_progression(self):
        """Test collaboration progression logic."""
        progression_0 = CurriculumEngine._get_collaboration_progression(0)
        progression_1 = CurriculumEngine._get_collaboration_progression(1)

        assert progression_0 != progression_1
        assert "turn-taking" in progression_0.lower()
        assert "exploration" in progression_1.lower()

    def test_expand_weekly_theme(self):
        """Test weekly theme expansion."""
        theme = "Community Helpers"
        expanded = CurriculumEngine._expand_weekly_theme(theme)

        assert len(expanded) == 5
        assert "Community Helpers" in expanded[0]
        assert "Wonder" in expanded[0]
        assert "Exploration" in expanded[1]
        assert "Investigation" in expanded[2]
        assert "Creation" in expanded[3]
        assert "Reflection" in expanded[4]


class TestAssessmentIntegration:
    """Test assessment functionality integration."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        yield db_path

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def db_manager(self, temp_db):
        """Create database manager."""
        return DatabaseManager(temp_db)

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        return Config(openai_api_key="test_key")

    def test_assessment_recording_and_retrieval(self, db_manager, mock_config):
        """Test recording and retrieving assessments."""
        from src.core.assessment import AssessmentService

        with patch("src.core.assessment.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            # Mock AI response for report generation
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = (
                '{"summary": "Test summary", "recommendations": ["Test rec"]}'
            )
            mock_client.chat.completions.create.return_value = mock_response

            service = AssessmentService(db_manager, mock_config.openai_client)

            # Record assessment
            service.record_observation(
                child_id="child123",
                date="2024-12-25",
                domain="social_emotional",
                observation="Child shared toys with peers",
                next_steps="Encourage more sharing opportunities",
            )

            # Retrieve assessments
            assessments = db_manager.get_assessments("child123", "2024-01-01", "2025-12-31")

            assert len(assessments) == 1
            assert assessments[0]["child_id"] == "child123"
            assert assessments[0]["domain"] == "social_emotional"
            assert assessments[0]["observation"] == "Child shared toys with peers"

    def test_progress_report_generation(self, db_manager, mock_config):
        """Test progress report generation."""
        from src.core.assessment import AssessmentService

        with patch("src.core.assessment.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            # Mock AI response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[
                0
            ].message.content = """{
                "summary": "Child shows good social-emotional development",
                "celebrations": ["Excellent sharing skills", "Good cooperation"],
                "next_steps": ["Continue encouraging social interactions"],
                "recommendations": ["Regular observation", "Family communication"]
            }"""
            mock_client.chat.completions.create.return_value = mock_response

            service = AssessmentService(db_manager, mock_config.openai_client)

            # Record some observations
            service.record_observation("child123", "2024-12-20", "social_emotional", "Shared toys")
            service.record_observation("child123", "2024-12-21", "cognitive", "Solved puzzle")

            # Generate report
            report = service.generate_progress_report("child123", "2024-12-01", "2024-12-31")

            assert report["success"] is True
            assert "data" in report
            assert "narrative_report" in report["data"]
            assert "summary" in report["data"]["narrative_report"]


class TestReportGenerationIntegration:
    """Test report generation integration."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        return Config(openai_api_key="test_key")

    def test_lesson_plan_markdown_generation(self, mock_config):
        """Test lesson plan markdown generation."""
        # Create test lesson plan
        from datetime import date, timedelta

        from src.core.reports import ReportBuilder

        future_date = (date.today() + timedelta(days=7)).isoformat()
        plan = LessonPlanModel(
            title="Test Lesson Plan",
            date=future_date,
            age_group="3-4",
            theme="Test Theme",
            duration_total_minutes=360,
            objectives=[],
            materials_needed=["test materials"],
            vocabulary_words=["test", "vocabulary"],
            activities=[],
            assessment_strategies=["observation"],
            family_engagement_suggestions=["read together"],
            modifications_for_inclusion={"mobility": "provide support"},
            social_emotional_focus="building relationships",
            empathy_building_elements=["sharing activities"],
            reflection_questions=["What went well?"],
        )

        builder = ReportBuilder()
        markdown = builder.generate_lesson_markdown(plan)

        assert "Test Lesson Plan" in markdown
        # Date should reflect the future_date used
        assert future_date in markdown
        assert "3-4" in markdown
        assert "test materials" in markdown
        # The markdown lists vocabulary words individually; check for entries
        assert "test" in markdown
        assert "vocabulary" in markdown

    def test_lesson_plan_json_generation(self, mock_config):
        """Test lesson plan JSON generation."""
        from datetime import date, timedelta

        from src.core.reports import ReportBuilder

        future_date = (date.today() + timedelta(days=7)).isoformat()
        plan = LessonPlanModel(
            title="Test Plan",
            date=future_date,
            age_group="3-4",
            theme="Test Theme",
            duration_total_minutes=360,
            objectives=[],
            materials_needed=[],
            vocabulary_words=[],
            activities=[],
            assessment_strategies=[],
            family_engagement_suggestions=[],
            modifications_for_inclusion={},
            social_emotional_focus="test",
            empathy_building_elements=[],
            reflection_questions=[],
        )

        builder = ReportBuilder()
        json_str = builder.generate_lesson_json(plan)

        import json

        parsed = json.loads(json_str)

        assert parsed["title"] == "Test Plan"
        assert parsed["age_group"] == "3-4"
        assert parsed["duration_total_minutes"] == 360


class TestConfigurationIntegration:
    """Test configuration integration."""

    def test_config_from_environment(self):
        """Test loading configuration from environment variables."""
        import os

        from src.core.config import get_config

        # Set test environment variables
        test_env = {
            "OPENAI_API_KEY": "test_key_123",
            "OPENAI_MODEL": "gpt-4o",
            "DATABASE_PATH": "/tmp/test.db",
            "LOG_LEVEL": "DEBUG",
        }

        with patch.dict(os.environ, test_env):
            config = get_config()

            assert config.openai_api_key == "test_key_123"
            assert config.openai_model == "gpt-4o"
            assert config.database_path == "/tmp/test.db"
            assert config.log_level == "DEBUG"

    def test_config_file_loading(self):
        """Test loading configuration from file."""
        import json
        import tempfile

        from src.core.config import get_config

        config_data = {
            "openai_model": "gpt-4",
            "database_path": "/tmp/config_test.db",
            "log_level": "INFO",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            config = get_config(config_file)

            assert config.openai_model == "gpt-4"
            assert config.database_path == "/tmp/config_test.db"
            assert config.log_level == "INFO"

        finally:
            os.unlink(config_file)
