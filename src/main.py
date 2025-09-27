#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenEarlyEducation: A complete, research-backed early childhood lesson planning and weekly scheduling system
that uses the OpenAI Assistants (Agents) SDK with function tools, robust validation, and persistent storage.

This is the enhanced version with:
- Beautiful Terminal User Interface (TUI)
- Comprehensive testing and validation
- FastAPI endpoints for web access
- Docker support
- Enhanced error handling and logging
- Configuration management

Pedagogical foundations (selected references):
- Developmentally Appropriate Practice (DAP): Copple & Bredekamp (2009); NAEYC (2020).
- Social-Emotional Learning (SEL): Durlak et al. (2011); CASEL (2020).
- Attachment and nurturing care: Bowlby (1969).
- Constructivism & ZPD: Bruner (1961); Vygotsky (1978).
- Cooperative learning: Johnson & Johnson (1999).
- Play-based learning: Hirsh-Pasek et al. (2009).
- Universal Design for Learning (UDL): CAST (2018).
- Cultural responsiveness: Gay (2010); Ladson-Billings (1995).
- Authentic assessment: Bagnato, Neisworth, & Pretti-Frontczak (2010).
- Routines and schedules: Ostrosky et al. (2008).
- Energy/attention patterns: Ruff & Rothbart (1996); Borbély (1982).

Environment:
- Python 3.10+
- OPENAI_API_KEY must be set in environment.

Install:
    pip install -r requirements.txt

Run examples:
    python -m src.main tui
    python -m src.main api
    python -m src.main week --age-group 4-5 --start-date 2025-09-29 --theme "Community and Belonging"
    python -m src.main day --age-group 3-4 --date 2025-10-01 --theme "Empathy in Our Classroom"
    python -m src.main assess --child-id A12 --domain social_emotional --observation "Comforted a peer during cleanup transition."
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.api.app import FastAPIApp
from src.core.assessment import AssessmentService
from src.core.assistant import AssistantManager
from src.core.config import Config, get_config
from src.core.database import DatabaseManager
from src.core.engine import CurriculumEngine
from src.core.reports import ReportBuilder
from src.tui.app import TUIApp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("open_early_education.log")],
)
logger = logging.getLogger(__name__)


