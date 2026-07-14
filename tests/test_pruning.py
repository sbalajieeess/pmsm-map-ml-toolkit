import numpy as np

from pmsm_map_ml.pruning import prune


def test_pruning_creates_zeros():
    model = {"w0": np.arange(1, 11, dtype=np.float32), "b0": np.zeros(1)}
    result = prune(model, 0.5)
    assert np.mean(result["w0"] == 0.0) >= 0.5
