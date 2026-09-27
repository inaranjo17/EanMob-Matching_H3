# tests/test_h3_matching.py
import pytest

from app.services.h3_matching import (
    MAX_DISTANCE_KM,
    TIME_TOLERANCE_MINUTES,
    haversine_km,
    score_distance,
    score_time,
)


def test_score_distance_at_zero():
    assert score_distance(0.0) == 1.0


def test_score_distance_at_max_range():
    assert score_distance(MAX_DISTANCE_KM) == 0.0


def test_score_distance_beyond_max_range_clips_to_zero():
    assert score_distance(MAX_DISTANCE_KM * 3) == 0.0


def test_score_distance_halfway():
    assert score_distance(MAX_DISTANCE_KM / 2) == pytest.approx(0.5)


def test_score_time_at_zero():
    assert score_time(0.0) == 1.0


def test_score_time_at_tolerance_limit():
    assert score_time(TIME_TOLERANCE_MINUTES) == 0.0


def test_score_time_beyond_limit_clips_to_zero():
    assert score_time(TIME_TOLERANCE_MINUTES * 2) == 0.0


def test_haversine_same_point_is_zero():
    assert haversine_km(4.6486, -74.0628, 4.6486, -74.0628) == pytest.approx(0.0)


def test_haversine_known_distance_bogota():
    # Chapinero (aprox) -> Usaquén (aprox), distancia real ~6-7 km
    distance = haversine_km(4.6486, -74.0628, 4.7110, -74.0387)
    assert 5 < distance < 8