class OpenEarlyEducationApp:
    """Main application class for OpenEarlyEducation."""

    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or get_config()
        self.db = DatabaseManager(self.config.database_path)
        self.assistant_manager = AssistantManager(self.config, self.db)
        self.engine = CurriculumEngine(self.assistant_manager, self.db)
        self.reports = ReportBuilder()
        self.assess = AssessmentService(self.db, self.config.openai_client)

    def run_tui(self) -> None:
        """Run the terminal user interface."""
        app = TUIApp(self)
        app.run()

    def run_api(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Run the FastAPI server."""
        app = FastAPIApp(self)
        import uvicorn

        logger.info(f"Starting FastAPI server on {host}:{port}")
        uvicorn.run(app.app, host=host, port=port)

    def generate_day_plan(
        self, date: dt.date, age_group: str, theme: str, duration_minutes: int = 360
    ) -> Dict[str, Any]:
        """Generate a single day lesson plan."""
        try:
            plan = self.engine.generate_day(date, age_group, theme, duration_minutes)
            return {"status": "success", "data": plan.dict()}
        except Exception as e:
            logger.error(f"Error generating day plan: {e}")
            return {"status": "error", "message": str(e)}

    def generate_weekly_schedule(
        self, week_start: dt.date, age_group: str, weekly_theme: str, duration_minutes: int = 360
    ) -> Dict[str, Any]:
        """Generate a weekly schedule."""
        try:
            schedule = self.engine.generate_week(
                week_start, age_group, weekly_theme, duration_minutes
            )
            return {"status": "success", "data": schedule.dict()}
        except Exception as e:
            logger.error(f"Error generating weekly schedule: {e}")
            return {"status": "error", "message": str(e)}

    def record_assessment(
        self, child_id: str, date: str, domain: str, observation: str, next_steps: str = ""
    ) -> Dict[str, Any]:
        """Record an assessment observation."""
        try:
            self.assess.record(child_id, date, domain, observation, next_steps)
            return {"status": "success", "message": "Assessment recorded successfully"}
        except Exception as e:
            logger.error(f"Error recording assessment: {e}")
            return {"status": "error", "message": str(e)}

    def generate_progress_report(self, child_id: str, start: str, end: str) -> Dict[str, Any]:
        """Generate a progress report."""
        try:
            report = self.assess.progress_report(child_id, start, end)
            return {"status": "success", "data": report}
        except Exception as e:
            logger.error(f"Error generating progress report: {e}")
            return {"status": "error", "message": str(e)}

    def list_lesson_plans(self, limit: int = 25) -> Dict[str, Any]:
        """List stored lesson plans."""
        try:
            cur = self.db.conn.cursor()
            cur.execute(
                "SELECT plan_id, date, age_group, theme FROM lesson_plans ORDER BY date DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
            plans = [dict(row) for row in rows]
            return {"status": "success", "data": plans}
        except Exception as e:
            logger.error(f"Error listing lesson plans: {e}")
            return {"status": "error", "message": str(e)}

    def list_weekly_schedules(self, limit: int = 25) -> Dict[str, Any]:
        """List stored weekly schedules."""
        try:
            cur = self.db.conn.cursor()
            cur.execute(
                "SELECT schedule_id, week_start_date, age_group, weekly_theme FROM weekly_schedules ORDER BY week_start_date DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
            schedules = [dict(row) for row in rows]
            return {"status": "success", "data": schedules}
        except Exception as e:
            logger.error(f"Error listing weekly schedules: {e}")
            return {"status": "error", "message": str(e)}


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="OpenEarlyEducation",
        description="Research-based ECE lesson and schedule generator with TUI and API support.",
    )

    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # TUI command
    subparsers.add_parser("tui", help="Launch terminal user interface")

    # API command
    api_parser = subparsers.add_parser("api", help="Start FastAPI server")
    api_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    api_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")

    # Day plan command
    day_parser = subparsers.add_parser("day", help="Generate a single day lesson plan")
    day_parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    day_parser.add_argument("--age-group", required=True, choices=["2-3", "3-4", "4-5"])
    day_parser.add_argument("--theme", required=True)
    day_parser.add_argument("--duration", type=int, default=360)
    day_parser.add_argument("--output", help="Output file path")

    # Week schedule command
    week_parser = subparsers.add_parser("week", help="Generate a weekly schedule (Mon start)")
    week_parser.add_argument("--start-date", required=True, help="YYYY-MM-DD (Monday)")
    week_parser.add_argument("--age-group", required=True, choices=["2-3", "3-4", "4-5"])
    week_parser.add_argument("--theme", required=True)
    week_parser.add_argument("--duration", type=int, default=360)
    week_parser.add_argument("--output", help="Output file path")

    # Assessment command
    assess_parser = subparsers.add_parser("assess", help="Record an assessment observation")
    assess_parser.add_argument("--child-id", required=True)
    assess_parser.add_argument(
        "--domain",
        required=True,
        choices=[
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
    )
    assess_parser.add_argument("--observation", required=True)
    assess_parser.add_argument("--next-steps", default="")
    assess_parser.add_argument("--date", default=dt.date.today().isoformat())

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate a progress report JSON")
    report_parser.add_argument("--child-id", required=True)
    report_parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    report_parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    report_parser.add_argument("--output", help="Output JSON file")

    # List command
    list_parser = subparsers.add_parser("list", help="List stored plans or schedules")
    list_parser.add_argument("--type", required=True, choices=["lessons", "weekly"])
    list_parser.add_argument("--limit", type=int, default=25)

    args = parser.parse_args()

    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Load configuration
    config = get_config(args.config) if args.config else get_config()

    # Create and run app
    app = OpenEarlyEducationApp(config)

    try:
        if args.command == "tui":
            app.run_tui()
        elif args.command == "api":
            app.run_api(args.host, args.port)
        elif args.command == "day":
            result = app.generate_day_plan(
                dt.date.fromisoformat(args.date), args.age_group, args.theme, args.duration
            )
            if result["status"] == "success":
                plan_data = result["data"]
                if args.output:
                    with open(args.output, "w", encoding="utf-8") as f:
                        json.dump(plan_data, f, indent=2, ensure_ascii=False)
                    print(f"Lesson plan saved to {args.output}")
                else:
                    print(json.dumps(plan_data, indent=2, ensure_ascii=False))
            else:
                print(f"Error: {result['message']}", file=sys.stderr)
                sys.exit(1)
        elif args.command == "week":
            result = app.generate_weekly_schedule(
                dt.date.fromisoformat(args.start_date), args.age_group, args.theme, args.duration
            )
            if result["status"] == "success":
                schedule_data = result["data"]
                if args.output:
                    with open(args.output, "w", encoding="utf-8") as f:
                        json.dump(schedule_data, f, indent=2, ensure_ascii=False)
                    print(f"Weekly schedule saved to {args.output}")
                else:
                    print(json.dumps(schedule_data, indent=2, ensure_ascii=False))
            else:
                print(f"Error: {result['message']}", file=sys.stderr)
                sys.exit(1)
        elif args.command == "assess":
            result = app.record_assessment(
                args.child_id, args.date, args.domain, args.observation, args.next_steps
            )
            if result["status"] == "success":
                print(result["message"])
            else:
                print(f"Error: {result['message']}", file=sys.stderr)
                sys.exit(1)
        elif args.command == "report":
            result = app.generate_progress_report(args.child_id, args.start, args.end)
            if result["status"] == "success":
                report_data = result["data"]
                if args.output:
                    with open(args.output, "w", encoding="utf-8") as f:
                        json.dump(report_data, f, indent=2, ensure_ascii=False)
                    print(f"Progress report saved to {args.output}")
                else:
                    print(json.dumps(report_data, indent=2, ensure_ascii=False))
            else:
                print(f"Error: {result['message']}", file=sys.stderr)
                sys.exit(1)
        elif args.command == "list":
            if args.type == "lessons":
                result = app.list_lesson_plans(args.limit)
            else:
                result = app.list_weekly_schedules(args.limit)

            if result["status"] == "success":
                for item in result["data"]:
                    print(
                        f"{item['plan_id' if args.type == 'lessons' else 'schedule_id']} | "
                        f"{item['date' if args.type == 'lessons' else 'week_start_date']} | "
                        f"{item['age_group']} | {item['theme' if args.type == 'lessons' else 'weekly_theme']}"
                    )
            else:
                print(f"Error: {result['message']}", file=sys.stderr)
                sys.exit(1)
        else:
            parser.print_help()
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
