"""Original scalar counterexample, not a hardware or paper reproduction.

For a real-valued reference amplitude a, conjugate unknown responses have
identical magnitudes. A future complex interferer can distinguish them.
Run: python reference_phase_ambiguity.py
"""
import json
from pathlib import Path


def evaluate():
    zp, zm, other = complex(0.6, 0.8), complex(0.6, -0.8), complex(0, 0.8)
    amplitudes = [k / 100 for k in range(301)]
    error = max(abs(abs(zp + a) - abs(zm + a)) for a in amplitudes)
    threshold = 1.2
    result = {
        "kind": "original_single_tap_identifiability_counterexample",
        "reference_phase": "real_axis",
        "reference_amplitude_points": len(amplitudes),
        "maximum_observation_difference": error,
        "future_combination_magnitudes": [abs(zp + other), abs(zm + other)],
        "threshold": threshold,
        "threshold_crossings": [abs(zp + other) >= threshold, abs(zm + other) >= threshold],
        "hardware_measurement": False,
        "analytic_reason": "abs(x+iy+a)^2=(x+a)^2+y^2 for real a; sign(y) is unobserved",
    }
    assert error < 1e-12
    assert result["threshold_crossings"] == [True, False]
    return result


if __name__ == "__main__":
    result = evaluate()
    text = json.dumps(result, indent=2) + "\n"
    Path(__file__).with_suffix(".json").write_text(text, encoding="utf-8")
    print(text, end="")
