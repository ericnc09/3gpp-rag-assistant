"""Tests for scripts/eval/agreement.py — kappa statistics (pure functions)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.eval.agreement import agreement_report, cohen_kappa, weighted_kappa


class TestCohenKappa:
    def test_perfect_agreement(self):
        assert cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0

    def test_chance_level(self):
        # Observed 0.5, expected 0.5 -> kappa 0.
        assert cohen_kappa([1, 1, 0, 0], [1, 0, 1, 0]) == 0.0

    def test_known_value(self):
        # Textbook 2x2: 20 yes/yes, 5 yes/no, 10 no/yes, 15 no/no -> kappa 0.4
        a = [1] * 25 + [0] * 25
        b = [1] * 20 + [0] * 5 + [1] * 10 + [0] * 15
        assert cohen_kappa(a, b) == pytest.approx(0.4)

    def test_undefined_when_constant(self):
        assert cohen_kappa([1, 1, 1], [1, 1, 1]) is None
        assert cohen_kappa([], []) is None

    def test_length_mismatch(self):
        with pytest.raises(ValueError):
            cohen_kappa([1], [1, 0])


class TestWeightedKappa:
    def test_perfect(self):
        assert weighted_kappa([0, 2, 5, 3], [0, 2, 5, 3]) == 1.0

    def test_near_misses_beat_far_misses(self):
        human = [0, 1, 2, 3, 4, 5]
        near = [1, 2, 3, 4, 5, 4]
        far = [5, 4, 3, 2, 1, 0]
        assert weighted_kappa(human, near) > weighted_kappa(human, far)
        assert weighted_kappa(human, far) < 0

    def test_report_fields(self):
        r = agreement_report([5, 4, 3], [5, 3, 3])
        assert r["n"] == 3 and r["exact_agreement"] == pytest.approx(0.667)
        assert r["within_one"] == 1.0
