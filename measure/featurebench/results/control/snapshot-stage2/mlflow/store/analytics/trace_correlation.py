import math
from dataclasses import dataclass

# Recommended smoothing parameter for NPMI calculation
# Using Jeffreys prior (alpha=0.5) to minimize bias while providing robust estimates
JEFFREYS_PRIOR = 0.5


@dataclass
class TraceCorrelationCounts:
    """
    Count statistics for trace correlation analysis.

    This dataclass encapsulates the four fundamental counts needed
    for correlation analysis between two trace filters.

    Attributes:
        total_count: Total number of traces in the experiment(s)
        filter1_count: Number of traces matching filter 1
        filter2_count: Number of traces matching filter 2
        joint_count: Number of traces matching both filters
    """

    total_count: int
    filter1_count: int
    filter2_count: int
    joint_count: int


@dataclass
class NPMIResult:
    """
    Result of NPMI calculation containing both unsmoothed and smoothed values.

    Attributes:
        npmi: Unsmoothed NPMI value with explicit -1.0 rule for zero joint count.
              Returns NaN when undefined (e.g., when filter1_count=0 or filter2_count=0).
        npmi_smoothed: NPMI calculated with Jeffreys prior smoothing (alpha=0.5).
                      More robust for small sample sizes and confidence interval estimation.
    """

    npmi: float
    npmi_smoothed: float | None


def _build_contingency_cells(
    joint_count: int, filter1_count: int, filter2_count: int, total_count: int
) -> tuple[int, int, int, int] | None:
    """
    Build the 2x2 contingency table (n11, n10, n01, n00) from the four counts.

    Returns None when total_count <= 0 or when any cell is negative
    (inconsistent input data).
    """
    if total_count <= 0:
        return None
    n11 = joint_count
    n10 = filter1_count - joint_count
    n01 = filter2_count - joint_count
    n00 = total_count - filter1_count - filter2_count + joint_count
    if min(n11, n10, n01, n00) < 0:
        return None
    return n11, n10, n01, n00


def _npmi_from_cells(n11: float, n10: float, n01: float, n00: float) -> float:
    """
    Compute NPMI from non-negative contingency cells in log space.

    Returns NaN for degenerate marginals. The result is clamped to [-1, 1].
    """
    total = n11 + n10 + n01 + n00
    n1 = n11 + n10
    n2 = n11 + n01
    if n1 <= 0 or n2 <= 0 or n11 <= 0:
        return float("nan")
    # PMI = log(n11 * N / (n1 * n2)); computed as a sum of logs for stability.
    pmi = math.log(n11) + math.log(total) - math.log(n1) - math.log(n2)
    # NPMI = PMI / -log(P(x, y)) where P(x, y) = n11 / N.
    neg_log_joint = math.log(total) - math.log(n11)
    if neg_log_joint <= 0:
        # Only reached when n11 == N, i.e. perfect co-occurrence.
        return 1.0
    npmi = pmi / neg_log_joint
    return max(-1.0, min(1.0, npmi))


def calculate_npmi_from_counts(
    joint_count: int, filter1_count: int, filter2_count: int, total_count: int
) -> NPMIResult:
    """
    Calculate both unsmoothed and smoothed NPMI from count data.

    Implements the recommended policy for NPMI calculation:
    - Returns NaN (undefined) when either filter has zero support (n1=0 or n2=0)
    - Returns -1.0 for unsmoothed when filters never co-occur despite both having support
    - Calculates smoothed version using Jeffreys prior for robustness

    Args:
        joint_count: Number of times both events occur together.
        filter1_count: Number of times event 1 occurs.
        filter2_count: Number of times event 2 occurs.
        total_count: Total number of observations.

    Returns:
        NPMIResult with the unsmoothed ``npmi`` and the Jeffreys-smoothed ``npmi_smoothed``.
        Both are NaN when the counts are inconsistent or total_count <= 0.
    """
    cells = _build_contingency_cells(joint_count, filter1_count, filter2_count, total_count)
    if cells is None:
        return NPMIResult(npmi=float("nan"), npmi_smoothed=float("nan"))

    n11, n10, n01, n00 = cells
    npmi_smoothed = calculate_smoothed_npmi(
        joint_count, filter1_count, filter2_count, total_count, JEFFREYS_PRIOR
    )

    # Zero support for either filter makes the unsmoothed NPMI undefined.
    if filter1_count == 0 or filter2_count == 0:
        return NPMIResult(npmi=float("nan"), npmi_smoothed=npmi_smoothed)

    # Both filters have support but never co-occur: explicit -1.0 rule.
    if n11 == 0:
        return NPMIResult(npmi=-1.0, npmi_smoothed=npmi_smoothed)

    # Perfect co-occurrence: every observation has both events.
    if n10 == 0 and n01 == 0 and n00 == 0:
        return NPMIResult(npmi=1.0, npmi_smoothed=npmi_smoothed)

    return NPMIResult(
        npmi=_npmi_from_cells(n11, n10, n01, n00),
        npmi_smoothed=npmi_smoothed,
    )


def calculate_smoothed_npmi(
    joint_count: int,
    filter1_count: int,
    filter2_count: int,
    total_count: int,
    smoothing: float = JEFFREYS_PRIOR,
) -> float:
    """
    Calculate smoothed NPMI for confidence interval estimation.

    Adds ``smoothing`` (Jeffreys prior 0.5 by default) to every cell of the 2x2
    contingency table before computing NPMI. Returns NaN for inconsistent counts
    (negative cells) or degenerate cases (total_count <= 0). Perfect co-occurrence
    (n10 = n01 = n00 = 0 before smoothing) returns 1.0. The result is clamped to [-1, 1].

    Args:
        joint_count: Number of times both events occur together.
        filter1_count: Number of times event 1 occurs.
        filter2_count: Number of times event 2 occurs.
        total_count: Total number of observations.
        smoothing: Additive smoothing applied to all contingency table cells.

    Returns:
        float: Smoothed NPMI in [-1, 1], or NaN when the calculation is undefined.
    """
    cells = _build_contingency_cells(joint_count, filter1_count, filter2_count, total_count)
    if cells is None:
        return float("nan")

    n11, n10, n01, n00 = cells
    # Perfect co-occurrence is checked on the raw cells, before smoothing.
    if n10 == 0 and n01 == 0 and n00 == 0:
        return 1.0

    return _npmi_from_cells(n11 + smoothing, n10 + smoothing, n01 + smoothing, n00 + smoothing)
