"""V1 simple/complex cell receptive fields — Hubel & Wiesel 1962, Gabor model.

Reference (neuroscience anchor):
    Hubel DH, Wiesel TN. Receptive fields, binocular interaction and functional
    architecture in the cat's visual cortex.
    J Physiol. 1962 Jan;160(1):106-54.   Nobel Prize in Physiology 1981.
    doi:10.1113/jphysiol.1962.sp006837   PMID:14449617

Reference (mathematical model):
    Daugman JG. Two-dimensional spectral analysis of cortical receptive field
    profiles. Vision Res. 1980;20(10):847-56.
    doi:10.1016/0042-6989(80)90065-6

Reference (energy model for complex cells):
    Adelson EH, Bergen JR. Spatiotemporal energy models for the perception of
    motion. J Opt Soc Am A. 1985 Feb;2(2):284-99.
    doi:10.1364/JOSAA.2.000284

Reference (CNN lineage):
    LeCun Y, Boser B, Denker JS, et al. Backpropagation applied to handwritten
    zip code recognition. Neural Computation. 1989;1(4):541-51.
    doi:10.1162/neco.1989.1.4.541   (cites Hubel & Wiesel directly).

This module implements the modern Gabor-filter formalization of the simple-cell
receptive field that Hubel & Wiesel discovered, plus the Adelson-Bergen energy
model of the complex cell. No invented math: every formula here traces to one
of the four references above.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _orientation_grid(image_size: int, theta_deg: float) -> tuple[np.ndarray, np.ndarray]:
    """Return rotated x', y' coordinate grids centered on the image."""
    half = (image_size - 1) / 2.0
    ys, xs = np.mgrid[0:image_size, 0:image_size].astype(np.float64)
    xs -= half
    ys -= half
    theta = np.deg2rad(theta_deg)
    x_rot = xs * np.cos(theta) + ys * np.sin(theta)
    y_rot = -xs * np.sin(theta) + ys * np.cos(theta)
    return x_rot, y_rot


def gabor_filter(
    *,
    image_size: int,
    orientation_deg: float,
    spatial_frequency_cyc_per_px: float,
    phase_deg: float = 0.0,
    sigma_px: float | None = None,
) -> np.ndarray:
    """Construct a 2D Gabor receptive field.

    Standard Daugman 1980 form, with the convention that orientation_deg = θ
    means the cell responds maximally to bars/edges oriented at θ degrees:
        G(x, y) = exp(-(x'² + y'²) / (2 σ²)) · cos(2π f y' + φ)
    where (x', y') are coordinates rotated by θ. The carrier modulates along
    y' (perpendicular to the preferred edge direction), so the Gabor's bands
    run along x' — i.e. parallel to a bar at orientation θ.

    Args:
        image_size: square filter side in pixels (must be odd for a centered RF).
        orientation_deg: preferred orientation θ in degrees. 0 = bars running
            along the x-axis (horizontal); 90 = bars running along the y-axis.
        spatial_frequency_cyc_per_px: f, the carrier spatial frequency in
            cycles per pixel. Typical biological cells: 0.05 - 0.2.
        phase_deg: φ in degrees. 0 = even-symmetric (cosine), 90 = odd-symmetric (sine).
        sigma_px: Gaussian envelope width. Defaults to one carrier wavelength
            (1 / spatial_frequency), i.e. ≈ 1 cycle visible in the receptive field.
    """
    if image_size < 3 or image_size % 2 == 0:
        raise ValueError("image_size must be an odd integer >= 3")
    if spatial_frequency_cyc_per_px <= 0:
        raise ValueError("spatial_frequency_cyc_per_px must be > 0")

    if sigma_px is None:
        sigma_px = 1.0 / spatial_frequency_cyc_per_px

    x_rot, y_rot = _orientation_grid(image_size, orientation_deg)
    envelope = np.exp(-(x_rot**2 + y_rot**2) / (2.0 * sigma_px**2))
    carrier = np.cos(2.0 * np.pi * spatial_frequency_cyc_per_px * y_rot + np.deg2rad(phase_deg))
    return envelope * carrier


def oriented_bar(
    *,
    image_size: int,
    orientation_deg: float,
    bar_length_px: float | None = None,
    bar_width_px: float = 3.0,
    contrast: float = 1.0,
) -> np.ndarray:
    """Render a high-contrast oriented bar centered on the image."""
    if bar_length_px is None:
        bar_length_px = float(image_size)
    x_rot, y_rot = _orientation_grid(image_size, orientation_deg)
    inside_width = np.abs(y_rot) <= bar_width_px / 2.0
    inside_length = np.abs(x_rot) <= bar_length_px / 2.0
    bar = np.where(inside_width & inside_length, contrast, 0.0)
    return bar


@dataclass(frozen=True, slots=True)
class V1TuningCurve:
    orientations_deg: np.ndarray
    simple_responses: np.ndarray
    complex_responses: np.ndarray


def simple_cell_response(stimulus: np.ndarray, gabor_even: np.ndarray) -> float:
    """Linear filter response = inner product of stimulus and Gabor.

    Simple cells in Hubel-Wiesel terminology have phase-sensitive linear
    receptive fields. The even-symmetric Gabor models the classic 'cosine'
    simple cell. Output is rectified at zero (cells can't fire negatively).
    """
    return float(max(np.sum(stimulus * gabor_even), 0.0))


def complex_cell_response(
    stimulus: np.ndarray, gabor_even: np.ndarray, gabor_odd: np.ndarray
) -> float:
    """Adelson-Bergen 1985 energy model: sqrt(I_even² + I_odd²).

    Complex cells in Hubel-Wiesel terminology are phase-invariant: they
    respond to an oriented edge regardless of where exactly the edge falls
    in the receptive field. The energy model captures this by pooling the
    squared outputs of two simple cells in quadrature (90° phase apart).
    """
    even = float(np.sum(stimulus * gabor_even))
    odd = float(np.sum(stimulus * gabor_odd))
    return float(np.sqrt(even**2 + odd**2))


def orientation_tuning_curve(
    *,
    preferred_orientation_deg: float,
    spatial_frequency_cyc_per_px: float,
    image_size: int = 65,
    n_orientations: int = 36,
    sigma_px: float | None = None,
) -> V1TuningCurve:
    """Sweep an oriented bar through 0-180° and record V1 cell responses.

    Returns the canonical Hubel-Wiesel orientation tuning curve: simple-cell
    response peaks sharply at the preferred orientation and falls toward zero
    at orthogonal; complex-cell response shows the same orientation tuning
    but with a broader, less-cuspy peak due to phase pooling.
    """
    if n_orientations < 4:
        raise ValueError("n_orientations must be >= 4")
    gabor_even = gabor_filter(
        image_size=image_size,
        orientation_deg=preferred_orientation_deg,
        spatial_frequency_cyc_per_px=spatial_frequency_cyc_per_px,
        phase_deg=0.0,
        sigma_px=sigma_px,
    )
    gabor_odd = gabor_filter(
        image_size=image_size,
        orientation_deg=preferred_orientation_deg,
        spatial_frequency_cyc_per_px=spatial_frequency_cyc_per_px,
        phase_deg=90.0,
        sigma_px=sigma_px,
    )

    orientations = np.linspace(0.0, 180.0, n_orientations, endpoint=False)
    simple = np.empty(n_orientations)
    complex_ = np.empty(n_orientations)
    for i, theta in enumerate(orientations):
        bar = oriented_bar(image_size=image_size, orientation_deg=float(theta))
        # Subtract mean so a uniform field gives zero response (DC removal).
        bar = bar - bar.mean()
        simple[i] = simple_cell_response(bar, gabor_even)
        complex_[i] = complex_cell_response(bar, gabor_even, gabor_odd)
    return V1TuningCurve(
        orientations_deg=orientations,
        simple_responses=simple,
        complex_responses=complex_,
    )
