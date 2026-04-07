"""Motor arc calculation for ST3215 calibration.

Ported from: /software/drivers/st3215/src/calibrate.rs
"""

from dataclasses import dataclass
from st3215 import FULL_RANGE


@dataclass
class MotorArc:
    """Motor movement arc with min and max positions."""
    min: int
    max: int


def calculate_arc(measures_set: set[int]) -> MotorArc:
    """Calculate motor arc from a set of encoder position measurements.

    Determines whether the motor has a direct arc (min to max) or a wrap-around
    arc (crosses the 0/4095 boundary) based on gap analysis.

    Args:
        measures_set: Set of encoder position readings (0-4095)

    Returns:
        MotorArc with min and max positions
    """
    if len(measures_set) < 2:
        if not measures_set:
            return MotorArc(min=0, max=0)
        val = next(iter(measures_set))
        return MotorArc(min=val, max=val)

    # Sort measurements
    sorted_measures = sorted(measures_set)
    min_reading = sorted_measures[0]
    max_reading = sorted_measures[-1]

    # Calculate gaps between consecutive points (including wrap-around)
    gaps = []
    gap_start_points = []

    for i in range(len(sorted_measures)):
        current = sorted_measures[i]
        gap_start_points.append(current)

        if i < len(sorted_measures) - 1:
            next_val = sorted_measures[i + 1]
            gaps.append(next_val - current)
        else:
            # Last element - calculate wrap-around gap
            gap = FULL_RANGE - current + min_reading
            gaps.append(gap)

    # Find largest and second largest gaps
    gap_indices = sorted(range(len(gaps)), key=lambda i: gaps[i], reverse=True)

    largest_gap_idx = gap_indices[0]
    largest_gap_size = gaps[largest_gap_idx]
    second_largest_gap_size = gaps[gap_indices[1]] if len(gaps) > 1 else 0

    # Determine arc type based on gap analysis
    if largest_gap_idx == len(gaps) - 1:
        # Wrap-around gap is largest - indicates direct arc
        return MotorArc(min=min_reading, max=max_reading)
    else:
        # Largest gap is between consecutive readings
        gap_before = gap_start_points[largest_gap_idx]
        gap_after = gap_start_points[(largest_gap_idx + 1) % len(gap_start_points)]

        # Check if this is clearly a wrap-around arc
        is_clearly_wrap_around = largest_gap_size > second_largest_gap_size * 3

        if is_clearly_wrap_around:
            # Wrap-around arc: gap indicates where arc does NOT go
            actual_min = gap_after
            actual_max = gap_before

            return MotorArc(min=actual_min, max=actual_max)
        else:
            # Gaps are evenly distributed - direct arc
            return MotorArc(min=min_reading, max=max_reading)
