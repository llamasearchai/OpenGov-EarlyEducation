#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced assistant manager for OpenAI Assistants API integration.

Provides robust interaction with OpenAI Assistants with retry logic,
error handling, and comprehensive tool definitions.
"""

import json
import logging
import os
import textwrap
import time
from pathlib import Path
from typing import Any, Dict, List

from openai import OpenAI

from src.core.config import Config
from src.core.database import DatabaseManager

logger = logging.getLogger(__name__)


class AssistantManager:
    """
    Enhanced manager for OpenAI Assistant "OpenEarlyEducation".

    Features:
    - Robust error handling and retry logic
    - Comprehensive tool definitions
    - Assistant caching and reuse
    - Enhanced system instructions
    """

    def __init__(self, config: Config, db: DatabaseManager) -> None:
        self.config = config
        self.db = db
        # Instantiate OpenAI client here so tests can patch src.core.assistant.OpenAI
        self.client = OpenAI(api_key=self.config.openai_api_key)
        # Offline mode allows local operation without network (for tests/TUI demos)
        offline_flag = os.getenv("OPENAI_OFFLINE", "").lower() in ("1", "true", "yes")
        self.offline = offline_flag or self.config.openai_api_key in ("dummy", "test_key", "")
        self.assistant_id = self._ensure_assistant()

    def _ensure_assistant(self) -> str:
        """Create or retrieve assistant with caching."""
        if self.offline:
            logger.info("Assistant running in offline mode")
            return "offline"
        cache_file = Path(self.config.assistant_cache_path)

        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                assistant_id = data.get("assistant_id")
                if assistant_id and self._validate_assistant(assistant_id):
                    logger.info(f"Using cached assistant: {assistant_id}")
                    return str(assistant_id)
            except Exception as e:
                logger.warning(f"Error loading assistant cache: {e}")

        # Create new assistant
        logger.info("Creating new assistant")
        return self._create_assistant(cache_file)

    def _validate_assistant(self, assistant_id: str) -> bool:
        """Validate that assistant exists and is accessible."""
        try:
            self.client.beta.assistants.retrieve(assistant_id)
            return True
        except Exception:
            return False

    def _create_assistant(self, cache_file: Path) -> str:
        """Create a new assistant."""
        system_instructions = self._get_system_instructions()
        tools = self._get_tool_definitions()

        for attempt in range(self.config.max_retries):
            try:
                assistant = self.client.beta.assistants.create(
                    name="OpenEarlyEducation",
                    description="Research-based early childhood curriculum and schedule generator focusing on love, empathy, and collaboration.",
                    model=self.config.openai_model,
                    instructions=system_instructions,
                    tools=tools,  # type: ignore[arg-type]
                )

                # Cache the assistant ID
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(
                    json.dumps({"assistant_id": assistant.id}, indent=2), encoding="utf-8"
                )

                logger.info(f"Created assistant: {assistant.id}")
                return str(assistant.id)

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed to create assistant: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (2**attempt))

        raise RuntimeError("Failed to create assistant after all retries")

    def _get_system_instructions(self) -> str:
        """Get comprehensive system instructions for the assistant."""
        return textwrap.dedent(
            """
        You are OpenEarlyEducation, an expert early childhood education assistant that designs daily and weekly plans
        centered on love, empathy, collaboration, inclusion, and developmentally appropriate practice.

        Foundational principles to uphold:
        - Nurturing and secure relationships that foster emotional safety (Bowlby, 1969).
        - Developmentally Appropriate Practice per NAEYC (Copple & Bredekamp, 2009; NAEYC, 2020).
        - Play-based, child-centered learning (Hirsh-Pasek et al., 2009).
        - Constructivist learning with scaffolds and ZPD (Vygotsky, 1978; Bruner, 1961).
        - Cooperative learning structures and prosocial development (Johnson & Johnson, 1999; Eisenberg & Mussen, 1989).
        - SEL integration across routines (Durlak et al., 2011; CASEL, 2020).
        - Universal Design for Learning and inclusive design (CAST, 2018).
        - Culturally responsive pedagogy (Gay, 2010; Ladson-Billings, 1995).
        - Predictable routines that support regulation (Ostrosky et al., 2008).
        - Attention/energy sequencing (Ruff & Rothbart, 1996; Borbély, 1982).
        - Authentic, strengths-based assessment and family partnership (Bagnato et al., 2010; NAEYC, 2020).

        Output requirements:
        - Return only valid JSON objects for programmatic tasks.
        - Conform exactly to provided schema specifications.
        - Use measurable verbs and observable outcomes.
        - Embed empathy-building and collaboration opportunities.
        - Ensure warm, responsive transitions and safety considerations.
        - Use people-first and strengths-based language.
        - Offer multiple means of engagement, representation, and expression (UDL).

        Safety guidelines:
        - No medical, diagnostic, or legal claims.
        - Suggest referrals to appropriate professionals when needed.
        - Prioritize child safety and inclusion in all activities.
        """
        )

    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get comprehensive tool definitions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_daily_schedule_template",
                    "description": "Return a developmentally appropriate daily routine template for the given age group.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "age_group": {
                                "type": "string",
                                "enum": ["2-3", "3-4", "4-5"],
                                "description": "Age band for the template.",
                            }
                        },
                        "required": ["age_group"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_energy_pattern",
                    "description": "Return an hourly energy/attention pattern for the given age group.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "age_group": {
                                "type": "string",
                                "enum": ["2-3", "3-4", "4-5"],
                                "description": "Age band for the energy pattern.",
                            }
                        },
                        "required": ["age_group"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "save_lesson_plan_to_db",
                    "description": "Persist a generated lesson plan JSON to database.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lesson_plan": {
                                "type": "object",
                                "description": "Complete lesson plan following the required schema.",
                                "properties": {
                                    "title": {"type": "string"},
                                    "date": {"type": "string", "format": "date"},
                                    "age_group": {"type": "string", "enum": ["2-3", "3-4", "4-5"]},
                                    "theme": {"type": "string"},
                                    "duration_total_minutes": {
                                        "type": "integer",
                                        "minimum": 30,
                                        "maximum": 480,
                                    },
                                    "objectives": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "domain": {
                                                    "type": "string",
                                                    "enum": [
                                                        "social_emotional",
                                                        "cognitive",
                                                        "language",
                                                        "literacy",
                                                        "mathematics",
                                                        "scientific_reasoning",
                                                        "physical",
                                                        "creative_arts",
                                                        "perceptual_motor",
                                                    ],
                                                },
                                                "objective_text": {"type": "string"},
                                                "measurable_outcome": {"type": "string"},
                                                "assessment_method": {"type": "string"},
                                                "bloom_level": {"type": "string"},
                                                "age_group": {"type": "string"},
                                                "prerequisite_skills": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                },
                                            },
                                            "required": [
                                                "domain",
                                                "objective_text",
                                                "measurable_outcome",
                                                "assessment_method",
                                                "bloom_level",
                                                "age_group",
                                            ],
                                        },
                                    },
                                    "materials_needed": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "vocabulary_words": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "activities": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "duration_minutes": {
                                                    "type": "integer",
                                                    "minimum": 1,
                                                    "maximum": 120,
                                                },
                                                "materials": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                },
                                                "instructions": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                },
                                                "learning_approach": {
                                                    "type": "string",
                                                    "enum": [
                                                        "visual",
                                                        "auditory",
                                                        "kinesthetic",
                                                        "tactile",
                                                        "multimodal",
                                                    ],
                                                },
                                                "collaboration_type": {
                                                    "type": "string",
                                                    "enum": [
                                                        "peer_tutoring",
                                                        "think_pair_share",
                                                        "group_investigation",
                                                        "jigsaw",
                                                        "team_games",
                                                        "collaborative_projects",
                                                    ],
                                                },
                                                "differentiation_strategies": {
                                                    "type": "object",
                                                    "additionalProperties": {"type": "string"},
                                                },
                                                "safety_considerations": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                },
                                                "engagement_hooks": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                },
                                                "transition_strategy": {"type": "string"},
                                            },
                                            "required": [
                                                "name",
                                                "duration_minutes",
                                                "materials",
                                                "instructions",
                                                "learning_approach",
                                                "differentiation_strategies",
                                                "safety_considerations",
                                                "engagement_hooks",
                                                "transition_strategy",
                                            ],
                                        },
                                    },
                                    "assessment_strategies": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "family_engagement_suggestions": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "modifications_for_inclusion": {
                                        "type": "object",
                                        "additionalProperties": {"type": "string"},
                                    },
                                    "social_emotional_focus": {"type": "string"},
                                    "empathy_building_elements": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "reflection_questions": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                                "required": [
                                    "title",
                                    "date",
                                    "age_group",
                                    "theme",
                                    "duration_total_minutes",
                                    "objectives",
                                    "materials_needed",
                                    "vocabulary_words",
                                    "activities",
                                    "assessment_strategies",
                                    "family_engagement_suggestions",
                                    "modifications_for_inclusion",
                                    "social_emotional_focus",
                                    "empathy_building_elements",
                                    "reflection_questions",
                                ],
                                "additionalProperties": False,
                            }
                        },
                        "required": ["lesson_plan"],
                        "additionalProperties": False,
                    },
                },
            },
        ]

    def run_with_tools(self, user_instructions: str) -> Dict[str, Any]:
        """Run assistant with tool support and retry logic."""
        if self.offline:
            return self._offline_generate_default_plan(user_instructions)
        thread = None
        run = None

        try:
            # Create thread
            thread = self.client.beta.threads.create()
            logger.debug(f"Created thread: {thread.id}")

            # Add message
            self.client.beta.threads.messages.create(
                thread_id=thread.id, role="user", content=user_instructions
            )

            # Create run
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id, assistant_id=self.assistant_id
            )

            # Poll for completion
            return self._poll_run_completion(thread.id, run.id)

        except Exception as e:
            logger.error(f"Error in run_with_tools: {e}")
            raise
        finally:
            # Cleanup
            if thread and run:
                try:
                    self.client.beta.threads.runs.cancel(thread_id=thread.id, run_id=run.id)
                except Exception:
                    pass

    def _offline_generate_default_plan(self, user_instructions: str) -> Dict[str, Any]:
        """Return a deterministic, valid lesson plan JSON in offline mode."""
        # Minimal, valid plan focusing on empathy and collaboration
        today = time.strftime("%Y-%m-%d")
        plan: Dict[str, Any] = {
            "title": "Empathy and Collaboration Offline Demo",
            "date": today,
            "age_group": "3-4",
            "theme": "Caring Community",
            "duration_total_minutes": 360,
            "objectives": [],
            "materials_needed": ["picture books", "blocks", "paper", "crayons"],
            "vocabulary_words": ["empathy", "share", "kind"],
            "activities": [],
            "assessment_strategies": ["anecdotal notes"],
            "family_engagement_suggestions": ["Talk about kind acts at home"],
            "modifications_for_inclusion": {"visual_supports": "Use picture cues for transitions"},
            "social_emotional_focus": "building caring relationships",
            "empathy_building_elements": ["role-play helping a friend"],
            "reflection_questions": ["How did children show care today?"],
        }
        return plan

    def _poll_run_completion(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Poll for run completion with retry logic."""
        for attempt in range(self.config.max_retries * 10):  # Max polling attempts
            try:
                run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)

                if run.status in ("queued", "in_progress"):
                    time.sleep(self.config.retry_delay)
                    continue

                if run.status == "requires_action":
                    return self._handle_tool_calls(thread_id, run_id, run)

                if run.status == "completed":
                    return self._get_assistant_response(thread_id)

                # Error states
                raise RuntimeError(f"Run ended with status: {run.status}")

            except Exception as e:
                logger.warning(f"Polling attempt {attempt + 1} failed: {e}")
                if attempt >= self.config.max_retries * 10 - 1:
                    raise RuntimeError(f"Run polling failed after {attempt + 1} attempts") from e
                time.sleep(self.config.retry_delay * (2 ** min(attempt, 5)))  # Exponential backoff

        raise RuntimeError("Run polling timed out")

    def _handle_tool_calls(self, thread_id: str, run_id: str, run: Any) -> Dict[str, Any]:
        """Handle required tool calls."""
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        tool_outputs = []

        for call in tool_calls:
            try:
                result = self._execute_tool_call(call)
                tool_outputs.append(
                    {"tool_call_id": call.id, "output": json.dumps(result, ensure_ascii=False)}
                )
            except Exception as e:
                logger.error(f"Error executing tool call {call.function.name}: {e}")
                tool_outputs.append(
                    {
                        "tool_call_id": call.id,
                        "output": json.dumps({"error": str(e)}, ensure_ascii=False),
                    }
                )

        # Submit tool outputs
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id, run_id=run_id, tool_outputs=tool_outputs  # type: ignore[arg-type]
        )

        # Continue polling
        return self._poll_run_completion(thread_id, run_id)

    def _execute_tool_call(self, tool_call: Any) -> Any:
        """Execute a single tool call."""
        name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments or "{}")

        tool_methods: Dict[str, Any] = {
            "get_daily_schedule_template": self._get_daily_schedule_template,
            "get_energy_pattern": self._get_energy_pattern,
            "save_lesson_plan_to_db": self._save_lesson_plan_to_db,
        }

        if name not in tool_methods:
            raise ValueError(f"Unknown tool: {name}")

        func = tool_methods[name]
        return func(**arguments)

    def _get_daily_schedule_template(self, age_group: str) -> Dict[str, Any]:
        """Get daily schedule template for age group."""
        templates = {
            "2-3": [
                {"block": "arrival", "minutes": 30, "type": "transition"},
                {"block": "morning_circle", "minutes": 15, "type": "whole_group"},
                {"block": "centers_play", "minutes": 45, "type": "small_group"},
                {"block": "snack", "minutes": 20, "type": "social"},
                {"block": "outdoor_play", "minutes": 45, "type": "gross_motor"},
                {"block": "lunch", "minutes": 25, "type": "social"},
                {"block": "rest_quiet", "minutes": 120, "type": "quiet"},
                {"block": "snack_pm", "minutes": 20, "type": "social"},
                {"block": "project_time", "minutes": 45, "type": "collaborative"},
                {"block": "closing_circle", "minutes": 15, "type": "whole_group"},
            ],
            "3-4": [
                {"block": "arrival", "minutes": 30, "type": "transition"},
                {"block": "morning_circle", "minutes": 20, "type": "whole_group"},
                {"block": "centers_play", "minutes": 60, "type": "small_group"},
                {"block": "snack", "minutes": 20, "type": "social"},
                {"block": "outdoor_play", "minutes": 60, "type": "gross_motor"},
                {"block": "lunch", "minutes": 30, "type": "social"},
                {"block": "rest_quiet", "minutes": 90, "type": "quiet"},
                {"block": "snack_pm", "minutes": 20, "type": "social"},
                {"block": "project_time", "minutes": 60, "type": "collaborative"},
                {"block": "closing_circle", "minutes": 20, "type": "whole_group"},
            ],
            "4-5": [
                {"block": "arrival", "minutes": 30, "type": "transition"},
                {"block": "morning_circle", "minutes": 25, "type": "whole_group"},
                {"block": "centers_play", "minutes": 70, "type": "small_group"},
                {"block": "snack", "minutes": 20, "type": "social"},
                {"block": "outdoor_play", "minutes": 60, "type": "gross_motor"},
                {"block": "lunch", "minutes": 30, "type": "social"},
                {"block": "rest_quiet", "minutes": 75, "type": "quiet"},
                {"block": "snack_pm", "minutes": 20, "type": "social"},
                {"block": "project_time", "minutes": 70, "type": "collaborative"},
                {"block": "closing_circle", "minutes": 25, "type": "whole_group"},
            ],
        }

        return {"age_group": age_group, "template": templates.get(age_group, templates["3-4"])}

    def _get_energy_pattern(self, age_group: str) -> Dict[str, Any]:
        """Get energy pattern for age group."""
        patterns = {
            "2-3": [0.7, 0.85, 0.8, 0.55, 0.5, 0.45, 0.7, 0.75, 0.6],
            "3-4": [0.8, 0.9, 0.85, 0.6, 0.55, 0.5, 0.75, 0.8, 0.65],
            "4-5": [0.85, 0.95, 0.9, 0.65, 0.6, 0.55, 0.8, 0.85, 0.7],
        }

        return {"age_group": age_group, "energy": patterns.get(age_group, patterns["3-4"])}

    def _save_lesson_plan_to_db(self, lesson_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Save lesson plan to database."""
        try:
            plan_id = self.db.upsert_lesson_plan(lesson_plan)
            return {"status": "success", "plan_id": plan_id}
        except Exception as e:
            logger.error(f"Error saving lesson plan: {e}")
            return {"status": "error", "message": str(e)}

    def _get_assistant_response(self, thread_id: str) -> Dict[str, Any]:
        """Get the final assistant response."""
        messages = self.client.beta.threads.messages.list(
            thread_id=thread_id, order="desc", limit=5
        )

        for message in messages.data:
            if message.role == "assistant":
                content = message.content[0].text.value if message.content else ""  # type: ignore[union-attr]
                if content.strip():
                    try:
                        return self._extract_json_from_text(content)
                    except Exception as e:
                        logger.warning(f"Failed to parse assistant response as JSON: {e}")
                        return {"error": "Invalid JSON response", "raw_content": content}

        raise RuntimeError("No valid assistant response found")

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response."""
        text = text.strip()

        # Remove code fences
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:].strip()

        # Find JSON object
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("No JSON object found in response")

        json_str = text[start : end + 1]
        from typing import cast
        return cast(Dict[str, Any], json.loads(json_str))
