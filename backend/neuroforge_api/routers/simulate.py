"""POST /api/simulate/hh — run a Hodgkin-Huxley step-current simulation."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from neuroforge_api.models.simulation import (
    CapacitySweepResponse,
    DopamineRPERequest,
    DopamineRPEResponse,
    HebbianRequest,
    HebbianResponse,
    HHRequest,
    HHResponse,
    HopfieldRequest,
    HopfieldResponse,
    MCPGateResponse,
    MCPXorSearchResponse,
    ModernHopfieldRequest,
    ModernHopfieldResponse,
    ReceptorKineticsModel,
    STDPRequest,
    STDPResponse,
    SynapseRequest,
    SynapseResponse,
    SynapseTraceModel,
    V1Request,
    V1Response,
)
from neuroforge_api.simulators import synapse as synapse_module
from neuroforge_api.simulators.dopamine_rpe import simulate_dopamine_rpe
from neuroforge_api.simulators.hebbian import simulate_hebbian
from neuroforge_api.simulators.hodgkin_huxley import simulate_hh
from neuroforge_api.simulators.hopfield import simulate_hopfield
from neuroforge_api.simulators.hubel_wiesel import (
    gabor_filter,
    orientation_tuning_curve,
)
from neuroforge_api.simulators.mcp import (
    GATES,
    evaluate_gate,
    search_xor_single_layer,
)
from neuroforge_api.simulators.modern_hopfield import (
    CLASSIC_CRITICAL_ALPHA,
    capacity_sweep,
    simulate_modern_hopfield,
)
from neuroforge_api.simulators.stdp import (
    A_MINUS,
    A_PLUS,
    TAU_MINUS_MS,
    TAU_PLUS_MS,
    simulate_stdp_pair,
    stdp_curve,
)

router = APIRouter(prefix="/api/simulate", tags=["simulate"])

HH_CITATION = (
    "Hodgkin AL, Huxley AF. A quantitative description of membrane current and "
    "its application to conduction and excitation in nerve. "
    "J Physiol. 1952;117(4):500-44. doi:10.1113/jphysiol.1952.sp004764"
)

STDP_CITATION = (
    "Bi GQ, Poo MM. Synaptic modifications in cultured hippocampal neurons: "
    "dependence on spike timing, synaptic strength, and postsynaptic cell type. "
    "J Neurosci. 1998;18(24):10464-72. doi:10.1523/JNEUROSCI.18-24-10464.1998"
)

V1_CITATION = (
    "Hubel DH, Wiesel TN. Receptive fields, binocular interaction and "
    "functional architecture in the cat's visual cortex. J Physiol. "
    "1962;160(1):106-54. doi:10.1113/jphysiol.1962.sp006837"
)

HEBBIAN_CITATION = (
    "Hebb DO. The Organization of Behavior. Wiley, 1949. "
    "Bliss TVP, Lømo T. Long-lasting potentiation of synaptic transmission "
    "in the dentate area of the anaesthetized rabbit following stimulation "
    "of the perforant path. J Physiol. 1973;232(2):331-356. "
    "doi:10.1113/jphysiol.1973.sp010273. "
    "Oja E. A simplified neuron model as a principal component analyzer. "
    "J Math Biol. 1982;15(3):267-273. doi:10.1007/BF00275687"
)

HOPFIELD_CITATION = (
    "Hopfield JJ. Neural networks and physical systems with emergent "
    "collective computational abilities. Proc Natl Acad Sci USA. "
    "1982;79(8):2554-2558. doi:10.1073/pnas.79.8.2554 (Nobel 2024). "
    "Capacity bound: Amit DJ, Gutfreund H, Sompolinsky H. Statistical "
    "mechanics of neural networks near saturation. Ann Phys. "
    "1987;173(1):30-67. doi:10.1016/0003-4916(87)90092-3"
)
HOPFIELD_CRITICAL_ALPHA = 0.138

MODERN_HOPFIELD_CITATION = (
    "Ramsauer H, Schäfl B, Lehner J, et al. Hopfield Networks is All You Need. "
    "ICLR 2021. doi:10.48550/arXiv.2008.02217 (update rule ≡ transformer attention). "
    "Krotov D, Hopfield JJ. Dense Associative Memory for Pattern Recognition. "
    "NeurIPS 2016. doi:10.48550/arXiv.1606.01164. "
    "Demircigil M, Heusel J, Löwe M, Upgang S, Vermet F. On a Model of Associative "
    "Memory with Huge Storage Capacity. J Stat Phys. 2017;168(2):288-299. "
    "doi:10.1007/s10955-017-1806-y (capacity exponential in d). "
    "Classic bound: Amit DJ, Gutfreund H, Sompolinsky H. Ann Phys. 1987;173(1):30-67. "
    "doi:10.1016/0003-4916(87)90092-3 (α_c ≈ 0.138)."
)

DOPAMINE_CITATION = (
    "Schultz W, Dayan P, Montague PR. A neural substrate of prediction and reward. "
    "Science. 1997;275(5306):1593-1599. doi:10.1126/science.275.5306.1593. "
    "Montague PR, Dayan P, Sejnowski TJ. A framework for mesencephalic dopamine "
    "systems based on predictive Hebbian learning. J Neurosci. 1996;16(5):1936-1947. "
    "doi:10.1523/JNEUROSCI.16-05-01936.1996. "
    "Sutton RS. Learning to predict by the methods of temporal differences. "
    "Mach Learn. 1988;3(1):9-44. doi:10.1007/BF00115009. "
    "Schultz W. Predictive reward signal of dopamine neurons. J Neurophysiol. "
    "1998;80(1):1-27. doi:10.1152/jn.1998.80.1.1. "
    "Distributional update: Dabney W, et al. Nature. 2020;577(7792):671-675. "
    "doi:10.1038/s41586-019-1924-6."
)

SYNAPSE_CITATION = (
    "Destexhe A, Mainen ZF, Sejnowski TJ. An efficient method for computing synaptic "
    "conductances based on a kinetic model of receptor binding. Neural Comput. "
    "1994;6(1):14-18. doi:10.1162/neco.1994.6.1.14. "
    "Jahr CE, Stevens CF. Voltage dependence of NMDA-activated macroscopic conductances "
    "predicted by single-channel kinetics. J Neurosci. 1990;10(9):3178-3182. "
    "doi:10.1523/JNEUROSCI.10-09-03178.1990. "
    "Collingridge GL, Kehl SJ, McLennan H. J Physiol. 1983;334(1):33-46. "
    "doi:10.1113/jphysiol.1983.sp014478 (NMDA receptor triggers LTP)."
)

MCP_CITATION = (
    "McCulloch WS, Pitts W. A logical calculus of the ideas immanent in "
    "nervous activity. Bull Math Biophys. 1943;5(4):115-133. "
    "doi:10.1007/BF02478259. "
    "Minsky M, Papert S. Perceptrons. MIT Press, 1969 (single-layer XOR "
    "impossibility). "
    "Rumelhart DE, Hinton GE, Williams RJ. Learning representations by "
    "back-propagating errors. Nature. 1986;323(6088):533-536. "
    "doi:10.1038/323533a0 (multi-layer escape)."
)


@router.post("/hh", response_model=HHResponse)
def run_hh(request: HHRequest) -> HHResponse:
    try:
        trace = simulate_hh(
            duration_ms=request.duration_ms,
            stimulus_uA=request.stimulus_uA,
            stimulus_start_ms=request.stimulus_start_ms,
            stimulus_end_ms=request.stimulus_end_ms,
            dt_ms=request.dt_ms,
            record_every_n=request.record_every_n,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return HHResponse(
        times_ms=trace.times_ms.tolist(),
        voltage_mV=trace.voltage_mV.tolist(),
        stimulus_uA=trace.stimulus_uA.tolist(),
        spike_times_ms=trace.spike_times_ms.tolist(),
        dt_ms=trace.dt_ms,
        citation=HH_CITATION,
    )


@router.post("/stdp", response_model=STDPResponse)
def run_stdp(request: STDPRequest) -> STDPResponse:
    if request.dt_max_ms <= request.dt_min_ms:
        raise HTTPException(status_code=422, detail="dt_max_ms must be > dt_min_ms")
    try:
        result = simulate_stdp_pair(request.dt_ms)
        grid, values = stdp_curve(
            dt_min_ms=request.dt_min_ms,
            dt_max_ms=request.dt_max_ms,
            points=request.curve_points,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return STDPResponse(
        dt_ms=result.dt_ms,
        observed_delta_w=result.delta_w,
        kernel_delta_w=result.kernel_dw,
        pre_spike_ms=result.pre_spike_ms,
        post_spike_ms=result.post_spike_ms,
        curve_dt_ms=grid.tolist(),
        curve_delta_w=values.tolist(),
        tau_plus_ms=TAU_PLUS_MS,
        tau_minus_ms=TAU_MINUS_MS,
        a_plus=A_PLUS,
        a_minus=A_MINUS,
        citation=STDP_CITATION,
    )


@router.get("/mcp/{gate_or_search}", response_model=None)
def run_mcp(gate_or_search: str):
    """Evaluate a McCulloch-Pitts gate by name, or run the XOR-search proof."""
    if gate_or_search.lower() == "xor-search":
        proof = search_xor_single_layer()
        return MCPXorSearchResponse(
            target=list(proof.target),
            weight_range=list(proof.weight_range),
            threshold_range=list(proof.threshold_range),
            step=proof.weight_step,
            combinations_tried=proof.combinations_tried,
            best_match_correct=proof.best_match_correct,
            best_weights=list(proof.best_weights) if proof.best_weights is not None else None,
            best_threshold=proof.best_threshold,
            no_solution=proof.no_solution,
            citation=MCP_CITATION,
        )
    name = gate_or_search.upper()
    if name not in GATES:
        raise HTTPException(
            status_code=404,
            detail=f"unknown gate '{gate_or_search}'; choices: {sorted(GATES)} or 'xor-search'",
        )
    result = evaluate_gate(name)
    return MCPGateResponse(
        name=result.name,
        description=result.description,
        n_inputs=result.n_inputs,
        weights=list(result.weights),
        threshold=result.threshold,
        inputs_table=result.inputs_table,
        expected=list(result.expected),
        produced=list(result.produced),
        passes=result.passes,
        citation=MCP_CITATION,
    )


@router.post("/hopfield", response_model=HopfieldResponse)
def run_hopfield(request: HopfieldRequest) -> HopfieldResponse:
    try:
        run = simulate_hopfield(
            n_neurons=request.n_neurons,
            n_patterns=request.n_patterns,
            corruption_fraction=request.corruption_fraction,
            target_index=request.target_index,
            max_sweeps=request.max_sweeps,
            seed=request.seed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return HopfieldResponse(
        n_neurons=run.n_neurons,
        n_patterns=run.n_patterns,
        target_index=run.target_index,
        target_capacity_alpha=run.target_capacity_alpha,
        critical_capacity=HOPFIELD_CRITICAL_ALPHA,
        target_pattern=run.patterns[run.target_index].astype(int).tolist(),
        corrupted_input=run.corrupted_input.astype(int).tolist(),
        final_state=run.states[-1].astype(int).tolist(),
        energies=run.energies.tolist(),
        overlaps_with_target=run.overlaps_with_target.tolist(),
        final_overlap=run.final_overlap,
        converged=run.converged,
        citation=HOPFIELD_CITATION,
    )


@router.post("/modern-hopfield", response_model=ModernHopfieldResponse)
def run_modern_hopfield(request: ModernHopfieldRequest) -> ModernHopfieldResponse:
    try:
        run = simulate_modern_hopfield(
            d=request.d,
            n_patterns=request.n_patterns,
            corruption_fraction=request.corruption_fraction,
            beta=request.beta,
            n_updates=request.n_updates,
            target_index=request.target_index,
            seed=request.seed,
        )
        sweep = None
        if request.sweep:
            s = capacity_sweep(
                d=request.d,
                n_trials=request.sweep_trials,
                corruption_fraction=request.corruption_fraction,
                beta=request.beta,
                seed=request.seed,
            )
            sweep = CapacitySweepResponse(
                d=s.d,
                alphas=s.alphas.tolist(),
                n_patterns=s.n_patterns.tolist(),
                classic_success=s.classic_success.tolist(),
                modern_success=s.modern_success.tolist(),
                n_trials=s.n_trials,
                threshold=s.threshold,
                corruption_fraction=s.corruption_fraction,
                beta=s.beta,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    final = run.modern_states[-1]
    return ModernHopfieldResponse(
        d=run.d,
        n_patterns=run.n_patterns,
        alpha=run.alpha,
        beta=run.beta,
        classic_critical_alpha=CLASSIC_CRITICAL_ALPHA,
        target_index=run.target_index,
        target=run.target.tolist(),
        corrupted=run.corrupted.tolist(),
        modern_final=final.tolist(),
        modern_final_sign=[1 if v >= 0 else -1 for v in final],
        modern_energies=run.modern_energies.tolist(),
        modern_overlaps=run.modern_overlaps.tolist(),
        modern_attention_weights=run.modern_attention_weights.tolist(),
        classic_final=run.classic_final.astype(int).tolist(),
        classic_overlap=run.classic_overlap,
        attention_max_abs_diff=run.attention_max_abs_diff,
        sweep=sweep,
        citation=MODERN_HOPFIELD_CITATION,
    )


@router.post("/dopamine-rpe", response_model=DopamineRPEResponse)
def run_dopamine_rpe(request: DopamineRPERequest) -> DopamineRPEResponse:
    try:
        r = simulate_dopamine_rpe(
            n_steps=request.n_steps,
            bin_ms=request.bin_ms,
            cue_step=request.cue_step,
            reward_step=request.reward_step,
            reward=request.reward,
            alpha=request.alpha,
            gamma=request.gamma,
            n_training_trials=request.n_training_trials,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DopamineRPEResponse(
        n_steps=r.n_steps,
        bin_ms=r.bin_ms,
        cue_step=r.cue_step,
        reward_step=r.reward_step,
        alpha=r.alpha,
        gamma=r.gamma,
        n_training_trials=r.n_training_trials,
        times_ms=r.times_ms.tolist(),
        delta_unpredicted=r.delta_unpredicted.tolist(),
        delta_predicted=r.delta_predicted.tolist(),
        delta_omitted=r.delta_omitted.tolist(),
        value_trained=r.value_trained.tolist(),
        delta_at_reward_per_trial=r.delta_at_reward_per_trial.tolist(),
        delta_at_cue_per_trial=r.delta_at_cue_per_trial.tolist(),
        parameter_note=(
            "Model form (TD(0), tapped-delay-line stimulus) is Montague 1996 / Schultz 1997. "
            f"Numerical constants are this demo's: learning rate α={r.alpha}, discount γ={r.gamma}, "
            f"{r.bin_ms:.0f} ms bins, cue at {r.cue_step * r.bin_ms:.0f} ms, reward at "
            f"{r.reward_step * r.bin_ms:.0f} ms, {r.n_training_trials} training trials. "
            "δ is the model's prediction error (dimensionless), not a fitted firing rate; the "
            "paper's claims reproduced are the SIGN and TIMING of δ in the three conditions."
        ),
        citation=DOPAMINE_CITATION,
    )


@router.post("/synapse", response_model=SynapseResponse)
def run_synapse(request: SynapseRequest) -> SynapseResponse:
    try:
        traces = [
            synapse_module.simulate_synapse(
                r.key,
                holding_mV=request.holding_mV,
                g_max_nS=request.g_max_nS,
                mg_mM=request.mg_mM,
                duration_ms=request.duration_ms,
                dt_ms=request.dt_ms,
                onset_ms=request.onset_ms,
            )
            for r in synapse_module.RECEPTORS
        ]
        v, i_mg, i_free = synapse_module.nmda_iv_curve(mg_mM=request.mg_mM)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SynapseResponse(
        times_ms=traces[0].times_ms.tolist(),
        holding_mV=request.holding_mV,
        mg_mM=request.mg_mM,
        g_max_nS=request.g_max_nS,
        receptors=[
            ReceptorKineticsModel(
                key=r.key,
                name=r.name,
                transmitter=r.transmitter,
                tau_rise_ms=r.tau_rise_ms,
                tau_decay_ms=r.tau_decay_ms,
                e_rev_mV=r.e_rev_mV,
                mg_block=r.mg_block,
                citation=r.citation,
            )
            for r in synapse_module.RECEPTORS
        ],
        traces=[
            SynapseTraceModel(
                key=t.key,
                conductance_nS=t.conductance_nS.tolist(),
                current_pA=t.current_pA.tolist(),
                block_fraction=t.block_fraction,
            )
            for t in traces
        ],
        nmda_iv_voltage_mV=v.tolist(),
        nmda_iv_with_mg_pA=i_mg.tolist(),
        nmda_iv_without_mg_pA=i_free.tolist(),
        citation=SYNAPSE_CITATION,
    )


@router.post("/hebbian", response_model=HebbianResponse)
def run_hebbian(request: HebbianRequest) -> HebbianResponse:
    record_every_n = max(1, request.n_iterations // 200)
    try:
        hebb = simulate_hebbian(
            rule="hebb",
            n_iterations=request.n_iterations,
            learning_rate=request.learning_rate,
            correlation=request.correlation,
            input_dim=request.input_dim,
            seed=request.seed,
            record_every_n=record_every_n,
        )
        oja = simulate_hebbian(
            rule="oja",
            n_iterations=request.n_iterations,
            learning_rate=request.learning_rate,
            correlation=request.correlation,
            input_dim=request.input_dim,
            seed=request.seed,
            record_every_n=record_every_n,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return HebbianResponse(
        iterations=hebb.iterations.tolist(),
        hebb_norm=hebb.weight_norm.tolist(),
        hebb_angle_deg=hebb.weight_angle_deg.tolist(),
        oja_norm=oja.weight_norm.tolist(),
        oja_angle_deg=oja.weight_angle_deg.tolist(),
        principal_direction=hebb.principal_direction.tolist(),
        final_hebb_weight=hebb.final_weight.tolist(),
        final_oja_weight=oja.final_weight.tolist(),
        citation=HEBBIAN_CITATION,
    )


@router.post("/v1", response_model=V1Response)
def run_v1(request: V1Request) -> V1Response:
    sigma_px = request.sigma_px if request.sigma_px is not None else 1.0 / request.spatial_frequency_cyc_per_px
    try:
        even = gabor_filter(
            image_size=request.image_size,
            orientation_deg=request.preferred_orientation_deg,
            spatial_frequency_cyc_per_px=request.spatial_frequency_cyc_per_px,
            phase_deg=0.0,
            sigma_px=sigma_px,
        )
        odd = gabor_filter(
            image_size=request.image_size,
            orientation_deg=request.preferred_orientation_deg,
            spatial_frequency_cyc_per_px=request.spatial_frequency_cyc_per_px,
            phase_deg=90.0,
            sigma_px=sigma_px,
        )
        tc = orientation_tuning_curve(
            preferred_orientation_deg=request.preferred_orientation_deg,
            spatial_frequency_cyc_per_px=request.spatial_frequency_cyc_per_px,
            image_size=request.image_size,
            n_orientations=request.n_orientations,
            sigma_px=sigma_px,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return V1Response(
        preferred_orientation_deg=request.preferred_orientation_deg,
        spatial_frequency_cyc_per_px=request.spatial_frequency_cyc_per_px,
        image_size=request.image_size,
        sigma_px=float(sigma_px),
        gabor_even=even.tolist(),
        gabor_odd=odd.tolist(),
        tuning_orientations_deg=tc.orientations_deg.tolist(),
        tuning_simple=tc.simple_responses.tolist(),
        tuning_complex=tc.complex_responses.tolist(),
        citation=V1_CITATION,
    )
