"""Gate-neutral ideal three-level output-side integration shared by NPC and T-type.

No device roles, capacitor model, or mutable cross-run state belongs here.
"""


from __future__ import annotations


import math


from bisect import bisect_left, bisect_right


SAMPLES_PER_SWITCHING_PERIOD = 8


def _interpolate(previous: float, current: float, fraction: float) -> float:
    return float(previous) + (float(current) - float(previous)) * float(fraction)


def _interpolate_series_at_time(time_s: list[float], values: list[float], target_time_s: float) -> float:
    if not time_s or len(time_s) != len(values):
        return 0.0
    if target_time_s <= time_s[0]:
        return float(values[0])
    if target_time_s >= time_s[-1]:
        return float(values[-1])
    right = bisect_right(time_s, target_time_s)
    left = right - 1
    span_s = time_s[right] - time_s[left]
    fraction = (target_time_s - time_s[left]) / span_s if span_s > 0.0 else 0.0
    return _interpolate(values[left], values[right], fraction)


def _switching_period_midpoints(time_s: list[float], samples_per_switching_period: int) -> list[float]:
    """Return the midpoint time of each complete sampled switching period."""
    if len(time_s) < 2 or samples_per_switching_period <= 1:
        return []
    cycle_count = (len(time_s) - 1) // samples_per_switching_period
    return [0.5 * (time_s[cycle * samples_per_switching_period] + time_s[(cycle + 1) * samples_per_switching_period]) for cycle in range(cycle_count)]


def _time_average_by_switching_period(time_s: list[float], values: list[float], samples_per_switching_period: int) -> list[float]:
    """Return time-weighted averages over complete sampled switching periods."""
    if len(time_s) != len(values) or len(time_s) < 2 or samples_per_switching_period <= 1:
        return []
    cycle_count = (len(time_s) - 1) // samples_per_switching_period
    averages: list[float] = []
    for cycle in range(cycle_count):
        start = cycle * samples_per_switching_period
        end = (cycle + 1) * samples_per_switching_period
        duration_s = time_s[end] - time_s[start]
        if duration_s <= 0.0:
            averages.append(0.0)
            continue
        area = sum((0.5 * (values[index - 1] + values[index]) * (time_s[index] - time_s[index - 1]) for index in range(start + 1, end + 1)))
        averages.append(area / duration_s)
    return averages


