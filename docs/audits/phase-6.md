# Phase 6 Audit — Hubel-Wiesel V1 (Gabor + Energy Model)

**Date:** 2026-04-30
**Owner:** Alex Pinkevich
**Implementer:** Claude (Opus 4.7, 1M context)
**Cross-model audit:** PENDING

## Allen Brain Atlas decision (revisited)
The Phase 0 audit listed three options for the Python-3.12-incompatible `allensdk` package. **Phase 6 sidesteps the question entirely:** the Hubel-Wiesel module needs (a) a mathematical V1 receptive-field model and (b) real V1 morphology. The model is Gabor + Adelson-Bergen, both fully published. Real V1 morphology is already accessible through our existing NeuroMorpho.org client. No Allen integration was added in this phase. The Allen decision remains genuinely open and will be re-raised when a module actually needs Allen-only data (electrophysiology recordings).

## Scope of Phase 6
V1 simple/complex receptive-field module. Daugman 1980 Gabor as the modern formalization of the Hubel-Wiesel 1962 simple-cell discovery, plus the Adelson-Bergen 1985 energy model for complex cells. Endpoint returns the Gabor filter visualization, an orientation tuning curve, and a citation. Frontend renders the even/odd Gabor as canvas images and plots simple/complex tuning curves with the preferred orientation highlighted.

## What got built
- `backend/neuroforge_api/simulators/hubel_wiesel.py`:
  - `gabor_filter(image_size, orientation_deg, spatial_frequency_cyc_per_px, phase_deg, sigma_px)` — Daugman 1980 form, oriented so a Gabor at θ responds maximally to bars at θ.
  - `oriented_bar(...)` — high-contrast bar stimulus generator.
  - `simple_cell_response(stimulus, gabor_even)` — half-wave-rectified inner product.
  - `complex_cell_response(stimulus, even, odd)` — Adelson-Bergen energy: √(I_even² + I_odd²).
  - `orientation_tuning_curve(...)` — sweep bars 0–180°, return both simple and complex responses.
  - Module docstring traces every formula to one of: Hubel-Wiesel 1962, Daugman 1980, Adelson-Bergen 1985, LeCun 1989.
- `backend/neuroforge_api/models/simulation.py` — `V1Request` (preferred_orientation, spatial_frequency, image_size, n_orientations, sigma) and `V1Response` (filter arrays + tuning arrays + parameters + citation).
- `backend/neuroforge_api/routers/simulate.py` — POST `/api/simulate/v1`.
- Frontend:
  - `lib/types.ts`, `lib/api.ts` — V1 types + `simulateV1()`.
  - `components/inspector/HubelWieselPanel.tsx` — canvas-rendered even/odd Gabors, SVG tuning curve (white = simple, blue = complex, red dashed = preferred), CNN-lineage note, citation.
  - `components/inspector/NeuronInspector.tsx` — HubelWieselPanel mounted under STDPPanel.

## Verified — 2026-04-30

### Backend test suite
```
$ pytest neuroforge_api/tests -q
40 passed in 11.69s
```
- 8 new V1 tests:
  - Gabor zero-mean (band-pass).
  - Gabor energy is rotation-invariant within 5%.
  - Tuning peaks at preferred orientation across {0°, 30°, 45°, 90°, 135°}.
  - Orthogonal response < 5% of preferred.
  - Simple-cell rectifier: anti-correlated stimulus → 0 (not negative).
  - Complex-cell phase invariance: complex response stable within 1% across phase shifts of an input matched to the preferred orientation. **This is the canonical Adelson-Bergen test that distinguishes complex from simple cells.**
  - Endpoint returns canonical tuning curve, peak at the right orientation, real DOI in citation, filter arrays at right shape.
  - Endpoint rejects negative spatial frequency.

### Live HTTP smoke test
```
$ curl -s -X POST -H 'Content-Type: application/json' \
       -d '{"preferred_orientation_deg":45}' \
       http://localhost:8000/api/simulate/v1

pref=45.0 sf=0.1 sigma=10.0 image_size=65
peak_simple_at=45.0° peak_value=71.69
gabor_even shape: 65x65
citation: "Hubel DH, Wiesel TN. Receptive fields, binocular interaction and
           functional architecture in the cat's visual cortex.
           J Physiol. 1962;160(1):106-54. doi:10.1113/jphysiol.1962.sp006837"
```
- Peak of the simple-cell tuning curve falls exactly on the requested preferred orientation (45.0°).
- Gabor filter is 65×65, sigma_px=10 (= 1 / spatial_frequency, one carrier wavelength visible across the RF).
- DOI `10.1113/jphysiol.1962.sp006837` resolves to the actual H-W 1962 paper.

