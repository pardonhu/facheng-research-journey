"""Original synthetic counterexample, not a published or hardware result.

Python 3 + NumPy. Run from any working directory:
    python rf_phase_alias.py
Writes rf_phase_alias.json next to this script (or use --output PATH).

Two infinite horizontal planes have a carrier-phase alias at two symmetric
calibration positions. Exact scalar free-space 1/r propagation plus one TE
Fresnel reflection is used; diffraction, roughness, polarization mixing, and
other paths are absent. Epsilon is real and nondispersive (lossless material).
The 2-D coordinates describe a cross-section of a 3-D scalar Green function.

Finite-band/array distances use FIXED TOTAL pilot energy per position:
H is divided by sqrt(number of complex entries), then noise is CN(0,sigma^2 I).
Equivalent unnormalized per-entry noise variance is M*sigma^2. Adding entries
therefore does not silently add energy. Each position can have an independent
unknown packet phase or complex gain; these are profiled out explicitly.
"""

import argparse
import json
import math
from pathlib import Path

import numpy as np


C = 299792458.0
WAVELENGTH = 0.05
FC = C / WAVELENGTH
XC = 2.42
LC = math.sqrt(XC**2 + 4)
DB = (2 - math.sqrt((LC + WAVELENGTH)**2 - XC**2)) / 2
Q = (2 - 2 * DB)**2 - 4
XT = math.sqrt(((Q - (WAVELENGTH / 2)**2) / WAVELENGTH)**2 - 4)
EPS_A = 20.0


def fresnel(eps, x, y, d):
    length = np.sqrt(x*x + (y + 1 - 2*d)**2)
    cos_theta = (y + 1 - 2*d) / length
    sin_theta = x / length
    root = np.sqrt(eps - sin_theta**2)
    return (cos_theta - root) / (cos_theta + root)


RHO_A = float(fresnel(EPS_A, XC, 1, 0))
RHO_B = RHO_A * (LC + WAVELENGTH) / LC
COS_B = (2 - 2 * DB) / (LC + WAVELENGTH)
EPS_B = (XC / (LC + WAVELENGTH))**2 + COS_B**2 * ((1-RHO_B)/(1+RHO_B))**2
SIGMA = abs(RHO_A) / LC * 0.05


def channel(x, d, material, n=2, bandwidth=20e6, model="fresnel"):
    y = 1 + (np.arange(n) - (n - 1)/2) * WAVELENGTH/2
    frequencies = (np.linspace(FC-bandwidth/2, FC+bandwidth/2, 17)
                   if bandwidth else np.array([FC]))
    los = np.sqrt(x*x + (y-1)**2)
    reflected = np.sqrt(x*x + (y+1-2*d)**2)
    rho = fresnel(material, x, y, d) if model == "fresnel" else material
    direct = np.exp(-2j*np.pi*frequencies[:, None]*los/C)/los
    bounce = rho*np.exp(-2j*np.pi*frequencies[:, None]*reflected/C)/reflected
    return direct + bounce


def distances(a, b, sigma=SIGMA):
    a, b = a.ravel(), b.ravel()
    inner = np.vdot(a, b)
    # Rotate b to align with a. Stable at identical vectors.
    rotated = b * np.exp(-1j*np.angle(inner))
    fitted = a * inner / np.vdot(a, a)
    scale = math.sqrt(a.size)*sigma
    return {
        "coherent": float(np.linalg.norm(a-b)/scale),
        "packet_phase_profiled": float(np.linalg.norm(a-rotated)/scale),
        # Directed least-squares residual: fit arbitrary complex gain on A.
        "packet_complex_gain_profiled": float(np.linalg.norm(b-fitted)/scale),
    }


def beam_powers(d, material, model="fresnel"):
    h = channel(XT, d, material, n=2, bandwidth=0, model=model).ravel()
    powers = np.abs(np.array([[1, 1], [1, -1]]) @ h / math.sqrt(2))**2
    return {"sum": float(powers[0]), "difference": float(powers[1]),
            "sum_over_difference_db": float(10*np.log10(powers[0]/powers[1]))}


def realvec(z):
    return np.concatenate([z.real, z.imag])


def local_fisher(d, eps):
    # Both symmetric calibration positions have the same response and Jacobian.
    # Project nuisance columns separately per packet; symmetry lets us double F.
    def h(dd, ee):
        return channel(XC, dd, ee).ravel()
    base = h(d, eps)
    jac = np.stack([
        realvec((h(d+1e-7, eps)-h(d-1e-7, eps))/2e-7),
        realvec((h(d, eps+1e-4)-h(d, eps-1e-4))/2e-4),
    ], axis=1)
    result = {}
    for nuisance in ["none", "packet_phase", "packet_complex_gain"]:
        j = jac.copy()
        if nuisance != "none":
            columns = [realvec(1j*base)]
            if nuisance == "packet_complex_gain":
                columns.append(realvec(base))
            basis = np.linalg.qr(np.stack(columns, axis=1))[0]
            j -= basis @ basis.T @ j
        fisher = 4/(SIGMA**2*base.size) * j.T @ j
        covariance = np.linalg.inv(fisher)
        result[nuisance] = {
            "local_plane_sd_mm": float(math.sqrt(covariance[0, 0])*1000),
            "local_epsilon_sd": float(math.sqrt(covariance[1, 1])),
        }
    return result