def _required_average_inverter_voltage_by_switching_period(*, time_s: list[float], grid_phase_voltage_v: list[float], actual_current_a: list[float], reference_average_a: list[float], inductance_h: float, samples_per_switching_period: int, voltage_limit_v: float) -> list[float]:
    """Estimate the bounded average inverter voltage needed per switching period.

    With an ideal inductor and an approximately constant inverter voltage over
    one switching period, the period-average current is
    ``i_start + (v_inv_avg - v_grid_avg) * Tsw / (2 * L)``.
    """
    if len(time_s) != len(grid_phase_voltage_v) or len(time_s) != len(actual_current_a) or inductance_h <= 0.0 or (samples_per_switching_period <= 1) or (voltage_limit_v <= 0.0):
        return []
    cycle_count = min((len(time_s) - 1) // samples_per_switching_period, len(reference_average_a))
    targets: list[float] = []
    for cycle in range(cycle_count):
        start = cycle * samples_per_switching_period
        end = (cycle + 1) * samples_per_switching_period
        duration_s = time_s[end] - time_s[start]
        if duration_s <= 0.0:
            targets.append(0.0)
            continue
        grid_area_v_s = sum((0.5 * (grid_phase_voltage_v[index - 1] + grid_phase_voltage_v[index]) * (time_s[index] - time_s[index - 1]) for index in range(start + 1, end + 1)))
        grid_average_v = grid_area_v_s / duration_s
        required_v = grid_average_v + 2.0 * inductance_h * (reference_average_a[cycle] - actual_current_a[start]) / duration_s
        targets.append(min(max(required_v, -voltage_limit_v), voltage_limit_v))
    return targets


def _empty_periodic_solver_result() -> dict[str, object]:
    return {'method': 'periodic_shooting_with_projected_fixed_point_iteration', 'status': 'not_run', 'converged': False, 'initial_current_a': [0.0, 0.0, 0.0], 'period_end_current_a': [0.0, 0.0, 0.0], 'residual_a': [0.0, 0.0, 0.0], 'iterations': 0, 'tolerance_a': 1e-08, 'modulation_saturated': False, 'warm_start_used': False, 'warm_start_fallback_used': False}


def _project_three_phase_current(values: list[float]) -> list[float]:
    if len(values) != 3:
        return [0.0, 0.0, 0.0]
    mean = sum(values) / 3.0
    return [float(value) - mean for value in values]


def _valid_three_phase_current(values: list[float] | None) -> bool:
    if values is None or len(values) != 3:
        return False
    return all((math.isfinite(float(value)) for value in values))


def _solve_periodic_initial_current(*, time_s: list[float], phase_current_reference_a: tuple[list[float], list[float], list[float]], phase_current_reference_average_a: dict[str, list[float]], inductance_h: float, grid_voltage_peak_v: float, line_frequency_hz: float, half_bus_voltage_v: float, samples_per_switching_period: int, reference_initial_current: list[float], warm_start_current: list[float] | None=None) -> tuple[list[float], dict[str, object]]:
    """Solve the periodic current fixed point without endpoint correction."""
    tolerance_a = 1e-08
    max_iterations = 8
    warm_start_used = _valid_three_phase_current(warm_start_current)
    warm_start_fallback_used = False
    iteration_limit = 1 if warm_start_used else max_iterations
    initial = _project_three_phase_current(warm_start_current if warm_start_used else reference_initial_current)
    saturated = False
    result: dict[str, object] | None = None
    for iteration in range(1, iteration_limit + 1):
        result = _simulate_three_level_event_segmented_currents(time_s=time_s, phase_grid_voltage_v=([], [], []), phase_current_reference_a=phase_current_reference_a, phase_current_reference_average_a=phase_current_reference_average_a, inductance_h=inductance_h, grid_voltage_peak_v=grid_voltage_peak_v, line_frequency_hz=line_frequency_hz, half_bus_voltage_v=half_bus_voltage_v, samples_per_switching_period=samples_per_switching_period, _initial_current_a=initial, _solve_periodic=False)
        end_current = list(result['period_end_current_a'])
        residual = [end - start for end, start in zip(end_current, initial, strict=True)]
        saturated = saturated or any((any(values) for values in result['average_current_correction_saturated'].values()))
        if max((abs(value) for value in residual)) <= tolerance_a:
            return (initial, {'method': 'periodic_shooting_with_projected_fixed_point_iteration', 'status': 'converged', 'converged': True, 'initial_current_a': initial, 'period_end_current_a': end_current, 'residual_a': residual, 'iterations': iteration, 'tolerance_a': tolerance_a, 'modulation_saturated': saturated, 'warm_start_used': warm_start_used, 'warm_start_fallback_used': warm_start_fallback_used})
        initial = _project_three_phase_current([value - 0.75 * error for value, error in zip(initial, residual, strict=True)])
    result = _simulate_three_level_event_segmented_currents(time_s=time_s, phase_grid_voltage_v=([], [], []), phase_current_reference_a=phase_current_reference_a, phase_current_reference_average_a=phase_current_reference_average_a, inductance_h=inductance_h, grid_voltage_peak_v=grid_voltage_peak_v, line_frequency_hz=line_frequency_hz, half_bus_voltage_v=half_bus_voltage_v, samples_per_switching_period=samples_per_switching_period, _initial_current_a=initial, _solve_periodic=False)
    end_current = list(result['period_end_current_a'])
    residual = [end - start for end, start in zip(end_current, initial, strict=True)]
    if warm_start_used:
        fallback_initial, fallback_solver = _solve_periodic_initial_current(time_s=time_s, phase_current_reference_a=phase_current_reference_a, phase_current_reference_average_a=phase_current_reference_average_a, inductance_h=inductance_h, grid_voltage_peak_v=grid_voltage_peak_v, line_frequency_hz=line_frequency_hz, half_bus_voltage_v=half_bus_voltage_v, samples_per_switching_period=samples_per_switching_period, reference_initial_current=reference_initial_current)
        fallback_solver['warm_start_used'] = True
        fallback_solver['warm_start_fallback_used'] = True
        return (fallback_initial, fallback_solver)
    return (initial, {'method': 'periodic_shooting_with_projected_fixed_point_iteration', 'status': 'max_iterations_reached', 'converged': max((abs(value) for value in residual)) <= tolerance_a, 'initial_current_a': initial, 'period_end_current_a': end_current, 'residual_a': residual, 'iterations': max_iterations, 'tolerance_a': tolerance_a, 'modulation_saturated': saturated, 'warm_start_used': warm_start_used, 'warm_start_fallback_used': warm_start_fallback_used})


def _simulate_three_level_event_segmented_currents(*, time_s: list[float], phase_grid_voltage_v: tuple[list[float], list[float], list[float]], phase_current_reference_a: tuple[list[float], list[float], list[float]], phase_current_reference_average_a: dict[str, list[float]], inductance_h: float, grid_voltage_peak_v: float, line_frequency_hz: float, half_bus_voltage_v: float, samples_per_switching_period: int, periodic_initial_current_a: list[float] | None=None, _initial_current_a: list[float] | None=None, _solve_periodic: bool=True) -> dict[str, object]:
    """Simulate NPC currents with per-cycle average-current feedback."""
    phase_names = ('a', 'b', 'c')
    phase_angles = (0.0, -2.0 * math.pi / 3.0, 2.0 * math.pi / 3.0)
    empty = {'phase_currents_a': ([], [], []), 'phase_states': ([], [], []), 'pole_voltages_v': ([], [], []), 'line_line_pwm_v': ([], [], []), 'phase_neutral_pwm_v': ([], [], []), 'average_voltage_targets_v': {phase: [] for phase in phase_names}, 'level_duties': {phase: [] for phase in phase_names}, 'candidate_sequences': {phase: [] for phase in phase_names}, 'actual_current_average_a': {phase: [] for phase in phase_names}, 'current_average_error_a': {phase: [] for phase in phase_names}, 'average_current_correction_iterations': {phase: [] for phase in phase_names}, 'average_current_correction_tolerance_a': 1e-06, 'average_current_correction_saturated': {phase: [] for phase in phase_names}, 'event_timeline': [], 'segment_count': 0, 'segments': [], 'periodic_solver': _empty_periodic_solver_result(), 'period_end_current_a': [0.0, 0.0, 0.0]}
    if len(time_s) < 2 or inductance_h <= 0.0 or grid_voltage_peak_v <= 0.0 or (line_frequency_hz <= 0.0) or (half_bus_voltage_v <= 0.0) or (samples_per_switching_period <= 1):
        return empty
    cycle_count = min((len(time_s) - 1) // samples_per_switching_period, *(len(values) for values in phase_current_reference_average_a.values()))
    if cycle_count <= 0:
        return empty
    if _solve_periodic:
        reference_initial = [phase_current_reference_a[index][0] for index in range(3)]
        initial_current, periodic_solver = _solve_periodic_initial_current(time_s=time_s, phase_current_reference_a=phase_current_reference_a, phase_current_reference_average_a=phase_current_reference_average_a, inductance_h=inductance_h, grid_voltage_peak_v=grid_voltage_peak_v, line_frequency_hz=line_frequency_hz, half_bus_voltage_v=half_bus_voltage_v, samples_per_switching_period=samples_per_switching_period, reference_initial_current=reference_initial, warm_start_current=periodic_initial_current_a)
        result = _simulate_three_level_event_segmented_currents(time_s=time_s, phase_grid_voltage_v=phase_grid_voltage_v, phase_current_reference_a=phase_current_reference_a, phase_current_reference_average_a=phase_current_reference_average_a, inductance_h=inductance_h, grid_voltage_peak_v=grid_voltage_peak_v, line_frequency_hz=line_frequency_hz, half_bus_voltage_v=half_bus_voltage_v, samples_per_switching_period=samples_per_switching_period, _initial_current_a=initial_current, _solve_periodic=False)
        result['periodic_solver'] = periodic_solver
        return result
    phase_current_at_cycle_start = list(_initial_current_a if _initial_current_a is not None else [phase_current_reference_a[index][0] for index in range(3)])
    segments: list[dict[str, object]] = []
    target_voltages = {phase: [] for phase in phase_names}
    level_duties = {phase: [] for phase in phase_names}
    candidate_sequences = {phase: [] for phase in phase_names}
    actual_current_average = {phase: [] for phase in phase_names}
    current_average_error = {phase: [] for phase in phase_names}
    correction_iterations = {phase: [] for phase in phase_names}
    correction_saturated = {phase: [] for phase in phase_names}
    for cycle in range(cycle_count):
        start = cycle * samples_per_switching_period
        end = (cycle + 1) * samples_per_switching_period
        cycle_start_s = time_s[start]
        cycle_end_s = time_s[end]
        period_s = cycle_end_s - cycle_start_s
        if period_s <= 0.0:
            continue
        reference_average = [phase_current_reference_average_a[phase][cycle] for phase in phase_names]
        grid_average = [_sinusoidal_voltage_average(grid_voltage_peak_v, line_frequency_hz, phase_angles[index], cycle_start_s, cycle_end_s) for index in range(3)]
        target_voltage = [grid_average[index] + 2.0 * inductance_h * (reference_average[index] - phase_current_at_cycle_start[index]) / period_s for index in range(3)]
        cycle_result: dict[str, object] | None = None
        iteration = 0
        saturated_history = [False, False, False]
        for iteration in range(1, 5):
            cycle_result = _simulate_three_level_cycle_segments(cycle_start_s=cycle_start_s, cycle_end_s=cycle_end_s, phase_current_at_cycle_start=phase_current_at_cycle_start, reference_average_a=reference_average, target_voltage_v=target_voltage, inductance_h=inductance_h, grid_voltage_peak_v=grid_voltage_peak_v, line_frequency_hz=line_frequency_hz, half_bus_voltage_v=half_bus_voltage_v, phase_angles=phase_angles)
            saturated_history = [previous or current for previous, current in zip(saturated_history, cycle_result['saturated'], strict=True)]
            errors = cycle_result['current_average_error_a']
            if max((abs(value) for value in errors)) <= 1e-06:
                break
            target_voltage = [min(max(target_voltage[index] + 2.0 * inductance_h * errors[index] / period_s, -half_bus_voltage_v), half_bus_voltage_v) for index in range(3)]
        if cycle_result is None:
            continue
        segments.extend(cycle_result['segments'])
        phase_current_at_cycle_start = list(cycle_result['end_currents_a'])
        for index, phase in enumerate(phase_names):
            target_voltages[phase].append(cycle_result['target_voltage_v'][index])
            level_duties[phase].append(cycle_result['level_duties'][index])
            candidate_sequences[phase].append(cycle_result['candidate_sequences'][index])
            actual_current_average[phase].append(cycle_result['actual_current_average_a'][index])
            current_average_error[phase].append(cycle_result['current_average_error_a'][index])
            correction_iterations[phase].append(iteration)
            correction_saturated[phase].append(saturated_history[index])
    if not segments:
        return empty
    event_times = sorted({float(value) for segment in segments for value in (segment['start_time_s'], segment['end_time_s'])})
    sampled = _sample_three_level_event_segments(time_s=time_s, segments=segments, inductance_h=inductance_h, grid_voltage_peak_v=grid_voltage_peak_v, line_frequency_hz=line_frequency_hz, phase_angles=phase_angles, half_bus_voltage_v=half_bus_voltage_v)
    segment_start_times, _ = _build_segment_time_index(segments)
    timeline = [{'time_s': float(event_time), 'states': list(_states_at_event_time(segments, event_time, segment_start_times=segment_start_times))} for event_time in event_times]
    return {'phase_currents_a': sampled['phase_currents_a'], 'phase_states': sampled['phase_states'], 'pole_voltages_v': sampled['pole_voltages_v'], 'line_line_pwm_v': sampled['line_line_pwm_v'], 'phase_neutral_pwm_v': sampled['phase_neutral_pwm_v'], 'average_voltage_targets_v': target_voltages, 'level_duties': level_duties, 'candidate_sequences': candidate_sequences, 'actual_current_average_a': actual_current_average, 'current_average_error_a': current_average_error, 'average_current_correction_iterations': correction_iterations, 'average_current_correction_tolerance_a': 1e-06, 'average_current_correction_saturated': correction_saturated, 'period_end_current_a': phase_current_at_cycle_start, 'event_timeline': timeline, 'segment_count': len(segments), 'segments': segments}


def _simulate_three_level_cycle_segments(*, cycle_start_s: float, cycle_end_s: float, phase_current_at_cycle_start: list[float], reference_average_a: list[float], target_voltage_v: list[float], inductance_h: float, grid_voltage_peak_v: float, line_frequency_hz: float, half_bus_voltage_v: float, phase_angles: tuple[float, float, float]) -> dict[str, object]:
    """Integrate one shared PWM cycle and return its actual current average."""
    period_s = cycle_end_s - cycle_start_s
    level_duties = []
    candidate_sequences = []
    saturated = []
    for target_v in target_voltage_v:
        bounded_v = min(max(float(target_v), -half_bus_voltage_v), half_bus_voltage_v)
        saturated.append(abs(bounded_v - float(target_v)) > 1e-12)
        duties = _three_level_level_duty_cycles(bounded_v, half_bus_voltage_v)
        level_duties.append(duties)
        candidate_sequences.append(_center_aligned_three_level_sequence(*duties))
    boundaries = {cycle_start_s, cycle_end_s}
    for sequence in candidate_sequences:
        cursor_s = cycle_start_s
        for item in sequence[:-1]:
            cursor_s += float(item['duty']) * period_s
            boundaries.add(cursor_s)
    ordered_boundaries = sorted(boundaries)
    current = list(phase_current_at_cycle_start)
    current_area = [0.0, 0.0, 0.0]
    segments: list[dict[str, object]] = []
    for left_s, right_s in zip(ordered_boundaries, ordered_boundaries[1:]):
        duration_s = right_s - left_s
        if duration_s <= 1e-15:
            continue
        midpoint_s = 0.5 * (left_s + right_s)
        states = tuple((_sequence_state_at_time(sequence, cycle_start_s, period_s, midpoint_s) for sequence in candidate_sequences))
        poles = tuple((state * half_bus_voltage_v for state in states))
        common_mode_v = sum(poles) / 3.0
        phase_neutral = tuple((value - common_mode_v for value in poles))
        start_currents = tuple(current)
        end_currents = tuple((start_current + (phase_neutral[index] * duration_s - _sinusoidal_voltage_integral(grid_voltage_peak_v, line_frequency_hz, phase_angles[index], left_s, right_s)) / inductance_h for index, start_current in enumerate(start_currents)))
        for index in range(3):
            current_area[index] += start_currents[index] * duration_s + (phase_neutral[index] * duration_s * duration_s / 2.0 - _sinusoidal_voltage_weighted_integral(grid_voltage_peak_v, line_frequency_hz, phase_angles[index], left_s, right_s)) / inductance_h
        segments.append({'start_time_s': left_s, 'end_time_s': right_s, 'states': states, 'pole_voltages_v': poles, 'phase_neutral_voltages_v': phase_neutral, 'start_currents_a': start_currents, 'end_currents_a': end_currents})
        current = list(end_currents)
    actual_average = [value / period_s for value in current_area] if period_s > 0.0 else [0.0] * 3
    return {'segments': segments, 'end_currents_a': current, 'actual_current_average_a': actual_average, 'current_average_error_a': [float(reference_average_a[index]) - actual_average[index] for index in range(3)], 'target_voltage_v': [min(max(float(value), -half_bus_voltage_v), half_bus_voltage_v) for value in target_voltage_v], 'level_duties': level_duties, 'candidate_sequences': candidate_sequences, 'saturated': saturated}


def _sinusoidal_voltage_weighted_integral(peak_v: float, frequency_hz: float, phase_rad: float, start_s: float, end_s: float) -> float:
    """Return integral((end-t) * v_grid(t)) analytically."""
    omega = 2.0 * math.pi * frequency_hz
    duration_s = end_s - start_s
    start_angle = omega * start_s + phase_rad
    end_angle = omega * end_s + phase_rad
    return peak_v * (duration_s * math.cos(start_angle) / omega + (math.sin(start_angle) - math.sin(end_angle)) / (omega * omega))


def _sequence_state_at_time(sequence: list[dict[str, float]], cycle_start_s: float, switching_period_s: float, time_s: float) -> float:
    elapsed_s = min(max(time_s - cycle_start_s, 0.0), switching_period_s)
    cursor_s = 0.0
    for segment in sequence:
        cursor_s += float(segment['duty']) * switching_period_s
        if elapsed_s <= cursor_s + 1e-15:
            return float(segment['state'])
    return float(sequence[-1]['state'])


def _sinusoidal_voltage_integral(peak_v: float, frequency_hz: float, phase_rad: float, start_s: float, end_s: float) -> float:
    omega = 2.0 * math.pi * frequency_hz
    return peak_v * (math.cos(omega * start_s + phase_rad) - math.cos(omega * end_s + phase_rad)) / omega


def _sinusoidal_voltage_average(peak_v: float, frequency_hz: float, phase_rad: float, start_s: float, end_s: float) -> float:
    duration_s = end_s - start_s
    if duration_s <= 0.0:
        return 0.0
    return _sinusoidal_voltage_integral(peak_v, frequency_hz, phase_rad, start_s, end_s) / duration_s


def _current_at_event_time(segments: list[dict[str, object]], phase_index: int, time_s: float, inductance_h: float, grid_voltage_peak_v: float, line_frequency_hz: float, phase_angle_rad: float, *, segment_end_times: list[float] | None=None) -> float:
    if not segments:
        return 0.0
    end_times = segment_end_times or [float(segment['end_time_s']) for segment in segments]
    segment_index = _segment_index_for_current(end_times, time_s)
    segment = segments[segment_index]
    start_s = float(segment['start_time_s'])
    end_s = float(segment['end_time_s'])
    start_current = float(segment['start_currents_a'][phase_index])
    elapsed_s = max(min(time_s, end_s) - start_s, 0.0)
    state = float(segment['phase_neutral_voltages_v'][phase_index])
    grid_area = _sinusoidal_voltage_integral(grid_voltage_peak_v, line_frequency_hz, phase_angle_rad, start_s, start_s + elapsed_s)
    return start_current + (state * elapsed_s - grid_area) / inductance_h


def _states_at_event_time(segments: list[dict[str, object]], time_s: float, *, segment_start_times: list[float] | None=None) -> tuple[float, float, float]:
    if not segments:
        return (0.0, 0.0, 0.0)
    start_times = segment_start_times or [float(segment['start_time_s']) for segment in segments]
    segment_index = _segment_index_for_state(start_times, time_s)
    return tuple((float(value) for value in segments[segment_index]['states']))


def _build_segment_time_index(segments: list[dict[str, object]]) -> tuple[list[float], list[float]]:
    return ([float(segment['start_time_s']) for segment in segments], [float(segment['end_time_s']) for segment in segments])


def _segment_index_for_current(end_times: list[float], time_s: float) -> int:
    """Locate the segment ending at or after an event time."""
    return min(max(bisect_left(end_times, time_s - 1e-15), 0), len(end_times) - 1)


def _segment_index_for_state(start_times: list[float], time_s: float) -> int:
    """Locate the segment active after a state transition boundary."""
    return min(max(bisect_right(start_times, time_s + 1e-15) - 1, 0), len(start_times) - 1)


def _sample_three_level_event_segments(*, time_s: list[float], segments: list[dict[str, object]], inductance_h: float, grid_voltage_peak_v: float, line_frequency_hz: float, phase_angles: tuple[float, float, float], half_bus_voltage_v: float) -> dict[str, object]:
    phase_currents = [[], [], []]
    phase_states = [[], [], []]
    pole_voltages = [[], [], []]
    phase_neutral_voltages = [[], [], []]
    segment_start_times, segment_end_times = _build_segment_time_index(segments)
    for event_time in time_s:
        states = _states_at_event_time(segments, event_time, segment_start_times=segment_start_times)
        poles = tuple((state * half_bus_voltage_v for state in states))
        common_mode_v = sum(poles) / 3.0
        neutral = tuple((value - common_mode_v for value in poles))
        for phase_index in range(3):
            phase_states[phase_index].append(states[phase_index])
            pole_voltages[phase_index].append(poles[phase_index])
            phase_neutral_voltages[phase_index].append(neutral[phase_index])
            phase_currents[phase_index].append(_current_at_event_time(segments, phase_index, event_time, inductance_h, grid_voltage_peak_v, line_frequency_hz, phase_angles[phase_index], segment_end_times=segment_end_times))
    line_line_pwm = ([a - b for a, b in zip(pole_voltages[0], pole_voltages[1], strict=True)], [b - c for b, c in zip(pole_voltages[1], pole_voltages[2], strict=True)], [c - a for c, a in zip(pole_voltages[2], pole_voltages[0], strict=True)])
    return {'phase_currents_a': tuple(phase_currents), 'phase_states': tuple(phase_states), 'pole_voltages_v': tuple(pole_voltages), 'line_line_pwm_v': line_line_pwm, 'phase_neutral_pwm_v': tuple(phase_neutral_voltages)}


def _three_level_level_duty_cycles(average_voltage_v: float, half_bus_voltage_v: float) -> tuple[float, float, float]:
    """Map a bounded average phase voltage to NPC level duties."""
    if half_bus_voltage_v <= 0.0:
        return (0.0, 1.0, 0.0)
    normalized = min(max(float(average_voltage_v) / half_bus_voltage_v, -1.0), 1.0)
    if normalized >= 0.0:
        return (normalized, 1.0 - normalized, 0.0)
    return (0.0, 1.0 + normalized, -normalized)


def _center_aligned_three_level_sequence(d_plus: float, d_zero: float, d_minus: float) -> list[dict[str, float]]:
    """Return a zero-centered legal NPC state sequence for one switching period."""
    active_state = 1.0 if d_plus >= d_minus else -1.0
    active_duty = max(d_plus, d_minus)
    half_zero_duty = max(d_zero, 0.0) / 2.0
    if active_duty <= 1e-15:
        return [{'state': 0.0, 'duty': 1.0}]
    return [{'state': 0.0, 'duty': half_zero_duty}, {'state': active_state, 'duty': active_duty}, {'state': 0.0, 'duty': half_zero_duty}]


def _three_level_operating_contract(*, vdc_v: float, vac_phase_rms_v: float, f_line_hz: float, inductance_h: float, design_power_w: float, i_phase_rms_a: float, current_lag_rad: float, active_power_sign: float) -> dict[str, float | str | bool]:
    """Return the ideal-L voltage command used by the PLECS NPC model."""
    base_impedance_ohm = 3.0 * vac_phase_rms_v * vac_phase_rms_v / max(abs(design_power_w), 1e-12)
    reactance_ohm = 2.0 * math.pi * f_line_hz * inductance_h
    signed_current_rms_a = active_power_sign * i_phase_rms_a
    current_real_a = signed_current_rms_a * math.cos(current_lag_rad)
    current_imag_a = -signed_current_rms_a * math.sin(current_lag_rad)
    inverter_voltage_real_v = vac_phase_rms_v - reactance_ohm * current_imag_a
    inverter_voltage_imag_v = reactance_ohm * current_real_a
    inverter_voltage_rms_v = math.hypot(inverter_voltage_real_v, inverter_voltage_imag_v)
    inverter_voltage_peak_v = math.sqrt(2.0) * inverter_voltage_rms_v
    modulation_index = 2.0 * inverter_voltage_peak_v / max(vdc_v, 1e-12)
    return {'filter_series_resistance_policy': 'ideal_inductor_only', 'filter_series_resistance_pu': 0.0, 'filter_base_impedance_ohm': base_impedance_ohm, 'filter_series_resistance_ohm': 0.0, 'filter_inductive_reactance_ohm': reactance_ohm, 'current_lag_angle_rad': current_lag_rad, 'inverter_voltage_command_rms_v': inverter_voltage_rms_v, 'inverter_voltage_command_peak_v': inverter_voltage_peak_v, 'inverter_voltage_angle_rad': math.atan2(inverter_voltage_imag_v, inverter_voltage_real_v), 'modulation_index': modulation_index, 'modulation_valid': modulation_index <= 1.0, 'modulation_command_basis': 'Vgrid_phase + j*omega*Lphase*Iphase'}
