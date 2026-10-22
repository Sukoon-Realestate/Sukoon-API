import numpy as np
from core_apps.virtual_tours.capture_panorama import exposure_gain, global_appearance


def test_exposure_is_bounded_and_never_fills_unknown_pixels():
    total = np.full((64,64,3), 200, np.float32)
    weights = np.ones((64,64), np.float32)
    incoming = np.full((64,64,3), 40, np.uint8)
    np.testing.assert_allclose(exposure_gain(total, weights, incoming, weights > 0), [4/3]*3)
    np.testing.assert_allclose(exposure_gain(total, weights, incoming, weights < 0), [1]*3)


def test_ghosting_and_global_wrap_discontinuity_fail_quality():
    pixels = np.full((8,16,3), 120, np.uint8)
    weights = np.full((8,16), 2, np.float32)
    total = pixels.astype(np.float32)*2
    squares = pixels.astype(np.float32)**2*2
    counts = np.full((8,16), 2, np.uint8)
    mask = counts > 0
    assert global_appearance(total,squares,weights,counts,mask,pixels)["appearanceValidated"]
    assert not global_appearance(total,squares+weights[:,:,None]*900,weights,counts,mask,pixels)["appearanceValidated"]
    pixels[:, -1] = 240
    assert not global_appearance(total,squares,weights,counts,mask,pixels)["appearanceValidated"]
    assert global_appearance(total,squares,weights,counts*0,mask,pixels)["overlapStdP90"] is None
