#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Assessment service for recording and analyzing child progress.

Provides authentic assessment tracking, progress monitoring,
and research-based reporting aligned with early childhood best practices.
"""

import datetime as dt
import json
import logging
import textwrap
from typing import Any, Dict, List

from openai import OpenAI

from src.core.database import DatabaseManager
from src.core.models import DevelopmentalDomain

logger = logging.getLogger(__name__)


class AssessmentService:
    """
    Enhanced assessment service for early childhood progress tracking.

    Features:
    - Authentic assessment recording
    - Progress report generation
    - Research-based analysis
    - Strengths-based reporting
    """

    def __init__(self, db: DatabaseManager, openai_client: OpenAI) -> None:
        self.db = db
        self.openai_client = openai_client

    def record_observation(
        self,
        child_id: str,
        date: str,
        domain: DevelopmentalDomain,
        observation: str,
        next_steps: str = "",
    ) -> Dict[str, Any]:
        """Record an authentic assessment observation."""
        try:
            if domain not in DevelopmentalDomain.all():
                raise ValueError(f"Invalid domain. Must be one of: {DevelopmentalDomain.all()}")

            self.db.record_assessment(child_id, date, domain, observation, next_steps)

            return {
                "success": True,
                "message": "Observation recorded successfully",
                "data": {
                    "child_id": child_id,
                    "date": date,
                    "domain": domain,
                    "observation": observation,
                    "next_steps": next_steps,
                },
            }
        except Exception as e:
            logger.error(f"Error recording observation: {e}")
            return {"success": False, "message": f"Error recording observation: {str(e)}"}

    def get_child_progress(self, child_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get comprehensive progress data for a child."""
        try:
            observations = self.db.get_assessments(child_id, start_date, end_date)

            if not observations:
                return {
                    "success": True,
                    "data": {
                        "child_id": child_id,
                        "period": {"start": start_date, "end": end_date},
                        "observations": [],
                        "domain_summary": {},
                        "overall_progress": "No observations recorded for this period",
                    },
                }

            # Group by domain
            domain_groups: Dict[str, List[Dict[str, Any]]] = {}
            for obs in observations:
                domain = obs["domain"]
                if domain not in domain_groups:
                    domain_groups[domain] = []
                domain_groups[domain].append(obs)

            # Generate analysis
            analysis = self._analyze_progress(
                child_id, start_date, end_date, observations, domain_groups
            )

            return {
                "success": True,
                "data": {
                    "child_id": child_id,
                    "period": {"start": start_date, "end": end_date},
                    "observations": observations,
                    "domain_summary": domain_groups,
                    "analysis": analysis,
                },
            }

        except Exception as e:
            logger.error(f"Error getting child progress: {e}")
            return {"success": False, "message": f"Error getting progress data: {str(e)}"}

    def generate_progress_report(
        self, child_id: str, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """Generate a comprehensive progress report."""
        try:
            progress_data = self.get_child_progress(child_id, start_date, end_date)

            if not progress_data["success"]:
                return progress_data

            data = progress_data["data"]

            # Use AI to generate narrative report
            narrative = self._generate_narrative_report(child_id, start_date, end_date, data)

            return {
                "success": True,
                "data": {
                    **data,
                    "narrative_report": narrative,
                    "generated_at": dt.datetime.now(dt.UTC).isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Error generating progress report: {e}")
            return {"success": False, "message": f"Error generating report: {str(e)}"}

    def get_domain_progression(self, child_id: str, domain: DevelopmentalDomain) -> Dict[str, Any]:
        """Get progression in a specific domain over time."""
        try:
            # Get all observations for this child and domain
            observations = self.db.get_assessments(child_id, "1900-01-01", "2100-12-31")

            domain_observations = [obs for obs in observations if obs["domain"] == domain]

            if not domain_observations:
                return {
                    "success": True,
                    "data": {
                        "child_id": child_id,
                        "domain": domain,
                        "observations": [],
                        "progression": "No observations recorded for this domain",
                    },
                }

            # Sort by date
            domain_observations.sort(key=lambda x: x["date"])

            # Analyze progression
            progression_analysis = self._analyze_domain_progression(domain_observations)

            return {
                "success": True,
                "data": {
                    "child_id": child_id,
                    "domain": domain,
                    "observations": domain_observations,
                    "progression_analysis": progression_analysis,
                    "total_observations": len(domain_observations),
                },
            }

        except Exception as e:
            logger.error(f"Error getting domain progression: {e}")
            return {"success": False, "message": f"Error getting domain progression: {str(e)}"}

    def _analyze_progress(
        self,
        child_id: str,
        start_date: str,
        end_date: str,
        observations: List[Dict],
        domain_groups: Dict,
    ) -> Dict[str, Any]:
        """Analyze overall progress across domains."""
        total_observations = len(observations)
        domains_covered = len(domain_groups)

        # Calculate observation frequency
        start_dt = dt.datetime.fromisoformat(start_date)
        end_dt = dt.datetime.fromisoformat(end_date)
        days_span = (end_dt - start_dt).days or 1
        avg_observations_per_day = total_observations / days_span

        # Identify strengths and areas for growth
        strengths = []
        growth_areas = []

        for domain, obs_list in domain_groups.items():
            if len(obs_list) >= 3:  # Consider well-documented domains as strengths
                strengths.append(domain)
            else:
                growth_areas.append(domain)

        return {
            "total_observations": total_observations,
            "domains_covered": domains_covered,
            "average_observations_per_day": round(avg_observations_per_day, 2),
            "strengths": strengths,
            "growth_areas": growth_areas,
            "period_days": days_span,
        }

    def _analyze_domain_progression(self, observations: List[Dict]) -> Dict[str, Any]:
        """Analyze progression within a single domain."""
        if len(observations) < 2:
            return {"message": "Need at least 2 observations to analyze progression"}

        # Simple progression analysis based on observation content
        progression_indicators = [
            "improving",
            "progressing",
            "developing",
            "advancing",
            "mastering",
            "consistent",
            "growing",
            "building",
        ]

        progression_score = 0
        for obs in observations:
            obs_text = obs["observation"].lower()
            if any(indicator in obs_text for indicator in progression_indicators):
                progression_score += 1

        # Calculate trend
        dates = [dt.datetime.fromisoformat(obs["date"]) for obs in observations]
        mid_date = dates[len(dates) // 2]

        early_observations = [
            obs for obs in observations if dt.datetime.fromisoformat(obs["date"]) < mid_date
        ]
        later_observations = [
            obs for obs in observations if dt.datetime.fromisoformat(obs["date"]) >= mid_date
        ]

        return {
            "total_observations": len(observations),
            "progression_indicators_found": progression_score,
            "early_period_count": len(early_observations),
            "later_period_count": len(later_observations),
            "trend": "positive" if progression_score > len(observations) * 0.3 else "steady",
            "first_observation": observations[0]["date"],
            "last_observation": observations[-1]["date"],
        }

    def _generate_narrative_report(
        self, child_id: str, start_date: str, end_date: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate narrative progress report using AI."""
        try:
            system_prompt = textwrap.dedent(
                """
            You are an expert early childhood educator specializing in authentic assessment and strengths-based reporting.
            Write clear, professional progress reports that focus on children's strengths, growth, and next steps.
            Use warm, supportive language appropriate for sharing with families and educators.
            Avoid diagnostic or deficit-based language.
            """
            ).strip()

            user_prompt = self._build_report_prompt(child_id, start_date, end_date, data)

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=1000,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            raw_content = response.choices[0].message.content or ""
            report_content = raw_content.strip()

            # Extract structured data from response
            return self._parse_narrative_report(report_content)

        except Exception as e:
            logger.error(f"Error generating narrative report: {e}")
            return {
                "summary": "Unable to generate narrative report due to an error.",
                "recommendations": ["Continue with regular observations and assessments."],
                "celebrations": ["Child is engaged in learning activities."],
                "next_steps": ["Continue supporting child's development across all domains."],
            }

    def _build_report_prompt(
        self, child_id: str, start_date: str, end_date: str, data: Dict[str, Any]
    ) -> str:
        """Build prompt for narrative report generation."""
        return textwrap.dedent(
            f"""
        Please write a comprehensive, strengths-based progress report for child {child_id}
        covering the period from {start_date} to {end_date}.

        Data Summary:
        - Total observations: {data['analysis']['total_observations']}
        - Domains covered: {data['analysis']['domains_covered']}
        - Average observations per day: {data['analysis']['average_observations_per_day']}

        Strengths (well-documented areas): {', '.join(data['analysis']['strengths']) or 'None identified'}
        Growth areas (areas needing more observation): {', '.join(data['analysis']['growth_areas']) or 'None identified'}

        Observations by domain:
        {json.dumps(data['domain_summary'], indent=2)}

        Please structure your response as JSON with the following fields:
        - summary: A 2-3 paragraph overview of the child's progress and strengths
        - celebrations: Array of specific achievements and strengths observed
        - next_steps: Array of recommendations for continued growth and support
        - recommendations: Array of suggestions for educators and families

        Focus on:
        - The child's unique strengths and capabilities
        - Growth and progress over time
        - Social-emotional development and relationships
        - Engagement in learning activities
        - Areas where the child shows particular interest or skill
        """
        ).strip()

    def _parse_narrative_report(self, report_content: str) -> Dict[str, Any]:
        """Parse AI-generated narrative report."""
        try:
            # Try to extract JSON from response
            start = report_content.find("{")
            end = report_content.rfind("}") + 1

            if start != -1 and end != -1:
                json_str = report_content[start:end]
                from typing import cast

                return cast(Dict[str, Any], json.loads(json_str))
            else:
                # Fallback parsing if no JSON found
                return {
                    "summary": report_content,
                    "celebrations": ["Child is engaged and participating in activities."],
                    "next_steps": ["Continue providing supportive learning environment."],
                    "recommendations": ["Regular observation and documentation of progress."],
                }

        except Exception as e:
            logger.error(f"Error parsing narrative report: {e}")
            return {
                "summary": (
                    report_content[:500] + "..." if len(report_content) > 500 else report_content
                ),
                "celebrations": ["Child is engaged in learning activities."],
                "next_steps": ["Continue supporting child's development."],
                "recommendations": ["Continue with regular observations."],
            }
