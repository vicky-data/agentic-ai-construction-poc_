"""
RAG Retriever — Builds a text corpus from real DB data and answers
natural language questions using TF-IDF similarity + template responses.
No external LLM API required.
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime


class ProjectRAG:
    """
    Retrieval-Augmented Generation for project Q&A.
    Builds a searchable corpus from real project data.
    """

    def __init__(self):
        self.corpus = []
        self.metadata = []
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        self._fitted = False

    def build_corpus(
        self,
        project: pd.Series,
        expenses_df: pd.DataFrame,
        manpower_df: pd.DataFrame,
        materials_df: pd.DataFrame,
        machinery_df: pd.DataFrame,
        approvals_df: pd.DataFrame,
        boq_df: pd.DataFrame,
        users_df: pd.DataFrame,
        progress: dict,
        risk: dict,
    ):
        """Build text corpus from all available project data."""
        self.corpus = []
        self.metadata = []

        project_name = project.get("project_name", "Unknown")

        # ── Project Overview ──
        self._add(
            f"Project {project_name} is located at {project.get('location', 'N/A')}. "
            f"Status is {project.get('status', 'N/A')}. "
            f"Planned start date is {project.get('planned_start_date')}. "
            f"Planned end date is {project.get('planned_end_date')}. "
            f"Total budget is {project.get('total_price', 0)} INR. "
            f"Planned manpower is {project.get('man_power', 0)}.",
            "project_overview",
        )

        # ── Progress Summary ──
        self._add(
            f"Project progress: {progress.get('time_progress_pct', 0):.0f}% of time elapsed. "
            f"Total spent: {progress.get('total_spent', 0):,.0f} INR out of "
            f"{progress.get('total_budget', 0):,.0f} INR budget "
            f"({progress.get('cost_progress_pct', 0):.0f}% used). "
            f"Days remaining: {progress.get('days_remaining', 'N/A')}. "
            f"Health status: {progress.get('health', 'Unknown')}. "
            f"Cost overrun: {progress.get('cost_overrun', 0):,.0f} INR.",
            "progress_summary",
        )

        # ── Risk Summary ──
        risk_factors = "; ".join(risk.get("factors", []))
        self._add(
            f"Risk assessment: Level is {risk.get('risk_level', 'N/A')} "
            f"with score {risk.get('risk_score', 0)} and "
            f"confidence {risk.get('confidence', 0)}%. "
            f"Risk factors: {risk_factors}",
            "risk_summary",
        )

        # ── Expense Details ──
        if not expenses_df.empty:
            total_exp = expenses_df["amount"].sum()
            expense_types = expenses_df.groupby("parent_type")["amount"].sum()
            expense_summary = ", ".join(
                [f"{k}: {v:,.0f} INR" for k, v in expense_types.items()]
            )
            self._add(
                f"Total expenses: {total_exp:,.0f} INR. "
                f"Breakdown by category: {expense_summary}. "
                f"Number of expense records: {len(expenses_df)}.",
                "expenses",
            )

            # Daily expense trend
            try:
                exp_by_date = expenses_df.groupby("reporting_date")["amount"].sum()
                if len(exp_by_date) > 0:
                    avg_daily = exp_by_date.mean()
                    max_daily = exp_by_date.max()
                    self._add(
                        f"Average daily expense: {avg_daily:,.0f} INR. "
                        f"Maximum daily expense: {max_daily:,.0f} INR. "
                        f"Total reporting days with expenses: {len(exp_by_date)}.",
                        "expense_trend",
                    )
            except Exception:
                pass

        # ── Manpower Details ──
        if not manpower_df.empty:
            total_workers = manpower_df["man_count"].sum()
            avg_workers = manpower_df["man_count"].mean()
            mp_types = manpower_df.groupby("man_power_type")["man_count"].sum()
            mp_summary = ", ".join(
                [f"{k}: {v}" for k, v in mp_types.items()]
            )
            self._add(
                f"Total manpower records: {total_workers}. "
                f"Average daily manpower: {avg_workers:.0f}. "
                f"Manpower by type: {mp_summary}.",
                "manpower",
            )

        # ── Material Details ──
        if not materials_df.empty and "line_item_name" in materials_df.columns:
            mat_grouped = materials_df.groupby("line_item_name")["used_material"].sum()
            mat_summary = ", ".join(
                [f"{k}: {v}" for k, v in mat_grouped.head(10).items()]
            )
            self._add(
                f"Material usage: {mat_summary}. "
                f"Total material records: {len(materials_df)}.",
                "materials",
            )

        # ── Machinery Details ──
        if not machinery_df.empty:
            mach_types = machinery_df.groupby("parent_type").size()
            mach_summary = ", ".join(
                [f"{k}: {v} entries" for k, v in mach_types.items()]
            )
            self._add(
                f"Machinery usage: {mach_summary}. "
                f"Total machinery records: {len(machinery_df)}.",
                "machinery",
            )

        # ── Approval Status ──
        if not approvals_df.empty:
            status_counts = approvals_df["status"].value_counts()
            app_summary = ", ".join(
                [f"{k}: {v}" for k, v in status_counts.items()]
            )
            self._add(
                f"Daily report approvals: {app_summary}. "
                f"Total reports: {len(approvals_df)}.",
                "approvals",
            )

        # ── BOQ Scope ──
        if not boq_df.empty:
            boq_count = len(boq_df)
            self._add(
                f"Bill of Quantities: {boq_count} line items scoped for this project.",
                "boq",
            )
            # Add individual BOQ items
            for _, row in boq_df.head(20).iterrows():
                self._add(
                    f"BOQ item: {row.get('parent_item_name', 'N/A')} > "
                    f"{row.get('line_item_name', 'N/A')}, "
                    f"scope: {row.get('scope_quantity', 'N/A')} "
                    f"{row.get('unit_of_measurement', '')}.",
                    "boq_item",
                )

        # ── Team ──
        if not users_df.empty:
            team_summary = ", ".join(
                [f"{row.get('full_name', 'N/A')} ({row.get('role_name', 'N/A')})"
                 for _, row in users_df.iterrows()]
            )
            self._add(
                f"Project team: {team_summary}. "
                f"Total team members: {len(users_df)}.",
                "team",
            )

        # Fit TF-IDF
        if self.corpus:
            self.vectorizer.fit(self.corpus)
            self._fitted = True

    def answer_question(self, question: str) -> str:
        """
        Answer a question by finding the most relevant corpus chunks
        and composing a natural language response.
        """
        if not self._fitted or not self.corpus:
            return "❌ No project data loaded. Please select a project first."

        # Find most relevant chunks
        q_vec = self.vectorizer.transform([question])
        corpus_vec = self.vectorizer.transform(self.corpus)
        similarities = cosine_similarity(q_vec, corpus_vec).flatten()

        # Get top 3 most relevant
        top_indices = similarities.argsort()[-3:][::-1]
        top_scores = similarities[top_indices]

        if top_scores[0] < 0.05:
            return (
                "🤔 I couldn't find specific information about that in the project data. "
                "Try asking about expenses, manpower, materials, timeline, risk, or team members."
            )

        # Compose answer from relevant chunks
        relevant_chunks = [self.corpus[i] for i in top_indices if similarities[i] > 0.03]
        context = " ".join(relevant_chunks)

        # Generate response
        response = f"📊 **Based on project data:**\n\n"
        for i, idx in enumerate(top_indices):
            if similarities[idx] > 0.03:
                category = self.metadata[idx]
                chunk = self.corpus[idx]
                response += f"• {chunk}\n\n"

        return response.strip()

    def _add(self, text: str, category: str):
        """Add a text chunk to the corpus."""
        self.corpus.append(text)
        self.metadata.append(category)


def get_quick_questions() -> list[str]:
    """Return a list of suggested quick questions."""
    return [
        "What is the total expense?",
        "How many workers are on site?",
        "What is the project risk level?",
        "How many days remaining?",
        "What materials are being used?",
        "What is the budget status?",
        "Who is on the project team?",
        "What is the current progress?",
    ]
