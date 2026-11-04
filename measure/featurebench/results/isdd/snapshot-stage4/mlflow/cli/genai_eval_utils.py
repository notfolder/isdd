"""
Utility functions for trace evaluation output formatting.
"""

import re
from dataclasses import dataclass
from typing import Any

import click
import pandas as pd

from mlflow.exceptions import MlflowException
from mlflow.genai.scorers import Scorer, get_all_scorers, get_scorer
from mlflow.tracing.constant import AssessmentMetadataKey

# Represents the absence of a value for an assessment
NA_VALUE = "N/A"


@dataclass
class Assessment:
    """
    Structured assessment data for a trace evaluation.
    """

    name: str | None
    """The name of the assessment"""

    result: Any | None = None
    """The result value from the assessment"""

    rationale: str | None = None
    """The rationale text explaining the assessment"""

    error: str | None = None
    """Error message if the assessment failed"""


@dataclass
class Cell:
    """
    Structured cell data for table display with metadata.
    """

    value: str
    """The formatted display value for the cell"""

    assessment: Assessment | None = None
    """The assessment data for this cell, if it represents an assessment"""


@dataclass
class EvalResult:
    """
    Container for evaluation results for a single trace.

    This dataclass provides structured access to trace evaluation data,
    replacing dict-based access for better type safety.
    """

    trace_id: str
    """The trace ID"""

    assessments: list[Assessment]
    """List of Assessment objects for this trace"""


@dataclass
class TableOutput:
    """Container for formatted table data."""

    headers: list[str]
    rows: list[list[Cell]]


def _format_assessment_cell(assessment: Assessment | None) -> Cell:
    """
    Format a single assessment cell for table display.

    Args:
        assessment: Assessment object with result, rationale, and error fields

    Returns:
        Cell object with formatted value and assessment metadata
    """
    if not assessment:
        return Cell(value=NA_VALUE)

    if assessment.error:
        display_value = f"error: {assessment.error}"
    elif assessment.result is not None and assessment.rationale:
        display_value = f"value: {assessment.result}, rationale: {assessment.rationale}"
    elif assessment.result is not None:
        display_value = f"value: {assessment.result}"
    elif assessment.rationale:
        display_value = f"rationale: {assessment.rationale}"
    else:
        display_value = NA_VALUE

    return Cell(value=display_value, assessment=assessment)


def extract_assessments_from_results(results_df: pd.DataFrame, evaluation_run_id: str) -> list[EvalResult]:
    """
    Extract assessments from evaluation results DataFrame.

    Only assessments whose metadata SOURCE_RUN_ID equals ``evaluation_run_id`` are kept.
    A trace with no matching assessment gets a single error assessment so that every
    trace appears in the output.

    Args:
        results_df (pd.DataFrame): DataFrame from evaluate() results containing an
            'assessments' column (and optionally 'trace_id').
        evaluation_run_id (str): The MLflow run ID of the evaluation run.

    Returns:
        list[EvalResult]: One EvalResult per DataFrame row.
    """
    eval_results = []
    for _, row in results_df.iterrows():
        trace_id = row["trace_id"] if "trace_id" in row.index else "unknown"
        assessments = []
        for entry in row["assessments"] if "assessments" in row.index else []:
            metadata = entry.get("metadata") or {}
            if metadata.get(AssessmentMetadataKey.SOURCE_RUN_ID) != evaluation_run_id:
                continue
            feedback = entry.get("feedback")
            result = feedback.get("value") if isinstance(feedback, dict) else None
            error = entry.get("error")
            assessments.append(
                Assessment(
                    name=entry.get("assessment_name"),
                    result=result,
                    rationale=entry.get("rationale"),
                    error=str(error) if error else None,
                )
            )
        if not assessments:
            assessments.append(Assessment(name=None, error="No assessments found on trace"))
        eval_results.append(EvalResult(trace_id=trace_id, assessments=assessments))
    return eval_results


def format_table_output(output_data: list[EvalResult]) -> TableOutput:
    """
    Format evaluation results into a structured table with trace IDs as rows.

    Headers are "trace_id" followed by the sorted assessment names (None and "N/A" excluded).
    Cells for a missing assessment or a missing value are "N/A" with ``assessment=None``.

    Args:
        output_data (list[EvalResult]): Evaluation results, one per trace.

    Returns:
        TableOutput: Headers and rows of Cell objects.
    """
    names = {
        assessment.name
        for result in output_data
        for assessment in result.assessments
        if assessment.name is not None and assessment.name != NA_VALUE
    }
    headers = ["trace_id"] + sorted(names)

    rows = []
    for result in output_data:
        row = [Cell(value=str(result.trace_id))]
        for name in headers[1:]:
            match = next((a for a in result.assessments if a.name == name), None)
            cell = _format_assessment_cell(match)
            if cell.value == NA_VALUE:
                cell = Cell(value=NA_VALUE)
            row.append(cell)
        rows.append(row)

    return TableOutput(headers=headers, rows=rows)


def _to_snake_case(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def resolve_scorers(scorer_names: list[str], experiment_id: str) -> list[Scorer]:
    """
    Resolve scorer names to scorer objects.

    Built-in scorers are matched first by class name or snake_case name, then registered
    scorers are looked up in the experiment.

    Args:
        scorer_names (list[str]): Built-in class names, snake_case names, or registered names.
        experiment_id (str): Experiment ID used for looking up registered scorers.

    Returns:
        list[Scorer]: Resolved scorers, in the order of ``scorer_names``.

    Raises:
        click.UsageError: If a registered scorer lookup fails, or no scorers are specified.
    """
    builtin_scorers = get_all_scorers()
    builtin_lookup = {}
    for scorer in builtin_scorers:
        class_name = type(scorer).__name__
        builtin_lookup.setdefault(class_name, scorer)
        builtin_lookup.setdefault(_to_snake_case(class_name), scorer)

    resolved = []
    for name in scorer_names:
        if name in builtin_lookup:
            resolved.append(builtin_lookup[name])
            continue
        try:
            resolved.append(get_scorer(name=name, experiment_id=experiment_id))
        except MlflowException as e:
            available = ", ".join(sorted({type(s).__name__ for s in builtin_scorers}))
            raise click.UsageError(
                f"Scorer '{name}' was not found as a built-in or registered scorer. "
                f"Available built-in scorers: {available}. Details: {e}"
            )

    if not resolved:
        raise click.UsageError("No valid scorers specified.")
    return resolved
