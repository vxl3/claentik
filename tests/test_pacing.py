"""Tests for the pacing / backoff logic."""
from __future__ import annotations

from app.config.pacing import Pacer, PacingConfig


def test_base_delay_within_jitter_range():
    config = PacingConfig(base_delay_seconds=4.0, jitter_min=1.0, jitter_max=3.0)
    pacer = Pacer(config)
    for _ in range(50):
        delay = pacer.next_delay(failed=False)
        assert 5.0 <= delay <= 7.0


def test_backoff_grows_on_failure():
    config = PacingConfig(base_delay_seconds=4.0, backoff_base=2.0, backoff_max_seconds=300)
    pacer = Pacer(config)
    d1 = pacer.next_delay(failed=True)
    d2 = pacer.next_delay(failed=True)
    d3 = pacer.next_delay(failed=True)
    assert d1 < d2 < d3


def test_backoff_resets_after_success():
    config = PacingConfig(base_delay_seconds=4.0, backoff_base=2.0, backoff_max_seconds=300)
    pacer = Pacer(config)
    pacer.next_delay(failed=True)
    pacer.next_delay(failed=True)
    assert not pacer.should_stop
    pacer.next_delay(failed=False)
    assert pacer._consecutive_failures == 0


def test_should_stop_after_max_failures():
    config = PacingConfig(max_consecutive_failures=3)
    pacer = Pacer(config)
    pacer.next_delay(failed=True)
    pacer.next_delay(failed=True)
    assert not pacer.should_stop
    pacer.next_delay(failed=True)
    assert pacer.should_stop


def test_backoff_capped_at_max():
    config = PacingConfig(backoff_base=2.0, backoff_max_seconds=10.0)
    pacer = Pacer(config)
    delay = 0
    for _ in range(10):
        delay = pacer.next_delay(failed=True)
    assert delay == 10.0
