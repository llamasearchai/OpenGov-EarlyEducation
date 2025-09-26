#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI application for OpenEarlyEducation web API.

Provides REST API endpoints for lesson planning, assessment management,
and report generation with comprehensive documentation.
"""

from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.core.models import (
    AssessmentRecordRequest,
    AssessmentResponse,
    LessonPlanRequest,
    LessonPlanResponse,
    ProgressReportRequest,
    ProgressReportResponse,
    WeeklyScheduleRequest,
    WeeklyScheduleResponse,
)
from src.core.reports import ReportBuilder

# No direct BaseModel usage needed here


class FastAPIApp:
    """FastAPI application for OpenEarlyEducation."""

    def __init__(self, core_app) -> None:
        self.core_app = core_app
        self.app = FastAPI(
            title="OpenEarlyEducation API",
            description="Research-based early childhood curriculum planning API",
            version="2.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Mount static files
        self.app.mount("/static", StaticFiles(directory="static"), name="static")

        # Include routers
        self._include_routers()

        # Add health check endpoint
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "version": "2.0.0"}

    def _include_routers(self) -> None:
        """Include all API routers."""

        # Lesson Plans Router
        @self.app.post("/lesson-plans", response_model=LessonPlanResponse)
        async def generate_lesson_plan(request: LessonPlanRequest):
            """Generate a lesson plan."""
            try:
                result = self.core_app.generate_day_plan(
                    date.fromisoformat(request.date),
                    request.age_group,
                    request.theme,
                    request.duration_minutes,
                )

                if result["status"] == "success":
                    return LessonPlanResponse(success=True, data=result["data"])
                else:
                    raise HTTPException(status_code=400, detail=result["message"])

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/lesson-plans", response_model=List[Dict[str, Any]])
        async def list_lesson_plans(
            age_group: Optional[str] = Query(None),
            theme: Optional[str] = Query(None),
            start_date: Optional[str] = Query(None),
            end_date: Optional[str] = Query(None),
        ):
            """List lesson plans with optional filters."""
            try:
                # This would need to be implemented in the core app
                # For now, return from database
                result = self.core_app.db.search_lesson_plans(
                    age_group, theme, start_date, end_date
                )
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/lesson-plans/{plan_id}", response_model=LessonPlanResponse)
        async def get_lesson_plan(plan_id: str):
            """Get a specific lesson plan."""
            try:
                plan_data = self.core_app.db.get_lesson_plan(plan_id)
                if plan_data:
                    return LessonPlanResponse(success=True, data=plan_data)
                else:
                    raise HTTPException(status_code=404, detail="Lesson plan not found")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # Weekly Schedules Router
        @self.app.post("/weekly-schedules", response_model=WeeklyScheduleResponse)
        async def generate_weekly_schedule(request: WeeklyScheduleRequest):
            """Generate a weekly schedule."""
            try:
                result = self.core_app.generate_weekly_schedule(
                    date.fromisoformat(request.week_start_date),
                    request.age_group,
                    request.weekly_theme,
                    request.duration_minutes,
                )

                if result["status"] == "success":
                    return WeeklyScheduleResponse(success=True, data=result["data"])
                else:
                    raise HTTPException(status_code=400, detail=result["message"])

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/weekly-schedules", response_model=List[Dict[str, Any]])
        async def list_weekly_schedules(
            age_group: Optional[str] = Query(None),
            theme: Optional[str] = Query(None),
            start_date: Optional[str] = Query(None),
            end_date: Optional[str] = Query(None),
        ):
            """List weekly schedules with optional filters."""
            try:
                result = self.core_app.db.search_weekly_schedules(
                    age_group, theme, start_date, end_date
                )
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/weekly-schedules/{schedule_id}", response_model=WeeklyScheduleResponse)
        async def get_weekly_schedule(schedule_id: str):
            """Get a specific weekly schedule."""
            try:
                schedule_data = self.core_app.db.get_weekly_schedule(schedule_id)
                if schedule_data:
                    return WeeklyScheduleResponse(success=True, data=schedule_data)
                else:
                    raise HTTPException(status_code=404, detail="Weekly schedule not found")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # Assessment Router
        @self.app.post("/assessments", response_model=AssessmentResponse)
        async def record_assessment(request: AssessmentRecordRequest):
            """Record an assessment observation."""
            try:
                result = self.core_app.record_assessment(
                    request.child_id,
                    request.date,
                    request.domain,
                    request.observation,
                    request.next_steps,
                )

                if result["status"] == "success":
                    return AssessmentResponse(
                        success=True, message="Assessment recorded successfully"
                    )
                else:
                    raise HTTPException(status_code=400, detail=result["message"])

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/assessments/{child_id}", response_model=Dict[str, Any])
        async def get_child_assessments(
            child_id: str,
            start_date: Optional[str] = Query(None),
            end_date: Optional[str] = Query(None),
            domain: Optional[str] = Query(None),
        ):
            """Get assessments for a child."""
            try:
                if start_date and end_date:
                    result = self.core_app.get_child_progress(child_id, start_date, end_date)
                else:
                    # Return all assessments for the child
                    result = self.core_app.get_child_progress(
                        child_id, "1900-01-01", date.today().isoformat()
                    )

                if result["status"] == "success":
                    return result["data"]
                else:
                    raise HTTPException(status_code=400, detail=result["message"])

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # Progress Reports Router
        @self.app.post("/progress-reports", response_model=ProgressReportResponse)
        async def generate_progress_report(request: ProgressReportRequest):
            """Generate a progress report."""
            try:
                result = self.core_app.generate_progress_report(
                    request.child_id, request.start_date, request.end_date
                )

                if result["status"] == "success":
                    return ProgressReportResponse(success=True, data=result["data"])
                else:
                    raise HTTPException(status_code=400, detail=result["message"])

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # Export Router
        @self.app.get("/export/lesson-plan/{plan_id}/markdown")
        async def export_lesson_markdown(plan_id: str):
            """Export lesson plan as Markdown."""
            try:
                plan_data = self.core_app.db.get_lesson_plan(plan_id)
                if not plan_data:
                    raise HTTPException(status_code=404, detail="Lesson plan not found")

                report_builder = ReportBuilder()
                markdown_content = report_builder.generate_lesson_markdown(plan_data)

                # Save to temporary file and return
                temp_file = Path(f"/tmp/lesson_plan_{plan_id}.md")
                temp_file.write_text(markdown_content)

                return FileResponse(
                    path=temp_file, filename=f"lesson_plan_{plan_id}.md", media_type="text/markdown"
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/export/weekly-schedule/{schedule_id}/markdown")
        async def export_weekly_markdown(schedule_id: str):
            """Export weekly schedule as Markdown."""
            try:
                schedule_data = self.core_app.db.get_weekly_schedule(schedule_id)
                if not schedule_data:
                    raise HTTPException(status_code=404, detail="Weekly schedule not found")

                report_builder = ReportBuilder()
                markdown_content = report_builder.generate_weekly_markdown(schedule_data)

                temp_file = Path(f"/tmp/weekly_schedule_{schedule_id}.md")
                temp_file.write_text(markdown_content)

                return FileResponse(
                    path=temp_file,
                    filename=f"weekly_schedule_{schedule_id}.md",
                    media_type="text/markdown",
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/export/lesson-plan/{plan_id}/pdf")
        async def export_lesson_pdf(plan_id: str, background_tasks: BackgroundTasks):
            """Export lesson plan as PDF."""
            try:
                plan_data = self.core_app.db.get_lesson_plan(plan_id)
                if not plan_data:
                    raise HTTPException(status_code=404, detail="Lesson plan not found")

                report_builder = ReportBuilder()
                pdf_path = f"/tmp/lesson_plan_{plan_id}.pdf"

                # Generate PDF in background
                background_tasks.add_task(report_builder.export_lesson_pdf, plan_data, pdf_path)

                return {"message": f"PDF generation started for {plan_id}"}

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/export/weekly-schedule/{schedule_id}/pdf")
        async def export_weekly_pdf(schedule_id: str, background_tasks: BackgroundTasks):
            """Export weekly schedule as PDF."""
            try:
                schedule_data = self.core_app.db.get_weekly_schedule(schedule_id)
                if not schedule_data:
                    raise HTTPException(status_code=404, detail="Weekly schedule not found")

                report_builder = ReportBuilder()
                pdf_path = f"/tmp/weekly_schedule_{schedule_id}.pdf"

                background_tasks.add_task(report_builder.export_weekly_pdf, schedule_data, pdf_path)

                return {"message": f"PDF generation started for {schedule_id}"}

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # Database Router
        @self.app.get("/database/statistics")
        async def get_database_statistics():
            """Get database statistics."""
            try:
                stats = self.core_app.db.get_statistics()
                return stats
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/database/backup")
        async def backup_database():
            """Create a database backup."""
            try:
                timestamp = date.today().isoformat().replace("-", "")
                backup_path = f"open_early_education_backup_{timestamp}.db"
                self.core_app.db.backup_database(backup_path)
                return {"message": f"Database backed up to {backup_path}"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/database/cleanup")
        async def cleanup_database(days_to_keep: int = 365):
            """Clean up old records."""
            try:
                deleted_count = self.core_app.db.cleanup_old_records(days_to_keep)
                return {"message": f"Cleaned up {deleted_count} old records"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    def run(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Run the FastAPI server."""
        uvicorn.run(self.app, host=host, port=port)
