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


def extract_assessments_from_results(
    results_df: pd.DataFrame, evaluation_run_id: str
) -> list[EvalResult]:
    """
    Extract assessments from evaluation results DataFrame.

    Only assessments whose metadata SOURCE_RUN_ID equals ``evaluation_run_id`` are kept.
    A trace with no matching assessment gets a single error Assessment.

    Args:
        results_df: DataFrame from evaluate() results with 'trace_id' and 'assessments' columns.
        evaluation_run_id: The MLflow run ID of the evaluation that generated the assessments.

    Returns:
        list[EvalResult]: One EvalResult per DataFrame row.
    """
    eval_results = []
    for _, row in results_df.iterrows():
        trace_id = row["trace_id"] if "trace_id" in row else "unknown"
        raw_assessments = row["assessments"] if "assessments" in row else []

        assessments = []
        for entry in raw_assessments:
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
            assessments.append(Assessment(name=NA_VALUE, error="No assessments found on trace"))

        eval_results.append(EvalResult(trace_id=trace_id, assessments=assessments))
    return eval_results


def format_table_output(output_data: list[EvalResult]) -> TableOutput:
    """
    Format evaluation results into a table with trace IDs as rows and assessment names as columns.

    Args:
        output_data: List of EvalResult objects.

    Returns:
        TableOutput: headers start with "trace_id" followed by sorted assessment names
        (None and "N/A" excluded); each row starts with a trace ID cell and then one cell per
        header, "N/A" where the trace has no such assessment.
    """
    names = {
        assessment.name
        for result in output_data
        for assessment in result.assessments
        if assessment.name is not None and assessment.name != NA_VALUE
    }
    column_names = sorted(names)
    headers = ["trace_id", *column_names]

    rows = []
    for result in output_data:
        row = [Cell(value=str(result.trace_id))]
        for column in column_names:
            match = next(
                (a for a in result.assessments if a.name == column),
                None,
            )
            cell = _format_assessment_cell(match) if match is not None else Cell(value=NA_VALUE)
            row.append(cell)
        rows.append(row)

    return TableOutput(headers=headers, rows=rows)


def _to_snake_case(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def resolve_scorers(scorer_names: list[str], experiment_id: str) -> list[Scorer]:
    """
    Resolve scorer names to scorer objects.

    Built-in scorers are matched first by class name or snake_case name, then registered
    scorers are looked up in ``experiment_id``.

    Args:
        scorer_names: Built-in class names, snake_case names, or registered scorer names.
        experiment_id: Experiment ID used for looking up registered scorers.

    Returns:
        list[Scorer]: Resolved scorers in input order.

    Raises:
        click.UsageError: If a registered-scorer lookup raises an MlflowException, or if no
            valid scorers are specified.
    """
    builtin_scorers = {}
    for scorer in get_all_scorers():
        class_name = scorer.__class__.__name__
        builtin_scorers[class_name] = scorer
        builtin_scorers[_to_snake_case(class_name)] = scorer

    resolved = []
    for name in scorer_names:
        if name in builtin_scorers:
            resolved.append(builtin_scorers[name])
            continue
        try:
            resolved.append(get_scorer(name=name, experiment_id=experiment_id))
        except MlflowException as e:
            available = ", ".join(sorted({s.__class__.__name__ for s in get_all_scorers()}))
            raise click.UsageError(
                f"Scorer '{name}' was not found as a built-in or registered scorer. "
                f"Available built-in scorers: {available}. Error: {e}"
            )

    if not resolved:
        raise click.UsageError("No valid scorers specified")
    return resolved
