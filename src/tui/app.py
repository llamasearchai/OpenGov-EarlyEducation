#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beautiful Terminal User Interface for OpenEarlyEducation.

Provides an intuitive, modern interface for early childhood educators
to generate lesson plans, manage assessments, and create reports.
"""

import asyncio
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.status import Status
from rich.table import Table
from rich.text import Text

from src.core.models import DevelopmentalDomain
from src.core.reports import ReportBuilder


class TUIApp:
    """Main TUI application for OpenEarlyEducation."""

    def __init__(self, core_app) -> None:
        self.core_app = core_app
        self.console = Console()
        self.current_view = "main"
        self.selected_child = None
        self.report_builder = ReportBuilder()

    def run(self) -> None:
        """Run the TUI application."""
        self._show_welcome()
        self._main_loop()

    def _show_welcome(self) -> None:
        """Display welcome screen."""
        welcome_text = "OpenEarlyEducation"
        subtitle = "Research-Based Early Childhood Curriculum Planning"

        panel = Panel(
            "\n".join(
                [
                    f"[bold magenta]{welcome_text}[/bold magenta]",
                    "",
                    f"[cyan]{subtitle}[/cyan]",
                    "",
                    "Generate developmentally appropriate lesson plans grounded in empathy and collaboration",
                    "Track authentic assessments and observations",
                    "Create weekly schedules with love-centered classroom practices",
                    "Export professional reports",
                    "",
                    "Navigate by entering numbers for menu options.",
                ]
            ),
            title="Welcome",
            border_style="blue",
            box=box.ROUNDED,
        )

        self.console.print(panel)
        self.console.print()

    def _main_loop(self) -> None:
        """Main application loop."""
        while True:
            try:
                self._show_main_menu()
                choice = self._get_menu_choice()

                if choice == "generate_plan":
                    self._generate_lesson_plan_menu()
                elif choice == "generate_schedule":
                    self._generate_weekly_schedule_menu()
                elif choice == "assessments":
                    self._assessments_menu()
                elif choice == "reports":
                    self._reports_menu()
                elif choice == "database":
                    self._database_menu()
                elif choice == "settings":
                    self._settings_menu()
                elif choice == "exit":
                    self._exit_app()
                    break

            except KeyboardInterrupt:
                self._exit_app()
                break
            except Exception as e:
                self.console.print(f"\n[red]Error: {e}[/red]")
                self.console.print("[yellow]Press Enter to continue...[/yellow]")
                input()

    def _show_main_menu(self) -> None:
        """Display main menu."""
        menu_options = [
            ("-", "Generate Lesson Plan", "generate_plan"),
            ("-", "Generate Weekly Schedule", "generate_schedule"),
            ("-", "Manage Assessments", "assessments"),
            ("-", "Reports & Exports", "reports"),
            ("-", "Database Management", "database"),
            ("-", "Settings", "settings"),
            ("-", "Exit", "exit"),
        ]

        self.console.clear()
        self._show_welcome()

        options_text = []
        for _, title, _ in menu_options:
            options_text.append(f"{title}")

        panel = Panel(
            "\n".join(options_text), title="Main Menu", border_style="cyan", box=box.ROUNDED
        )

        self.console.print(panel)

    def _get_menu_choice(self) -> str:
        """Get user's menu choice."""
        menu_options = [
            "generate_plan",
            "generate_schedule",
            "assessments",
            "reports",
            "database",
            "settings",
            "exit",
        ]

        # Simple numeric selection to avoid external select dependency
        options_render = Table(show_header=False, box=box.SIMPLE)
        options_render.add_column("#", style="cyan", width=4)
        options_render.add_column("Option", style="white")
        for idx, key in enumerate(menu_options, start=1):
            label_map = {
                "generate_plan": "Generate Lesson Plan",
                "generate_schedule": "Generate Weekly Schedule",
                "assessments": "Manage Assessments",
                "reports": "Reports & Exports",
                "database": "Database Management",
                "settings": "Settings",
                "exit": "Exit",
            }
            options_render.add_row(str(idx), label_map.get(key, key))

        self.console.print(options_render)
        sel = Prompt.ask("Enter choice number", default="1")
        try:
            idx = int(sel)
            if 1 <= idx <= len(menu_options):
                return menu_options[idx - 1]
        except Exception:
            pass
        return "exit"

        return choice

    def _generate_lesson_plan_menu(self) -> None:
        """Menu for generating lesson plans."""
        self.console.clear()

        # Get user input
        date = Prompt.ask("Enter date (YYYY-MM-DD)", default=dt.date.today().isoformat())
        age_group = Prompt.ask(
            "Select age group (2-3 / 3-4 / 4-5)", choices=["2-3", "3-4", "4-5"], default="3-4"
        )

        theme = Prompt.ask("Enter lesson theme")
        duration = Prompt.ask("Duration in minutes", default="360")

        # Generate plan
        with self.console.status("[bold green]Generating lesson plan...") as status:
            result = self.core_app.generate_day_plan(
                dt.date.fromisoformat(date), age_group, theme, int(duration)
            )

        if result["status"] == "success":
            plan_data = result["data"]
            self._display_lesson_plan(plan_data)

            # Offer to save
            if Confirm.ask("Save this lesson plan to database?"):
                self.console.print("[green]Lesson plan saved successfully![/green]")

            # Offer export options
            self._export_options(plan_data, "lesson")

        else:
            self.console.print(f"[red]Error: {result['message']}[/red]")

    def _generate_weekly_schedule_menu(self) -> None:
        """Menu for generating weekly schedules."""
        self.console.clear()

        # Get user input
        start_date = Prompt.ask("Enter week start date (YYYY-MM-DD, Monday)")
        age_group = Prompt.ask(
            "Select age group (2-3 / 3-4 / 4-5)", choices=["2-3", "3-4", "4-5"], default="3-4"
        )

        theme = Prompt.ask("Enter weekly theme")
        duration = Prompt.ask("Duration per day in minutes", default="360")

        # Generate schedule
        with self.console.status("[bold green]Generating weekly schedule...") as status:
            result = self.core_app.generate_weekly_schedule(
                dt.date.fromisoformat(start_date), age_group, theme, int(duration)
            )

        if result["status"] == "success":
            schedule_data = result["data"]
            self._display_weekly_schedule(schedule_data)

            # Offer export options
            self._export_options(schedule_data, "weekly")

        else:
            self.console.print(f"[red]Error: {result['message']}[/red]")

    def _assessments_menu(self) -> None:
        """Menu for managing assessments."""
        while True:
            self.console.clear()
            self.console.print(Panel("Assessment Management", border_style="blue", box=box.ROUNDED))

            options = [
                "Record New Observation",
                "View Child Progress",
                "Generate Progress Report",
                "Back to Main Menu",
            ]
            for i, o in enumerate(options, 1):
                self.console.print(f"{i}. {o}")
            sel = Prompt.ask("Enter choice number", default="1")
            choice = (
                options[int(sel) - 1]
                if sel.isdigit() and 1 <= int(sel) <= len(options)
                else "Back to Main Menu"
            )

            if choice == "Record New Observation":
                self._record_observation_menu()
            elif choice == "View Child Progress":
                self._view_progress_menu()
            elif choice == "Generate Progress Report":
                self._generate_report_menu()
            else:
                break

    def _record_observation_menu(self) -> None:
        """Menu for recording observations."""
        self.console.clear()

        child_id = Prompt.ask("Child ID")
        date = Prompt.ask("Date (YYYY-MM-DD)", default=dt.date.today().isoformat())

        domain = Prompt.ask(
            "Developmental domain",
            choices=[d for d in DevelopmentalDomain.all()],
            default=DevelopmentalDomain.social_emotional.value,
        )

        observation = Prompt.ask("Observation (what did you see?)", multiline=True)
        next_steps = Prompt.ask("Next steps (optional)", default="")

        result = self.core_app.record_assessment(child_id, date, domain, observation, next_steps)

        if result["status"] == "success":
            self.console.print("[green]Observation recorded successfully![/green]")
        else:
            self.console.print(f"[red]Error: {result['message']}[/red]")

        self.console.print("\nPress Enter to continue...")
        input()

    def _view_progress_menu(self) -> None:
        """Menu for viewing progress."""
        self.console.clear()

        child_id = Prompt.ask("Child ID")
        start_date = Prompt.ask("Start date (YYYY-MM-DD)", default="2024-01-01")
        end_date = Prompt.ask("End date (YYYY-MM-DD)", default=dt.date.today().isoformat())

        with self.console.status("[bold green]Retrieving progress data..."):
            result = self.core_app.get_child_progress(child_id, start_date, end_date)

        if result["status"] == "success":
            self._display_progress_data(result["data"])
        else:
            self.console.print(f"[red]Error: {result['message']}[/red]")

        self.console.print("\nPress Enter to continue...")
        input()

    def _generate_report_menu(self) -> None:
        """Menu for generating reports."""
        self.console.clear()

        child_id = Prompt.ask("Child ID")
        start_date = Prompt.ask("Start date (YYYY-MM-DD)")
        end_date = Prompt.ask("End date (YYYY-MM-DD)")

        with self.console.status("[bold green]Generating progress report..."):
            result = self.core_app.generate_progress_report(child_id, start_date, end_date)

        if result["status"] == "success":
            report_data = result["data"]
            self._display_report(report_data)

            # Offer to save report
            if Confirm.ask("Save report to file?"):
                filename = f"progress_report_{child_id}_{start_date}_{end_date}.json"
                with open(filename, "w") as f:
                    json.dump(report_data, f, indent=2)
                self.console.print(f"[green]Report saved to {filename}[/green]")

        else:
            self.console.print(f"[red]Error: {result['message']}[/red]")

        self.console.print("\nPress Enter to continue...")
        input()

    def _reports_menu(self) -> None:
        """Menu for reports and exports."""
        while True:
            self.console.clear()
            self.console.print(Panel("Reports & Exports", border_style="blue", box=box.ROUNDED))

            options = [
                "List Lesson Plans",
                "List Weekly Schedules",
                "Export Data",
                "Back to Main Menu",
            ]
            for i, o in enumerate(options, 1):
                self.console.print(f"{i}. {o}")
            sel = Prompt.ask("Enter choice number", default="1")
            choice = (
                options[int(sel) - 1]
                if sel.isdigit() and 1 <= int(sel) <= len(options)
                else "Back to Main Menu"
            )

            if choice == "List Lesson Plans":
                self._list_lesson_plans()
            elif choice == "List Weekly Schedules":
                self._list_weekly_schedules()
            elif choice == "Export Data":
                self._export_menu()
            else:
                break

    def _list_lesson_plans(self) -> None:
        """List stored lesson plans."""
        result = self.core_app.list_lesson_plans()

        if result["status"] == "success":
            plans = result["data"]

            table = Table(title="Lesson Plans")
            table.add_column("Plan ID", style="cyan")
            table.add_column("Date", style="magenta")
            table.add_column("Age Group", style="green")
            table.add_column("Theme", style="yellow")

            for plan in plans:
                table.add_row(plan["plan_id"], plan["date"], plan["age_group"], plan["theme"])

            self.console.print(table)
        else:
            self.console.print(f"[red]Error: {result['message']}[/red]")

        self.console.print("\nPress Enter to continue...")
        input()

    def _list_weekly_schedules(self) -> None:
        """List stored weekly schedules."""
        result = self.core_app.list_weekly_schedules()

        if result["status"] == "success":
            schedules = result["data"]

            table = Table(title="Weekly Schedules")
            table.add_column("Schedule ID", style="cyan")
            table.add_column("Start Date", style="magenta")
            table.add_column("Age Group", style="green")
            table.add_column("Theme", style="yellow")

            for schedule in schedules:
                table.add_row(
                    schedule["schedule_id"],
                    schedule["week_start_date"],
                    schedule["age_group"],
                    schedule["weekly_theme"],
                )

            self.console.print(table)
        else:
            self.console.print(f"[red]Error: {result['message']}[/red]")

        self.console.print("\nPress Enter to continue...")
        input()

    def _export_menu(self) -> None:
        """Menu for export options."""
        self.console.clear()

        export_options = [
            "Export lesson plan as Markdown",
            "Export weekly schedule as Markdown",
            "Export lesson plan as PDF",
            "Export weekly schedule as PDF",
            "Back",
        ]
        for i, o in enumerate(export_options, 1):
            self.console.print(f"{i}. {o}")
        sel = Prompt.ask("Select export option number", default="1")
        choice = (
            export_options[int(sel) - 1]
            if sel.isdigit() and 1 <= int(sel) <= len(export_options)
            else "Back"
        )

        if choice == "Export lesson plan as Markdown":
            self._export_lesson_markdown()
        elif choice == "Export weekly schedule as Markdown":
            self._export_weekly_markdown()
        elif choice == "Export lesson plan as PDF":
            self._export_lesson_pdf()
        elif choice == "Export weekly schedule as PDF":
            self._export_weekly_pdf()

    def _export_lesson_markdown(self) -> None:
        """Export lesson plan as Markdown using most recent generated plan if available."""
        self.console.clear()
        # Ask for plan ID or export from last generated if available
        plan_id = Prompt.ask("Enter plan ID (or leave blank to export most recent)", default="")
        plan_data = None
        if plan_id:
            plan_data = self.core_app.db.get_lesson_plan(plan_id)
        else:
            # Fallback: list recent and choose
            recent = self.core_app.list_lesson_plans().get("data", [])
            if recent:
                plan_id = recent[0]["plan_id"]
                plan_data = self.core_app.db.get_lesson_plan(plan_id)
        if not plan_data:
            self.console.print("[red]No lesson plan found to export.[/red]")
            self.console.print("\nPress Enter to continue...")
            input()
            return
        markdown = self.report_builder.generate_lesson_markdown(plan_data)
        filename = f"lesson_plan_{plan_id or 'latest'}.md"
        Path(filename).write_text(markdown, encoding="utf-8")
        self.console.print(f"[green]Exported lesson markdown to {filename}[/green]")
        self.console.print("\nPress Enter to continue...")
        input()

    def _export_weekly_markdown(self) -> None:
        """Export weekly schedule as Markdown using most recent generated schedule if available."""
        self.console.clear()
        schedule_id = Prompt.ask(
            "Enter schedule ID (or leave blank to export most recent)", default=""
        )
        schedule_data = None
        if schedule_id:
            schedule_data = self.core_app.db.get_weekly_schedule(schedule_id)
        else:
            recent = self.core_app.list_weekly_schedules().get("data", [])
            if recent:
                schedule_id = recent[0]["schedule_id"]
                schedule_data = self.core_app.db.get_weekly_schedule(schedule_id)
        if not schedule_data:
            self.console.print("[red]No weekly schedule found to export.[/red]")
            self.console.print("\nPress Enter to continue...")
            input()
            return
        markdown = self.report_builder.generate_weekly_markdown(schedule_data)
        filename = f"weekly_schedule_{schedule_id or 'latest'}.md"
        Path(filename).write_text(markdown, encoding="utf-8")
        self.console.print(f"[green]Exported weekly markdown to {filename}[/green]")
        self.console.print("\nPress Enter to continue...")
        input()

    def _export_lesson_pdf(self) -> None:
        """Export lesson plan as PDF using most recent generated plan if available."""
        self.console.clear()
        plan_id = Prompt.ask("Enter plan ID (or leave blank to export most recent)", default="")
        plan_data = None
        if plan_id:
            plan_data = self.core_app.db.get_lesson_plan(plan_id)
        else:
            recent = self.core_app.list_lesson_plans().get("data", [])
            if recent:
                plan_id = recent[0]["plan_id"]
                plan_data = self.core_app.db.get_lesson_plan(plan_id)
        if not plan_data:
            self.console.print("[red]No lesson plan found to export.[/red]")
            self.console.print("\nPress Enter to continue...")
            input()
            return
        filename = f"lesson_plan_{plan_id or 'latest'}.pdf"
        success = self.report_builder.export_lesson_pdf(plan_data, filename)
        if success:
            self.console.print(f"[green]Exported lesson PDF to {filename}[/green]")
        else:
            self.console.print("[red]PDF export failed (ensure reportlab is installed)[/red]")
        self.console.print("\nPress Enter to continue...")
        input()

    def _export_weekly_pdf(self) -> None:
        """Export weekly schedule as PDF using most recent generated schedule if available."""
        self.console.clear()
        schedule_id = Prompt.ask(
            "Enter schedule ID (or leave blank to export most recent)", default=""
        )
        schedule_data = None
        if schedule_id:
            schedule_data = self.core_app.db.get_weekly_schedule(schedule_id)
        else:
            recent = self.core_app.list_weekly_schedules().get("data", [])
            if recent:
                schedule_id = recent[0]["schedule_id"]
                schedule_data = self.core_app.db.get_weekly_schedule(schedule_id)
        if not schedule_data:
            self.console.print("[red]No weekly schedule found to export.[/red]")
            self.console.print("\nPress Enter to continue...")
            input()
            return
        filename = f"weekly_schedule_{schedule_id or 'latest'}.pdf"
        success = self.report_builder.export_weekly_pdf(schedule_data, filename)
        if success:
            self.console.print(f"[green]Exported weekly PDF to {filename}[/green]")
        else:
            self.console.print("[red]PDF export failed (ensure reportlab is installed)[/red]")
        self.console.print("\nPress Enter to continue...")
        input()

    def _database_menu(self) -> None:
        """Menu for database operations."""
        while True:
            self.console.clear()
            self.console.print(Panel("Database Management", border_style="blue", box=box.ROUNDED))

            # Get database statistics
            stats = self.core_app.db.get_statistics()

            table = Table()
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")

            table.add_row("Lesson Plans", str(stats["lesson_plans"]))
            table.add_row("Weekly Schedules", str(stats["weekly_schedules"]))
            table.add_row("Assessments", str(stats["assessments"]))
            table.add_row("Database Size", f"{stats['database_size']} bytes")

            self.console.print(table)

            options = [
                "View Age Distribution",
                "View Domain Distribution",
                "Backup Database",
                "Back to Main Menu",
            ]

            choice = Select(options, message="Select option").ask(self.console)

            if choice == "View Age Distribution":
                self._show_distribution("age", stats["age_distribution"])
            elif choice == "View Domain Distribution":
                self._show_distribution("domain", stats["domain_distribution"])
            elif choice == "Backup Database":
                self._backup_database()
            else:
                break

    def _show_distribution(self, name: str, data: Dict) -> None:
        """Show distribution data."""
        self.console.clear()

        table = Table(title=f"{name.title()} Distribution")
        table.add_column(name.title(), style="cyan")
        table.add_column("Count", style="magenta")

        for key, value in data.items():
            table.add_row(key.replace("_", " ").title(), str(value))

        self.console.print(table)
        self.console.print("\nPress Enter to continue...")
        input()

    def _backup_database(self) -> None:
        """Backup database."""
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"open_early_education_backup_{timestamp}.db"

        try:
            self.core_app.db.backup_database(backup_path)
            self.console.print(f"[green]Database backed up to {backup_path}[/green]")
        except Exception as e:
            self.console.print(f"[red]Backup failed: {e}[/red]")

        self.console.print("\nPress Enter to continue...")
        input()

    def _settings_menu(self) -> None:
        """Menu for application settings."""
        self.console.clear()
        self.console.print(Panel("Application Settings", border_style="blue", box=box.ROUNDED))

        self.console.print("[yellow]Settings management will be available in a future update.[/yellow]")
        self.console.print("\nPress Enter to continue...")
        input()

    def _display_lesson_plan(self, plan_data: Dict[str, Any]) -> None:
        """Display lesson plan in beautiful format."""
        self.console.clear()

        # Header
        header = f"[bold cyan]{plan_data['title']}[/bold cyan]"
        subtitle = f"[yellow]{plan_data['date']} | {plan_data['age_group']} | {plan_data['theme']}[/yellow]"

        self.console.print(header)
        self.console.print(subtitle)
        self.console.print()

        # Objectives
        self.console.print("[bold green]Learning Objectives[/bold green]")
        for obj in plan_data["objectives"]:
            self.console.print(
                f"• [blue]{obj['domain'].replace('_', ' ').title()}[/blue]: {obj['objective_text']}"
            )
        self.console.print()

        # Activities
        self.console.print("[bold green]Activities[/bold green]")
        for activity in plan_data["activities"]:
            self.console.print(
                f"• [magenta]{activity['name']}[/magenta] ({activity['duration_minutes']} min)"
            )
            self.console.print(f"  Approach: [cyan]{activity['learning_approach']}[/cyan]")
            if activity["collaboration_type"]:
                self.console.print(
                    f"  Collaboration: [yellow]{activity['collaboration_type'].replace('_', ' ').title()}[/yellow]"
                )
        self.console.print()

        # Social-emotional focus
        self.console.print("[bold green]Social-Emotional Focus[/bold green]")
        self.console.print(f"[cyan]{plan_data['social_emotional_focus']}[/cyan]")
        self.console.print()

    def _display_weekly_schedule(self, schedule_data: Dict[str, Any]) -> None:
        """Display weekly schedule in beautiful format."""
        self.console.clear()

        # Header
        header = f"[bold cyan]{schedule_data['weekly_theme']}[/bold cyan]"
        subtitle = f"[yellow]Week of {schedule_data['week_start_date']} | {schedule_data['age_group']}[/yellow]"

        self.console.print(header)
        self.console.print(subtitle)
        self.console.print()

        # Daily plans
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            plan = schedule_data[f"{day}_plan"]
            self.console.print(f"[bold green]{day.title()}[/bold green]")
            self.console.print(f"• [magenta]{plan['title']}[/magenta]")
            self.console.print(f"  Theme: [cyan]{plan['theme']}[/cyan]")
            self.console.print(f"  Focus: [yellow]{plan['social_emotional_focus']}[/yellow]")
            self.console.print()

        # Special events
        if schedule_data["special_events"]:
            self.console.print("[bold green]Special Events[/bold green]")
            for date, event in schedule_data["special_events"].items():
                self.console.print(f"• [blue]{date}[/blue]: {event}")
            self.console.print()

    def _display_progress_data(self, progress_data: Dict[str, Any]) -> None:
        """Display progress data in beautiful format."""
        self.console.clear()

        # Header
        child_id = progress_data["child_id"]
        period = progress_data["period"]
        self.console.print(f"[bold cyan]Progress Report: {child_id}[/bold cyan]")
        self.console.print(f"[yellow]{period['start']} to {period['end']}[/yellow]")
        self.console.print()

        # Analysis
        analysis = progress_data["analysis"]
        self.console.print("[bold green]Summary[/bold green]")
        self.console.print(f"• Total observations: [cyan]{analysis['total_observations']}[/cyan]")
        self.console.print(f"• Domains covered: [cyan]{analysis['domains_covered']}[/cyan]")
        self.console.print(
            f"• Average observations per day: [cyan]{analysis['average_observations_per_day']}[/cyan]"
        )
        self.console.print()

        if analysis["strengths"]:
            self.console.print("[bold green]Strengths[/bold green]")
            for strength in analysis["strengths"]:
                self.console.print(f"• [green]{strength.replace('_', ' ').title()}[/green]")
            self.console.print()

        if analysis["growth_areas"]:
            self.console.print("[bold green]Growth Areas[/bold green]")
            for area in analysis["growth_areas"]:
                self.console.print(f"• [yellow]{area.replace('_', ' ').title()}[/yellow]")
            self.console.print()

        # Observations by domain
        self.console.print("[bold green]Observations by Domain[/bold green]")
        for domain, observations in progress_data["domain_summary"].items():
            self.console.print(
                f"• [blue]{domain.replace('_', ' ').title()}[/blue]: {len(observations)} observations"
            )

        self.console.print()

    def _display_report(self, report_data: Dict[str, Any]) -> None:
        """Display generated report."""
        self.console.clear()

        # Header
        child_id = report_data["child_id"]
        period = report_data["period"]
        self.console.print(f"[bold cyan]Progress Report: {child_id}[/bold cyan]")
        self.console.print(f"[yellow]{period['start']} to {period['end']}[/yellow]")
        self.console.print()

        # Narrative report
        narrative = report_data.get("narrative_report", {})

        if "summary" in narrative:
            self.console.print("[bold green]Summary[/bold green]")
            self.console.print(f"[cyan]{narrative['summary']}[/cyan]")
            self.console.print()

        if "celebrations" in narrative:
            self.console.print("[bold green]Celebrations[/bold green]")
            for celebration in narrative["celebrations"]:
                self.console.print(f"• [green]{celebration}[/green]")
            self.console.print()

        if "next_steps" in narrative:
            self.console.print("[bold green]Next Steps[/bold green]")
            for step in narrative["next_steps"]:
                self.console.print(f"• [yellow]{step}[/yellow]")
            self.console.print()

        if "recommendations" in narrative:
            self.console.print("[bold green]Recommendations[/bold green]")
            for rec in narrative["recommendations"]:
                self.console.print(f"• [blue]{rec}[/blue]")
            self.console.print()

    def _export_options(self, data: Dict[str, Any], data_type: str) -> None:
        """Offer export options for generated data."""
        self.console.print("\n[bold green]Export Options[/bold green]")

        options = ["View Markdown", "Export as JSON", "Skip export"]

        if data_type == "lesson" and self.report_builder:
            options.insert(1, "Export as PDF")

        choice = Select(options, message="How would you like to export?").ask(self.console)

        if choice == "View Markdown":
            if data_type == "lesson":
                markdown = self.report_builder.generate_lesson_markdown(data)
            else:
                markdown = self.report_builder.generate_weekly_markdown(data)
            self.console.print(markdown)
            self.console.print("\nPress Enter to continue...")
            input()

        elif choice == "Export as JSON":
            filename = f"{data_type}_{data.get('date', 'export')}.json"
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)
            self.console.print(f"[green]Exported to {filename}[/green]")

        elif choice == "Export as PDF":
            filename = f"{data_type}_{data.get('date', 'export')}.pdf"
            if data_type == "lesson":
                success = self.report_builder.export_lesson_pdf(data, filename)
            else:
                success = self.report_builder.export_weekly_pdf(data, filename)

            if success:
                self.console.print(f"[green]PDF exported to {filename}[/green]")
            else:
                self.console.print("[red]PDF export failed[/red]")

    def _exit_app(self) -> None:
        """Exit the application gracefully."""
        self.console.clear()
        self.console.print("[bold cyan]Thank you for using OpenEarlyEducation.[/bold cyan]")
        self.console.print("[green]Wishing you a caring, collaborative day.[/green]")
        self.console.print()