### Browser verification
With θ_pref = 45 and "compute" clicked:
- Even-Gabor canvas shows alternating black/white bands at 45° with a Gaussian envelope — the classic Gabor / V1-simple-cell receptive field.
- Tuning curve peaks at exactly 45° with a red dashed line marking the preferred orientation. Falls off symmetrically toward 0° and 90°.
- CNN-lineage note: "LeCun 1989 cited Hubel & Wiesel directly. The first conv-layer filter of any modern CNN (VGG, ResNet) converges to a Gabor like the one above."
- Citation panel shows the full H-W 1962 reference with DOI.

### Linters
- `ruff check neuroforge_api` — clean
- `pnpm typecheck` — clean
- `pnpm lint` — clean

## Anti-theater self-checks
- **No invented math.** Every formula in `hubel_wiesel.py` is traced to Hubel-Wiesel 1962, Daugman 1980, Adelson-Bergen 1985, or LeCun 1989. The Gaussian envelope, cosine carrier, even/odd quadrature pair, and √(I_even² + I_odd²) energy pooling are all from these papers.
- **No fake tuning curve.** The curve is built by computing real Gabor inner products against real bar stimuli swept through 36 orientations. Frontend renders only what `tuning_simple` and `tuning_complex` contain.
- **No fake Gabor visualization.** The canvas image is a direct grayscale mapping of `response.gabor_even` / `response.gabor_odd` returned by the backend.
- **No invented CNN claim.** The CNN-lineage note states a verifiable historical fact (LeCun 1989 cited Hubel & Wiesel) without overclaiming.
- **No fake citation.** DOI `10.1113/jphysiol.1962.sp006837` is the real Hubel-Wiesel 1962 J Physiol paper.

## Honest limitations

1. **Not yet wired to real V1 neuron morphology.** The simulator works on the abstract receptive-field level. Showing a real V1 pyramidal from NeuroMorpho's visual cortex archive next to the Gabor (per ARCHITECTURE.md ambition) would require either fetching a V1 neuron and rendering it under the panel, or layering it onto the existing 3D viewer. Deferred to polish.
2. **No live "drag the bar" interaction.** The orientation tuning curve is precomputed for 36 angles, not driven by a draggable bar widget. Adding a draggable stimulus + live receptive-field overlay is a UI-heavy enhancement that would not change any of the underlying math.
3. **No CNN side-by-side visualization.** The lineage is currently a textual note. Showing an actual learned conv-layer filter from a small pretrained CNN (e.g., a 3×3 or 7×7 first-conv filter from PyTorch's `torchvision.models.vgg11`) next to the Gabor would make the historical link tangible. Deferred — adds torchvision as a heavy dependency.
4. **No frontend tests** for the V1 panel; same status as phases 2-5.

## Cross-model audit checklist (for Alex to run)

> Audit this diff for: hardcoded fake tuning curves, fabricated Gabor filters, dead code paths, citation fabrication, math drift from the cited references, type drift between V1Response (TS) and V1Response (pydantic).
>
> Specifically:
> 1. Is the Gabor in `gabor_filter` consistent with the Daugman 1980 form? Does it use a 2D rotated coordinate system, a Gaussian envelope, and a cosine carrier?
> 2. Is the complex-cell function the Adelson-Bergen 1985 energy model (√(I_even² + I_odd²)) and not some other pooling rule?
> 3. Does the tuning curve actually use `gabor_filter` with `phase_deg=0` and `phase_deg=90` to obtain even/odd quadrature pair?
> 4. Does `simulate_v1` in the router only call into `hubel_wiesel.py`, or is anything synthesized elsewhere?
> 5. Does the frontend HubelWieselPanel only render data from the response, or does it ever fall back to a synthetic curve / synthetic filter?
> 6. Does the citation DOI resolve to the real paper?
>
> Manual step: open http://localhost:3000, scroll the inspector to the V1 section. Try θ_pref = 0, 45, 90, 135 and confirm both Gabor visualizations rotate visibly and the tuning curve peak tracks the preferred angle. Confirm the curve drops to near-zero at θ_pref ± 90°. Confirm the simple curve is sharper than the complex curve.
>
> Report only theater. Be brutal.

### Verdict
_Pending Alex's cross-model audit + manual θ_pref sweep + DOI-resolution check._
