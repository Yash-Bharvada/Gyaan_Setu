"""Bayesian Knowledge Tracing (BKT) Engine.

Models latent student knowledge state $P(L_t)$ per concept/topic,
updating probabilities after each observation (correct/incorrect response).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class BKTParams:
    p_init: float = 0.30      # Prior probability of knowing concept P(L_0)
    p_transit: float = 0.15   # Probability of learning concept during practice P(T)
    p_guess: float = 0.20     # Probability of guessing correctly without knowing P(G)
    p_slip: float = 0.10      # Probability of slipping/making error despite knowing P(S)


class BKTEngine:
    @staticmethod
    def update(
        p_known: float,
        correct: bool,
        params: BKTParams = BKTParams(),
    ) -> float:
        """Calculate updated knowledge state P(L_{t+1}) given observation."""
        p_l = max(0.01, min(0.99, p_known))

        if correct:
            # P(L_t | correct)
            numerator = p_l * (1.0 - params.p_slip)
            denominator = (p_l * (1.0 - params.p_slip)) + ((1.0 - p_l) * params.p_guess)
        else:
            # P(L_t | incorrect)
            numerator = p_l * params.p_slip
            denominator = (p_l * params.p_slip) + ((1.0 - p_l) * (1.0 - params.p_guess))

        if denominator == 0:
            p_l_obs = p_l
        else:
            p_l_obs = numerator / denominator

        # Transition to t+1: P(L_{t+1}) = P(L_t | obs) + (1 - P(L_t | obs)) * P(T)
        p_next = p_l_obs + ((1.0 - p_l_obs) * params.p_transit)
        return round(float(max(0.01, min(0.99, p_next))), 4)

    @staticmethod
    def update_stability(
        current_stability: float,
        correct: bool,
        p_known: float,
    ) -> float:
        """Update memory stability in days (FSRS-inspired curve)."""
        stability = max(0.5, current_stability)
        if correct:
            # Knowledge reinforced; stability grows faster when well-known
            growth_factor = 1.0 + (p_known * 1.5)
            new_stability = stability * growth_factor
        else:
            # Failure resets stability back down
            new_stability = max(0.5, stability * 0.4)

        return round(float(new_stability), 2)
