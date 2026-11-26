"""Small identifiability counterexample, not a FastSET experiment."""
import json
import numpy as np

N = 8
h_a = np.array([1., 0., 0.])
h_b = np.array([0., 0., 1.])
H_a = np.fft.fft(h_a, N)
H_b = np.fft.fft(h_b, N)
pilot = np.array([0, 4])
X_a = np.ones(N, dtype=complex)
X_b = X_a / H_b
Y_a, Y_b = H_a * X_a, H_b * X_b
out = {
    "scope": "Noiseless OFDM, two pilots, QPSK, no coding constraint. Identifiability example, not new algorithm.",
    "pilot_indices": pilot.tolist(),
    "pilot_channel_difference": float(np.max(np.abs(H_a[pilot] - H_b[pilot]))),
    "entire_received_grid_difference": float(np.max(np.abs(Y_a - Y_b))),
    "qpsk_payload_distance": float(np.min(np.abs(X_b[:, None] - np.array([1, 1j, -1, -1j])[None, :]), axis=1).max()),
    "data_subcarrier_2_channel_values": [float(H_a[2].real), float(H_b[2].real)],
    "data_subcarrier_2_bpsk_labels": [float(X_a[2].real), float(X_b[2].real)],
    "logistic_gradient_at_zero_for_two_worlds": [-0.5, 0.5],
    "extra_known_pilot_at_2_channel_separation": float(abs(H_a[2] - H_b[2])),
    "interpretation": "Same pilots and received samples do not determine the sign of a useful bit-loss update. One known pilot at k=2 resolves this pair; parity/code constraints might already do so and must be tested first."
}
print(json.dumps(out, indent=2))