def run():
    scalar_a = channel(XC, 0, EPS_A, n=1, bandwidth=0)
    scalar_b = channel(XC, DB, EPS_B, n=1, bandwidth=0)
    table = []
    for n in [1, 2, 8]:
        for bandwidth in [0, 20e6, 80e6, 320e6]:
            row = {"antennas": n, "bandwidth_mhz": bandwidth/1e6}
            row.update(distances(channel(XC, 0, EPS_A, n, bandwidth),
                                 channel(XC, DB, EPS_B, n, bandwidth)))
            table.append(row)
    probes = []
    for offset in [0, .05, .1, .25, .5, 1.0]:
        row = {"offset_m": offset, "x_m": XC+offset}
        row.update(distances(channel(XC+offset, 0, EPS_A),
                             channel(XC+offset, DB, EPS_B)))
        probes.append(row)
    fixed_material = {
        "epsilon_b": EPS_A,
        "initial_one_position": distances(channel(XC, 0, EPS_A), channel(XC, DB, EPS_A)),
        "extra_x_plus_0_5": distances(channel(XC+.5, 0, EPS_A), channel(XC+.5, DB, EPS_A)),
        "target_b": beam_powers(DB, EPS_A),
    }
    constant_rho_a = -.9
    constant_rho_b = constant_rho_a*(LC+WAVELENGTH)/LC
    result = {
        "label": "Original synthetic example; not a method comparison or hardware experiment",
        "parameters": {"c_m_per_s": C, "wavelength_m": WAVELENGTH, "carrier_hz": FC,
                       "tx_xy_m": [0, 1], "calibration_x_m": [-XC, XC], "rx_center_y_m": 1,
                       "plane_a_y_m": 0, "plane_b_y_m": DB, "target_x_m": XT,
                       "epsilon_a": EPS_A, "epsilon_b": EPS_B,
                       "conductivity_both_s_per_m": 0,
                       "rho_cal_a": RHO_A, "rho_cal_b": RHO_B,
                       "sigma_normalized_complex_rms": SIGMA,
                       "reference_reflection_snr_db": 20*math.log10(20),
                       "energy_normalization": "Fixed total pilot energy per position; vector / sqrt(M)"},
        "carrier_siso_calibration_absolute_error": float(np.max(np.abs(scalar_a-scalar_b))),
        "target_a": beam_powers(0, EPS_A),
        "target_b": beam_powers(DB, EPS_B),
        "finite_band_array_one_position_distances_sigma": table,
        "two_ant_20mhz_one_position_probe_distances_sigma": probes,
        "local_fisher_two_positions_a": local_fisher(0, EPS_A),
        "local_fisher_two_positions_b": local_fisher(DB, EPS_B),
        "same_material_control": fixed_material,
        "original_constant_reflection_control": {
            "rho_a": constant_rho_a, "rho_b": constant_rho_b,
            "target_a": beam_powers(0, constant_rho_a, "constant"),
            "target_b": beam_powers(DB, constant_rho_b, "constant"),
        },
        "interpretation": {
            "combined_two_calibration_distance": "sqrt(2) times each one-position distance",
            "phase_nuisance": "Independent arbitrary packet phase per position, shared over antennas/frequencies",
            "gain_nuisance": "Further fits arbitrary complex scalar per packet; no cross-packet phase reference",
            "limits": "Known array response/positions; fixed path visibility; no timing-slope nuisance; no hardware test",
        },
    }
    assert result["carrier_siso_calibration_absolute_error"] < 1e-12
    assert result["target_a"]["sum_over_difference_db"] > 10
    assert result["target_b"]["sum_over_difference_db"] < -3
    assert fixed_material["target_b"]["sum_over_difference_db"] < -2
    assert probes[4]["packet_complex_gain_profiled"] > 7
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("rf_phase_alias.json"))
    args = parser.parse_args()
    result = run()
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output.resolve()),
                      "scalar_calibration_error": result["carrier_siso_calibration_absolute_error"],
                      "target_beam_ratios_db": [result["target_a"]["sum_over_difference_db"], result["target_b"]["sum_over_difference_db"]],
                      "extra_probe_gain_profiled_distance_sigma": result["two_ant_20mhz_one_position_probe_distances_sigma"][4]["packet_complex_gain_profiled"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
