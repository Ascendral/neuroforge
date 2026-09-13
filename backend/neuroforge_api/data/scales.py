"""The multi-scale graph — human brain and AI system on one shared ladder of scales.

    level 1   organ            ↔   deployed system
    level 2   region/network   ↔   architecture (stack of blocks)
    level 3   circuit          ↔   block internals (attention / MLP / residual)
    level 4   cell             ↔   unit (artificial neuron / feature)
    level 5   synapse/molecule ↔   parameter (weight / gradient / activation)

Every node says what the thing IS (description), what it DOES (function) and
HOW (mechanism), cites its sources, and — where there is one — names its
analog on the other side with an honest evidence tag:

    equivalence  the two are the same mathematics (proved)
    strong       quantitative or causal evidence the two compute alike
    analogy      a useful conceptual parallel, not a demonstrated mechanism
    none         no known counterpart (the disanalogy is itself the fact)

Brain nodes carry atlas anchors (Harvard-Oxford labels, Pauli 2017 nuclei,
Diedrichsen cerebellum) so the 3D viewer can light them up, and a NeuroMorpho
query where real reconstructed cells exist. Nodes with a `widget` open a live
simulator from neuroforge_api.simulators.

Anti-theater: every DOI here is resolved by scripts/verify_dois.py. Numbers
are quoted with the paper they come from. Nothing is a placeholder.
"""

from __future__ import annotations

from dataclasses import dataclass

STRENGTHS = ("equivalence", "strong", "analogy", "none")


@dataclass(frozen=True, slots=True)
class Cite:
    text: str
    doi: str | None = None


@dataclass(frozen=True, slots=True)
class Analog:
    target: str              # node id on the OTHER side
    strength: str            # one of STRENGTHS
    note: str
    cites: tuple[Cite, ...] = ()


@dataclass(frozen=True, slots=True)
class Fact:
    label: str
    value: str
    cite: Cite


@dataclass(frozen=True, slots=True)
class Node:
    id: str
    side: str                # "brain" | "ai"
    level: int               # 1..5
    name: str
    parent: str | None
    group: str               # layout group (brain: cortex/subcortex/…; ai: inference/training/augmentation)
    description: str         # what it is
    function: str            # what it does
    mechanism: str           # how it does it
    cites: tuple[Cite, ...]
    analogs: tuple[Analog, ...] = ()
    no_analog_note: str | None = None
    facts: tuple[Fact, ...] = ()
    ho_labels: tuple[str, ...] = ()        # Harvard-Oxford cortical/subcortical labels
    pauli: tuple[str, ...] = ()            # Pauli 2017 nucleus abbrevs
    cerebellum: bool = False               # Diedrichsen 2009 whole-cerebellum anchor
    neuromorpho: dict[str, str] | None = None   # {"region": …, "cell_type": …}
    widget: str | None = None              # simulator id
    order: int = 0                         # display order within (side, level)


@dataclass(frozen=True, slots=True)
class Edge:
    source: str
    target: str
    kind: str                # projects_to | data_flow | modulates | gradient | teaches
    note: str
    cite: Cite | None = None


@dataclass(frozen=True, slots=True)
class Level:
    level: int
    brain_name: str
    ai_name: str
    brain_blurb: str
    ai_blurb: str


LEVELS: tuple[Level, ...] = (
    Level(1, "organ", "system",
          "The whole brain: ~86 billion neurons in one 1.3 kg organ.",
          "A deployed model: weights + inference runtime + memory + sampling."),
    Level(2, "region / network", "architecture",
          "Cortical areas, subcortical nuclei and the large-scale networks they form.",
          "The stack: embedding → N transformer blocks → unembedding, plus the training loop."),
    Level(3, "circuit", "block",
          "Wiring motifs that repeat across the brain — columns, loops, relays.",
          "What is inside one block: attention heads, the MLP, the residual stream."),
    Level(4, "cell", "unit",
          "Neuron types: what each computes and how it fires.",
          "The artificial neuron and the features it represents."),
    Level(5, "synapse / molecule", "parameter",
          "Receptors, channels, vesicles, plasticity — where learning physically happens.",
          "Weights, gradients, activations — where learning numerically happens."),
)

# ---------------------------------------------------------------------------
# Shared citations
# ---------------------------------------------------------------------------
AZEVEDO = Cite("Azevedo FAC, et al. Equal numbers of neuronal and nonneuronal cells make the human brain an isometrically scaled-up primate brain. J Comp Neurol. 2009;513(5):532-541.", "10.1002/cne.21974")
HERCULANO = Cite("Herculano-Houzel S. The human brain in numbers: a linearly scaled-up primate brain. Front Hum Neurosci. 2009;3:31.", "10.3389/neuro.09.031.2009")
ATTWELL = Cite("Attwell D, Laughlin SB. An energy budget for signaling in the grey matter of the brain. J Cereb Blood Flow Metab. 2001;21(10):1133-1145.", "10.1097/00004647-200110000-00001")
FELLEMAN = Cite("Felleman DJ, Van Essen DC. Distributed hierarchical processing in the primate cerebral cortex. Cereb Cortex. 1991;1(1):1-47.", "10.1093/cercor/1.1.1")
YEO = Cite("Yeo BTT, et al. The organization of the human cerebral cortex estimated by intrinsic functional connectivity. J Neurophysiol. 2011;106(3):1125-1165.", "10.1152/jn.00338.2011")
RAICHLE = Cite("Raichle ME, et al. A default mode of brain function. PNAS. 2001;98(2):676-682.", "10.1073/pnas.98.2.676")
AMARAL = Cite("Amaral DG, Witter MP. The three-dimensional organization of the hippocampal formation: a review of anatomical data. Neuroscience. 1989;31(3):571-591.", "10.1016/0306-4522(89)90424-7")
MARR71 = Cite("Marr D. Simple memory: a theory for archicortex. Phil Trans R Soc B. 1971;262(841):23-81.", "10.1098/rstb.1971.0078")
TREVES = Cite("Treves A, Rolls ET. Computational analysis of the role of the hippocampus in memory. Hippocampus. 1994;4(3):374-391.", "10.1002/hipo.450040319")
OKEEFE = Cite("O'Keefe J, Dostrovsky J. The hippocampus as a spatial map. Brain Res. 1971;34(1):171-175.", "10.1016/0006-8993(71)90358-1")
HAFTING = Cite("Hafting T, Fyhn M, Molden S, Moser MB, Moser EI. Microstructure of a spatial map in the entorhinal cortex. Nature. 2005;436(7052):801-806.", "10.1038/nature03721")
ALEXANDER = Cite("Alexander GE, DeLong MR, Strick PL. Parallel organization of functionally segregated circuits linking basal ganglia and cortex. Annu Rev Neurosci. 1986;9:357-381.", "10.1146/annurev.ne.09.030186.002041")
REDGRAVE = Cite("Redgrave P, Prescott TJ, Gurney K. The basal ganglia: a vertebrate solution to the selection problem? Neuroscience. 1999;89(4):1009-1023.", "10.1016/S0306-4522(98)00319-4")
SCHULTZ97 = Cite("Schultz W, Dayan P, Montague PR. A neural substrate of prediction and reward. Science. 1997;275(5306):1593-1599.", "10.1126/science.275.5306.1593")
SCHULTZ98 = Cite("Schultz W. Predictive reward signal of dopamine neurons. J Neurophysiol. 1998;80(1):1-27.", "10.1152/jn.1998.80.1.1")
MONTAGUE = Cite("Montague PR, Dayan P, Sejnowski TJ. A framework for mesencephalic dopamine systems based on predictive Hebbian learning. J Neurosci. 1996;16(5):1936-1947.", "10.1523/JNEUROSCI.16-05-01936.1996")
SUTTON = Cite("Sutton RS. Learning to predict by the methods of temporal differences. Mach Learn. 1988;3(1):9-44.", "10.1007/BF00115009")
DABNEY = Cite("Dabney W, et al. A distributional code for value in dopamine-based reinforcement learning. Nature. 2020;577(7792):671-675.", "10.1038/s41586-019-1924-6")
MARR69 = Cite("Marr D. A theory of cerebellar cortex. J Physiol. 1969;202(2):437-470.", "10.1113/jphysiol.1969.sp008820")
ITO = Cite("Ito M. Cerebellar control of the vestibulo-ocular reflex — around the flocculus hypothesis. Annu Rev Neurosci. 1982;5:275-297.", "10.1146/annurev.ne.05.030182.001423")
SHERMAN = Cite("Sherman SM. Thalamus plays a central role in ongoing cortical functioning. Nat Neurosci. 2016;19(4):533-541.", "10.1038/nn.4269")
HUBEL = Cite("Hubel DH, Wiesel TN. Receptive fields, binocular interaction and functional architecture in the cat's visual cortex. J Physiol. 1962;160(1):106-154.", "10.1113/jphysiol.1962.sp006837")
OLSHAUSEN = Cite("Olshausen BA, Field DJ. Emergence of simple-cell receptive field properties by learning a sparse code for natural images. Nature. 1996;381(6583):607-609.", "10.1038/381607a0")
GOLDMAN = Cite("Goldman-Rakic PS. Cellular basis of working memory. Neuron. 1995;14(3):477-485.", "10.1016/0896-6273(95)90304-6")
FUNAHASHI = Cite("Funahashi S, Bruce CJ, Goldman-Rakic PS. Mnemonic coding of visual space in the monkey's dorsolateral prefrontal cortex. J Neurophysiol. 1989;61(2):331-349.", "10.1152/jn.1989.61.2.331")
WONGWANG = Cite("Wong KF, Wang XJ. A recurrent network mechanism of time integration in perceptual decisions. J Neurosci. 2006;26(4):1314-1328.", "10.1523/JNEUROSCI.3733-05.2006")
DOUGLAS = Cite("Douglas RJ, Martin KAC. Neuronal circuits of the neocortex. Annu Rev Neurosci. 2004;27:419-451.", "10.1146/annurev.neuro.27.070203.144152")
MOUNTCASTLE = Cite("Mountcastle VB. Modality and topographic properties of single neurons of cat's somatic sensory cortex. J Neurophysiol. 1957;20(4):408-434.", "10.1152/jn.1957.20.4.408")
MARKRAM = Cite("Markram H, et al. Reconstruction and simulation of neocortical microcircuitry. Cell. 2015;163(2):456-492.", "10.1016/j.cell.2015.09.029")
H01 = Cite("Shapson-Coe A, et al. A petavoxel fragment of human cerebral cortex reconstructed at nanoscale resolution. Science. 2024;384(6696):eadk4858.", "10.1126/science.adk4858")
MICRONS = Cite("MICrONS Consortium. Functional connectomics spanning multiple areas of mouse visual cortex. Nature. 2025;640:435-447.", "10.1038/s41586-025-08790-w")
TREMBLAY = Cite("Tremblay R, Lee S, Rudy B. GABAergic interneurons in the neocortex: from cellular properties to circuits. Neuron. 2016;91(2):260-292.", "10.1016/j.neuron.2016.06.033")
CONNORS = Cite("Connors BW, Gutnick MJ. Intrinsic firing patterns of diverse neocortical neurons. Trends Neurosci. 1990;13(3):99-104.", "10.1016/0166-2236(90)90185-D")
LARKUM = Cite("Larkum M. A cellular mechanism for cortical associations: an organizing principle for the cerebral cortex. Trends Neurosci. 2013;36(3):141-151.", "10.1016/j.tins.2012.11.006")
POLSKY = Cite("Polsky A, Mel BW, Schiller J. Computational subunits in thin dendrites of pyramidal cells. Nat Neurosci. 2004;7(6):621-627.", "10.1038/nn1253")
LONDON = Cite("London M, Häusser M. Dendritic computation. Annu Rev Neurosci. 2005;28:503-532.", "10.1146/annurev.neuro.28.061604.135703")
BENIAGUEV = Cite("Beniaguev D, Segev I, London M. Single cortical neurons as deep artificial neural networks. Neuron. 2021;109(17):2727-2739.", "10.1016/j.neuron.2021.07.002")
SILETTI = Cite("Siletti K, et al. Transcriptomic diversity of cell types across the adult human brain. Science. 2023;382(6667):eadd7046.", "10.1126/science.add7046")
QUIROGA = Cite("Quiroga RQ, Reddy L, Kreiman G, Koch C, Fried I. Invariant visual representation by single neurons in the human brain. Nature. 2005;435(7045):1102-1107.", "10.1038/nature03687")
HH = Cite("Hodgkin AL, Huxley AF. A quantitative description of membrane current and its application to conduction and excitation in nerve. J Physiol. 1952;117(4):500-544.", "10.1113/jphysiol.1952.sp004764")
CATTERALL = Cite("Catterall WA. From ionic currents to molecular mechanisms: the structure and function of voltage-gated sodium channels. Neuron. 2000;26(1):13-25.", "10.1016/S0896-6273(00)81133-2")
NEHER = Cite("Neher E, Sakmann B. Single-channel currents recorded from membrane of denervated frog muscle fibres. Nature. 1976;260(5554):799-802.", "10.1038/260799a0")
DESTEXHE = Cite("Destexhe A, Mainen ZF, Sejnowski TJ. An efficient method for computing synaptic conductances based on a kinetic model of receptor binding. Neural Comput. 1994;6(1):14-18.", "10.1162/neco.1994.6.1.14")
JAHR = Cite("Jahr CE, Stevens CF. Voltage dependence of NMDA-activated macroscopic conductances predicted by single-channel kinetics. J Neurosci. 1990;10(9):3178-3182.", "10.1523/JNEUROSCI.10-09-03178.1990")
COLLINGRIDGE = Cite("Collingridge GL, Kehl SJ, McLennan H. Excitatory amino acids in synaptic transmission in the Schaffer collateral-commissural pathway of the rat hippocampus. J Physiol. 1983;334(1):33-46.", "10.1113/jphysiol.1983.sp014478")
BLISS = Cite("Bliss TVP, Lømo T. Long-lasting potentiation of synaptic transmission in the dentate area of the anaesthetized rabbit following stimulation of the perforant path. J Physiol. 1973;232(2):331-356.", "10.1113/jphysiol.1973.sp010273")
MALENKA = Cite("Malenka RC, Bear MF. LTP and LTD: an embarrassment of riches. Neuron. 2004;44(1):5-21.", "10.1016/j.neuron.2004.09.012")
BIPOO = Cite("Bi GQ, Poo MM. Synaptic modifications in cultured hippocampal neurons: dependence on spike timing, synaptic strength, and postsynaptic cell type. J Neurosci. 1998;18(24):10464-10472.", "10.1523/JNEUROSCI.18-24-10464.1998")
SUDHOF = Cite("Südhof TC. Neurotransmitter release: the last millisecond in the life of a synaptic vesicle. Neuron. 2013;80(3):675-690.", "10.1016/j.neuron.2013.10.022")
KATZ = Cite("Fatt P, Katz B. Spontaneous subthreshold activity at motor nerve endings. J Physiol. 1952;117(1):109-128.", "10.1113/jphysiol.1952.sp004735")
TSODYKS = Cite("Tsodyks MV, Markram H. The neural code between neocortical pyramidal neurons depends on neurotransmitter release probability. PNAS. 1997;94(2):719-723.", "10.1073/pnas.94.2.719")
KANDEL = Cite("Kandel ER. The molecular biology of memory storage: a dialogue between genes and synapses. Science. 2001;294(5544):1030-1038.", "10.1126/science.1067020")
HANSEN = Cite("Hansen JY, et al. Mapping neurotransmitter systems to the structural and functional organization of the human neocortex. Nat Neurosci. 2022;25(11):1569-1581.", "10.1038/s41593-022-01186-3")
HAWRYLYCZ = Cite("Hawrylycz MJ, et al. An anatomically comprehensive atlas of the adult human brain transcriptome. Nature. 2012;489(7416):391-399.", "10.1038/nature11405")
TURRIGIANO = Cite("Turrigiano GG, et al. Activity-dependent scaling of quantal amplitude in neocortical neurons. Nature. 1998;391(6670):892-896.", "10.1038/36103")
HUTTENLOCHER = Cite("Huttenlocher PR. Synaptic density in human frontal cortex — developmental changes and effects of aging. Brain Res. 1979;163(2):195-205.", "10.1016/0006-8993(79)90349-4")
WILSON = Cite("Wilson MA, McNaughton BL. Reactivation of hippocampal ensemble memories during sleep. Science. 1994;265(5172):676-679.", "10.1126/science.8036517")
MCCLELLAND = Cite("McClelland JL, McNaughton BL, O'Reilly RC. Why there are complementary learning systems in the hippocampus and neocortex. Psychol Rev. 1995;102(3):419-457.", "10.1037/0033-295X.102.3.419")
KANWISHER = Cite("Kanwisher N, McDermott J, Chun MM. The fusiform face area: a module in human extrastriate cortex specialized for face perception. J Neurosci. 1997;17(11):4302-4311.", "10.1523/JNEUROSCI.17-11-04302.1997")
PATTERSON = Cite("Patterson K, Nestor PJ, Rogers TT. Where do you know what you know? The representation of semantic knowledge in the human brain. Nat Rev Neurosci. 2007;8(12):976-987.", "10.1038/nrn2277")
HUTH = Cite("Huth AG, et al. Natural speech reveals the semantic maps that tile human cerebral cortex. Nature. 2016;532(7600):453-458.", "10.1038/nature17637")
DEHAENE = Cite("Dehaene S, Kerszberg M, Changeux JP. A neuronal model of a global workspace in effortful cognitive tasks. PNAS. 1998;95(24):14529-14534.", "10.1073/pnas.95.24.14529")
CARANDINI = Cite("Carandini M, Heeger DJ. Normalization as a canonical neural computation. Nat Rev Neurosci. 2012;13(1):51-62.", "10.1038/nrn3136")
YAMINS = Cite("Yamins DLK, et al. Performance-optimized hierarchical models predict neural responses in higher visual cortex. PNAS. 2014;111(23):8619-8624.", "10.1073/pnas.1403112111")
SCHRIMPF = Cite("Schrimpf M, et al. The neural architecture of language: integrative modeling converges on predictive processing. PNAS. 2021;118(45):e2105646118.", "10.1073/pnas.2105646118")
GOLDSTEIN = Cite("Goldstein A, et al. Shared computational principles for language processing in humans and deep language models. Nat Neurosci. 2022;25(3):369-380.", "10.1038/s41593-022-01026-4")
RAO = Cite("Rao RPN, Ballard DH. Predictive coding in the visual cortex. Nat Neurosci. 1999;2(1):79-87.", "10.1038/4580")
FRISTON = Cite("Friston K. The free-energy principle: a unified brain theory? Nat Rev Neurosci. 2010;11(2):127-138.", "10.1038/nrn2787")
LILLICRAP = Cite("Lillicrap TP, Santoro A, Marris L, Akerman CJ, Hinton G. Backpropagation and the brain. Nat Rev Neurosci. 2020;21(6):335-346.", "10.1038/s41583-020-0277-3")
SACRAMENTO = Cite("Sacramento J, Costa RP, Bengio Y, Senn W. Dendritic cortical microcircuits approximate the backpropagation algorithm. NeurIPS 2018.", "10.48550/arXiv.1810.11393")
FRANK = Cite("Frank MC. Bridging the data gap between children and large language models. Trends Cogn Sci. 2023;27(11):990-992.", "10.1016/j.tics.2023.08.007")
ZADOR = Cite("Zador AM. A critique of pure learning and what artificial neural networks can learn from animal brains. Nat Commun. 2019;10:3770.", "10.1038/s41467-019-11786-6")
MNIH = Cite("Mnih V, et al. Human-level control through deep reinforcement learning. Nature. 2015;518(7540):529-533.", "10.1038/nature14236")
WHITTINGTON20 = Cite("Whittington JCR, et al. The Tolman-Eichenbaum Machine: unifying space and relational memory through generalization in the hippocampal formation. Cell. 2020;183(5):1249-1263.", "10.1016/j.cell.2020.10.024")
WHITTINGTON22 = Cite("Whittington JCR, Warren J, Behrens TEJ. Relating transformers to models and neural representations of the hippocampal formation. ICLR 2022.", "10.48550/arXiv.2112.04035")
BANINO = Cite("Banino A, et al. Vector-based navigation using grid-like representations in artificial agents. Nature. 2018;557(7705):429-433.", "10.1038/s41586-018-0102-6")
STRINGER = Cite("Stringer C, Pachitariu M, Steinmetz N, Carandini M, Harris KD. High-dimensional geometry of population responses in visual cortex. Nature. 2019;571(7765):361-365.", "10.1038/s41586-019-1346-5")
MCP = Cite("McCulloch WS, Pitts W. A logical calculus of the ideas immanent in nervous activity. Bull Math Biophys. 1943;5(4):115-133.", "10.1007/BF02478259")
ROSENBLATT = Cite("Rosenblatt F. The perceptron: a probabilistic model for information storage and organization in the brain. Psychol Rev. 1958;65(6):386-408.", "10.1037/h0042519")
RUMELHART = Cite("Rumelhart DE, Hinton GE, Williams RJ. Learning representations by back-propagating errors. Nature. 1986;323(6088):533-536.", "10.1038/323533a0")
HOPFIELD = Cite("Hopfield JJ. Neural networks and physical systems with emergent collective computational abilities. PNAS. 1982;79(8):2554-2558.", "10.1073/pnas.79.8.2554")
RAMSAUER = Cite("Ramsauer H, et al. Hopfield Networks is All You Need. ICLR 2021.", "10.48550/arXiv.2008.02217")
KROTOV = Cite("Krotov D, Hopfield JJ. Dense associative memory for pattern recognition. NeurIPS 2016.", "10.48550/arXiv.1606.01164")
DEMIRCIGIL = Cite("Demircigil M, et al. On a model of associative memory with huge storage capacity. J Stat Phys. 2017;168(2):288-299.", "10.1007/s10955-017-1806-y")
VASWANI = Cite("Vaswani A, et al. Attention is all you need. NeurIPS 2017.", "10.48550/arXiv.1706.03762")
BROWN = Cite("Brown TB, et al. Language models are few-shot learners. NeurIPS 2020.", "10.48550/arXiv.2005.14165")
OUYANG = Cite("Ouyang L, et al. Training language models to follow instructions with human feedback. NeurIPS 2022.", "10.48550/arXiv.2203.02155")
GEVA = Cite("Geva M, Schuster R, Berant J, Levy O. Transformer feed-forward layers are key-value memories. EMNLP 2021.", "10.48550/arXiv.2012.14913")
ELHAGE = Cite("Elhage N, et al. Toy models of superposition. Transformer Circuits Thread, 2022.", "10.48550/arXiv.2209.10652")
OLSSON = Cite("Olsson C, et al. In-context learning and induction heads. Transformer Circuits Thread, 2022.", "10.48550/arXiv.2209.11895")
SU = Cite("Su J, et al. RoFormer: enhanced transformer with rotary position embedding. 2021.", "10.48550/arXiv.2104.09864")
BA = Cite("Ba JL, Kiros JR, Hinton GE. Layer normalization. 2016.", "10.48550/arXiv.1607.06450")
HE = Cite("He K, Zhang X, Ren S, Sun J. Deep residual learning for image recognition. CVPR 2016.", "10.1109/CVPR.2016.90")
SHAZEER = Cite("Shazeer N, et al. Outrageously large neural networks: the sparsely-gated mixture-of-experts layer. ICLR 2017.", "10.48550/arXiv.1701.06538")
FEDUS = Cite("Fedus W, Zoph B, Shazeer N. Switch Transformers: scaling to trillion parameter models with simple and efficient sparsity. JMLR 2022.", "10.48550/arXiv.2101.03961")
LEWIS = Cite("Lewis P, et al. Retrieval-augmented generation for knowledge-intensive NLP tasks. NeurIPS 2020.", "10.48550/arXiv.2005.11401")
SRIVASTAVA = Cite("Srivastava N, Hinton G, Krizhevsky A, Sutskever I, Salakhutdinov R. Dropout: a simple way to prevent neural networks from overfitting. JMLR. 2014;15:1929-1958. (no DOI registered)", None)
KINGMA = Cite("Kingma DP, Ba J. Adam: a method for stochastic optimization. ICLR 2015.", "10.48550/arXiv.1412.6980")
HENDRYCKS = Cite("Hendrycks D, Gimpel K. Gaussian error linear units (GELUs). 2016.", "10.48550/arXiv.1606.08415")
NAIR = Cite("Nair V, Hinton GE. Rectified linear units improve restricted Boltzmann machines. ICML 2010. (no DOI registered)", None)
BRICKEN = Cite("Cunningham H, Ewart A, Riggs L, Huben R, Sharkey L. Sparse autoencoders find highly interpretable features in language models. 2023.", "10.48550/arXiv.2309.08600")
LECUN = Cite("LeCun Y, Bengio Y, Hinton G. Deep learning. Nature. 2015;521(7553):436-444.", "10.1038/nature14539")
HASSABIS = Cite("Hassabis D, Kumaran D, Summerfield C, Botvinick M. Neuroscience-inspired artificial intelligence. Neuron. 2017;95(2):245-258.", "10.1016/j.neuron.2017.06.011")
RICHARDS = Cite("Richards BA, et al. A deep learning framework for neuroscience. Nat Neurosci. 2019;22(11):1761-1770.", "10.1038/s41593-019-0520-2")
DORKENWALD = Cite("Dorkenwald S, et al. Neuronal wiring diagram of an adult brain. Nature. 2024;634:124-138.", "10.1038/s41586-024-07558-y")
IBL = Cite("International Brain Laboratory. A brain-wide map of neural activity during complex behaviour. Nature. 2025.", "10.1038/s41586-025-09235-0")

# ---------------------------------------------------------------------------
# BRAIN
# ---------------------------------------------------------------------------
BRAIN: tuple[Node, ...] = (
    # ---- level 1 -----------------------------------------------------------
    Node(
        id="brain.organ", side="brain", level=1, name="Human brain", parent=None, group="organ",
        description="One organ of ~86 billion neurons and about as many glia, wired by ~10¹⁴ synapses into cortex, subcortical nuclei, cerebellum and brainstem.",
        function="Perception, memory, decision, movement, language, homeostasis — everything below is a part of this.",
        mechanism="Electrochemical signalling: spikes along axons, chemical transmission at synapses, slow neuromodulation broadcast by a few thousand brainstem neurons.",
        cites=(AZEVEDO, HERCULANO, ATTWELL, IBL),
        facts=(
            Fact("neurons", "86.1 ± 8.1 billion", AZEVEDO),
            Fact("non-neuronal cells", "84.6 ± 9.8 billion", AZEVEDO),
            Fact("cortical neurons", "16.3 billion (19% of all neurons)", AZEVEDO),
            Fact("cerebellar neurons", "69.0 billion (80% of all neurons)", AZEVEDO),
            Fact("signalling energy", "action potentials + postsynaptic currents dominate the grey-matter ATP budget", ATTWELL),
            Fact("largest complete connectome", "adult Drosophila: 139,255 neurons, ~50 M synapses (2024) — no vertebrate brain is fully mapped", DORKENWALD),
        ),
        analogs=(Analog("ai.system", "analogy",
                        "Both are the top of their ladder, but the parts differ in kind: a brain is 10¹⁴ analog synapses in 1.3 kg at ~20 W; a model is 10¹¹-10¹² digital weights on data-center hardware. Nothing about the whole is proved equivalent.",
                        (HASSABIS, RICHARDS)),),
        order=0,
    ),
    # ---- level 2: regions / networks --------------------------------------
    Node(
        id="brain.region.cortex", side="brain", level=2, name="Neocortex", parent="brain.organ", group="cortex",
        description="The 2-4 mm six-layered sheet covering the hemispheres; ~16 billion neurons organized into ~180 areas per hemisphere and repeating columns.",
        function="Sensation, perception, action planning, language, working memory, abstract thought — the substrate of most 'cognitive functions'.",
        mechanism="Areas are wired into a hierarchy (Felleman & Van Essen: 32 visual areas, 10 levels). Feedforward paths carry sensory drive up; feedback paths carry predictions down.",
        cites=(FELLEMAN, AZEVEDO, DOUGLAS),
        ho_labels=("Frontal Pole", "Precentral Gyrus", "Postcentral Gyrus", "Superior Parietal Lobule", "Intracalcarine Cortex", "Superior Temporal Gyrus, posterior division"),
        facts=(Fact("neurons", "16.3 billion", AZEVEDO), Fact("hierarchy", "32 visual areas in ~10 levels", FELLEMAN)),
        analogs=(Analog("ai.arch.blocks", "strong",
                        "Deep networks trained only for object recognition predict single-neuron responses along the ventral stream, layer-for-area (Yamins 2014); next-word models predict human language-cortex fMRI/ECoG (Schrimpf 2021, Goldstein 2022). Hierarchical depth is shared; the layers are not the same thing.",
                        (YAMINS, SCHRIMPF, GOLDSTEIN)),),
        order=0,
    ),
    Node(
        id="brain.region.networks", side="brain", level=2, name="Large-scale functional networks", parent="brain.organ", group="cortex",
        description="Sets of distant cortical regions whose activity rises and falls together at rest — 7 (or 17) reproducible networks across 1,000 subjects.",
        function="Default mode (self-referential thought, memory), dorsal attention, salience, frontoparietal control, visual, somatomotor, limbic.",
        mechanism="Measured with resting-state fMRI correlation; supported by direct anatomical connections and shared neuromodulator input.",
        cites=(YEO, RAICHLE),
        ho_labels=("Precuneous Cortex", "Cingulate Gyrus, posterior division", "Frontal Medial Cortex", "Angular Gyrus"),
        analogs=(Analog("ai.aug.moe", "analogy",
                        "Both route work to specialized subsets; but MoE experts are selected per token by a learned gate, while brain networks are anatomically fixed and co-activate over seconds.",
                        (SHAZEER, YEO)),),
        order=1,
    ),
    Node(
        id="brain.region.prefrontal", side="brain", level=2, name="Prefrontal cortex", parent="brain.region.cortex", group="cortex",
        description="Frontal cortex anterior to motor areas; the largest cortical expansion in humans.",
        function="Working memory, planning, rule use, inhibition of prepotent responses.",
        mechanism="Neurons hold information across delays via persistent firing sustained by recurrent excitation (Goldman-Rakic 1995).",
        cites=(GOLDMAN, FUNAHASHI),
        ho_labels=("Frontal Pole", "Middle Frontal Gyrus", "Superior Frontal Gyrus"),
        neuromorpho={"region": "prefrontal", "cell_type": "pyramidal"},
        analogs=(Analog("ai.aug.kvcache", "analogy",
                        "Both keep recent context available for the current step. PFC does it with reverberating activity for seconds; the KV cache stores exact past keys/values in memory for the whole context window.",
                        (GOLDMAN,)),),
        order=2,
    ),
    Node(
        id="brain.region.motor", side="brain", level=2, name="Motor cortex", parent="brain.region.cortex", group="cortex",
        description="Precentral gyrus; layer-5 Betz cells send axons directly to spinal cord.",
        function="Generates voluntary movement commands; somatotopically organized (Penfield's homunculus).",
        mechanism="Population activity encodes movement direction and dynamics; the corticospinal tract carries it down.",
        cites=(Cite("Penfield W, Boldrey E. Somatic motor and sensory representation in the cerebral cortex of man as studied by electrical stimulation. Brain. 1937;60(4):389-443.", "10.1093/brain/60.4.389"),),
        ho_labels=("Precentral Gyrus",),
        neuromorpho={"region": "primary motor", "cell_type": "pyramidal"},
        analogs=(Analog("ai.arch.sampler", "analogy",
                        "The output stage: motor cortex commits the body to one action, the sampler commits the model to one token.",
                        (REDGRAVE,)),),
        order=3,
    ),
    Node(
        id="brain.region.hippocampus", side="brain", level=2, name="Hippocampal formation", parent="brain.organ", group="subcortex",
        description="Entorhinal cortex, dentate gyrus, CA3, CA1, subiculum — folded medial temporal cortex.",
        function="Episodic memory formation, spatial navigation (place cells, grid cells in entorhinal cortex), rapid one-shot learning.",
        mechanism="A recurrent CA3 network stores patterns by Hebbian plasticity and completes them from partial cues; replay during sleep consolidates them to neocortex.",
        cites=(AMARAL, OKEEFE, HAFTING, MARR71),
        ho_labels=("Left Hippocampus", "Right Hippocampus", "Parahippocampal Gyrus, anterior division"),
        neuromorpho={"region": "hippocampus", "cell_type": "pyramidal"},
        analogs=(Analog("ai.aug.rag", "analogy",
                        "Episodic memory retrieved by cue ↔ retrieval-augmented generation fetching documents by embedding similarity. Complementary learning systems theory says a fast memory store next to a slow learner is necessary — RAG is that architecture.",
                        (MCCLELLAND, LEWIS)),),
        order=4,
    ),
    Node(
        id="brain.region.basal_ganglia", side="brain", level=2, name="Basal ganglia", parent="brain.organ", group="subcortex",
        description="Striatum (caudate, putamen, nucleus accumbens), globus pallidus, subthalamic nucleus, substantia nigra.",
        function="Action selection and reinforcement learning: choose which of many competing cortical plans gets released.",
        mechanism="Tonic inhibition of thalamus by GPi/SNr; a chosen action's channel is disinhibited (direct pathway) while competitors stay suppressed (indirect pathway). Dopamine trains which channels win.",
        cites=(ALEXANDER, REDGRAVE),
        ho_labels=("Left Caudate", "Right Caudate", "Left Putamen", "Right Putamen", "Left Accumbens", "Right Accumbens"),
        pauli=("GPe", "GPi", "STH", "SNr"),
        neuromorpho={"region": "striatum", "cell_type": "medium spiny"},
        analogs=(Analog("ai.arch.sampler", "analogy",
                        "Winner-take-all selection among competing candidates — softmax sampling over the vocabulary plays the same role in one step.",
                        (REDGRAVE,)),),
        order=5,
    ),
    Node(
        id="brain.region.thalamus", side="brain", level=2, name="Thalamus", parent="brain.organ", group="subcortex",
        description="Paired egg-shaped nuclei at the center of the brain; every sense but smell passes through it to cortex.",
        function="Relay and gating of sensory input; cortico-thalamo-cortical loops route information between cortical areas.",
        mechanism="First-order nuclei relay periphery → cortex; higher-order nuclei relay cortex → cortex (Sherman 2016).",
        cites=(SHERMAN,),
        ho_labels=("Left Thalamus", "Right Thalamus"),
        neuromorpho={"region": "thalamus", "cell_type": ""},
        analogs=(Analog("ai.block.residual", "analogy",
                        "A shared bus every area reads from and writes to. The residual stream is the transformer's bus; the thalamus is a candidate for the cortex's.",
                        (SHERMAN, DEHAENE)),),
        order=6,
    ),
    Node(
        id="brain.region.midbrain_da", side="brain", level=2, name="Dopamine nuclei (VTA / SNc)", parent="brain.organ", group="brainstem",
        description="A few hundred thousand dopamine neurons in the ventral tegmental area and substantia nigra pars compacta.",
        function="Broadcast a reward-prediction-error teaching signal to striatum and cortex; SNc loss causes Parkinson's disease.",
        mechanism="Phasic bursts for better-than-expected outcomes, pauses for worse-than-expected — the TD error δ (Schultz 1997).",
        cites=(SCHULTZ97, SCHULTZ98, DABNEY),
        pauli=("VTA", "SNc"),
        neuromorpho={"region": "substantia nigra", "cell_type": "dopaminergic"},
        widget="dopamine_rpe",
        analogs=(Analog("ai.train.rlhf", "strong",
                        "The reward model + RL step in RLHF and the dopamine system both implement TD-style reward prediction error. The match between δ and dopamine firing is quantitative (Schultz 1997); the architecture around it differs.",
                        (SCHULTZ97, SUTTON, OUYANG)),),
        order=7,
    ),
    Node(
        id="brain.region.amygdala", side="brain", level=2, name="Amygdala", parent="brain.organ", group="subcortex",
        description="Almond-shaped nuclei in the medial temporal lobe.",
        function="Assigns emotional value — especially threat — to stimuli; drives fear learning and autonomic responses.",
        mechanism="Lateral nucleus receives sensory input; LTP at those synapses underlies conditioned fear; central nucleus outputs to hypothalamus and brainstem.",
        cites=(Cite("LeDoux JE. Brain mechanisms of emotion and emotional learning. Curr Opin Neurobiol. 1992;2(2):191-197.", "10.1016/0959-4388(92)90011-9"),),
        ho_labels=("Left Amygdala", "Right Amygdala"),
        neuromorpho={"region": "amygdala", "cell_type": ""},
        no_analog_note="No counterpart. Language models have no valence system; the reward model in RLHF scores text, it does not assign value to the model's own states.",
        order=8,
    ),
    Node(
        id="brain.region.cerebellum", side="brain", level=2, name="Cerebellum", parent="brain.organ", group="hindbrain",
        description="'Little brain' behind the brainstem, holding 80% of all neurons in 10% of the volume.",
        function="Fine motor coordination, timing, motor learning; increasingly implicated in cognition.",
        mechanism="A repeating feedforward circuit: mossy fibers → granule cells → Purkinje cells, taught by climbing-fiber error signals (Marr 1969, Ito 1982).",
        cites=(AZEVEDO, MARR69, ITO),
        cerebellum=True,
        neuromorpho={"region": "cerebellum", "cell_type": "Purkinje"},
        analogs=(Analog("ai.train.backprop", "analogy",
                        "The one brain circuit with a clear supervised teacher: the climbing fiber delivers an error to each Purkinje cell. It is a one-layer error signal, not backpropagation through depth.",
                        (MARR69, ITO)),),
        order=9,
    ),
    Node(
        id="brain.region.v1", side="brain", level=2, name="Primary visual cortex (V1)", parent="brain.region.cortex", group="cortex",
        description="Occipital cortex around the calcarine sulcus; the first cortical stage of vision.",
        function="Detects oriented edges, spatial frequency, motion direction, binocular disparity at each retinotopic location.",
        mechanism="Simple cells sum LGN inputs in oriented rows; complex cells pool simple cells for position invariance (Hubel & Wiesel 1962). Sparse coding of natural images predicts the same filters (Olshausen & Field 1996).",
        cites=(HUBEL, OLSHAUSEN),
        ho_labels=("Intracalcarine Cortex", "Occipital Pole"),
        neuromorpho={"region": "primary visual", "cell_type": ""},
        widget="v1",
        analogs=(Analog("ai.arch.blocks", "strong",
                        "The first convolutional layer of any vision network learns Gabor-like oriented filters; that is literally Hubel-Wiesel's simple cell. Deeper layers predict V4/IT (Yamins 2014).",
                        (HUBEL, YAMINS)),),
        order=10,
    ),
    # ---- level 3: circuits --------------------------------------------------
    Node(
        id="brain.circuit.column", side="brain", level=3, name="Canonical cortical microcircuit", parent="brain.region.cortex", group="cortex",
        description="The wiring motif repeated across all of neocortex: six layers, ~80% excitatory pyramidal cells, ~20% inhibitory interneurons, in ~0.5 mm columns.",
        function="Amplify a weak thalamic input, combine it with context from other areas, and send a processed signal up (L2/3) and down (L5/6).",
        mechanism="Thalamus → L4 → L2/3 → L5 → subcortical and other areas; L6 feeds back to thalamus. Recurrent excitation among L2/3 and L5 pyramidals amplifies; PV interneurons keep it stable.",
        cites=(DOUGLAS, MOUNTCASTLE, MARKRAM, H01, MICRONS),
        ho_labels=("Postcentral Gyrus",),
        facts=(
            Fact("H01 volume (2024)", "1 mm³ human cortex: ~57,000 cells, ~150 million synapses, 1.4 petabytes", H01),
            Fact("MICrONS (2025)", "1 mm³ mouse visual cortex: ~200,000 cells, 523 million synapses, functional responses of 75,000 neurons", MICRONS),
            Fact("Blue Brain (2015)", "31,000 neurons / 37 million synapses simulated from rat data", MARKRAM),
        ),
        analogs=(Analog("ai.block.mlp", "analogy",
                        "A feedforward expand-then-compress stage repeated identically across the sheet, with recurrent amplification — the shape of an MLP block, minus the recurrence. No proof they compute the same function.",
                        (DOUGLAS, GEVA)),),
        order=0,
    ),
    Node(
        id="brain.circuit.hippocampus", side="brain", level=3, name="Trisynaptic loop (EC → DG → CA3 → CA1)", parent="brain.region.hippocampus", group="subcortex",
        description="Entorhinal cortex projects to dentate gyrus (perforant path), DG mossy fibers to CA3, CA3 Schaffer collaterals to CA1, CA1 back to entorhinal cortex.",
        function="Store a new episode in one exposure and later recall the whole from a fragment (pattern completion).",
        mechanism="DG sparsifies inputs (pattern separation); CA3's recurrent collaterals form an autoassociative network — Marr 1971, formalized by Hopfield 1982; CA1 compares CA3's recall with current input.",
        cites=(AMARAL, MARR71, TREVES, HOPFIELD, WILSON),
        ho_labels=("Left Hippocampus", "Right Hippocampus"),
        neuromorpho={"region": "CA3", "cell_type": "pyramidal"},
        widget="modern_hopfield",
        analogs=(
            Analog("ai.block.attention", "strong",
                   "CA3 is modelled as an autoassociative (Hopfield) memory; the modern continuous Hopfield update is exactly the attention formula (Ramsauer 2021). The equivalence is between attention and the MODEL of CA3 — the biology itself is not proved to run this update.",
                   (MARR71, TREVES, RAMSAUER)),
            Analog("ai.train.replay", "strong",
                   "Place-cell sequences replay during sleep (Wilson & McNaughton 1994); DQN's experience replay was designed from this (Mnih 2015).",
                   (WILSON, MNIH, MCCLELLAND)),
        ),
        order=1,
    ),
    Node(
        id="brain.circuit.basal_ganglia", side="brain", level=3, name="Direct / indirect pathways", parent="brain.region.basal_ganglia", group="subcortex",
        description="Cortex → striatum → GPi/SNr → thalamus → cortex (direct, D1 receptors) and cortex → striatum → GPe → STN → GPi/SNr (indirect, D2 receptors).",
        function="Release one action and suppress its competitors; dopamine biases the balance toward rewarded actions.",
        mechanism="Direct pathway inhibits the inhibitor (GPi) → disinhibits thalamus → 'go'. Indirect pathway excites GPi via STN → 'no-go'. Dopamine strengthens direct and weakens indirect synapses in the striatum.",
        cites=(ALEXANDER, REDGRAVE),
        pauli=("GPe", "GPi", "STH", "SNr", "Ca", "Pu"),
        ho_labels=("Left Thalamus", "Right Thalamus"),
        analogs=(Analog("ai.arch.sampler", "analogy",
                        "Selection with lateral suppression ↔ softmax + sampling. Same job; the mechanism (disinhibition loops over ~100 ms) has no counterpart in one matrix multiply.",
                        (REDGRAVE,)),),
        order=2,
    ),
    Node(
        id="brain.circuit.dopamine", side="brain", level=3, name="Reward-prediction-error loop", parent="brain.region.midbrain_da", group="brainstem",
        description="VTA/SNc dopamine neurons receive reward and prediction signals and project to nucleus accumbens, dorsal striatum and prefrontal cortex.",
        function="Compute δ = reward received − reward expected and broadcast it as a global teaching signal.",
        mechanism="Temporal-difference learning: δ(t) = r(t) + γV(t) − V(t−1). Unexpected reward → burst; predicted reward → burst moves to the cue; omitted reward → pause. Later work shows a population code for the whole reward distribution (Dabney 2020).",
        cites=(SCHULTZ97, MONTAGUE, SUTTON, SCHULTZ98, DABNEY),
        pauli=("VTA", "SNc", "NAC"),
        widget="dopamine_rpe",
        analogs=(Analog("ai.train.rlhf", "strong",
                        "Same algorithm family (TD / policy-gradient RL with a scalar reward signal); in RLHF the reward model plays the role of the reward pathway. Evidence for the brain side is quantitative single-neuron data.",
                        (SCHULTZ97, SUTTON, OUYANG)),),
        order=3,
    ),
    Node(
        id="brain.circuit.cerebellum", side="brain", level=3, name="Cerebellar cortex circuit", parent="brain.region.cerebellum", group="hindbrain",
        description="Mossy fibers → ~50 billion granule cells → parallel fibers → Purkinje cells → deep cerebellar nuclei; one climbing fiber from the inferior olive per Purkinje cell.",
        function="Learn to predict the sensory consequences of movement and correct it in real time.",
        mechanism="Granule cells expand the input into a high-dimensional sparse code; the climbing fiber signals error and drives LTD at active parallel-fiber synapses (Marr 1969, Ito 1982).",
        cites=(MARR69, ITO, AZEVEDO),
        cerebellum=True,
        neuromorpho={"region": "cerebellum", "cell_type": "Purkinje"},
        analogs=(Analog("ai.unit.neuron", "analogy",
                        "Marr's cerebellum is a perceptron: a huge random expansion layer and one trained linear readout per Purkinje cell with an explicit error signal.",
                        (MARR69, ROSENBLATT)),),
        order=4,
    ),
    Node(
        id="brain.circuit.thalamocortical", side="brain", level=3, name="Thalamocortical loop", parent="brain.region.thalamus", group="subcortex",
        description="Thalamic relay cells project to cortical layer 4; cortical layer 6 projects back to the same thalamic nucleus; layer 5 projects to higher-order thalamus which projects to the next cortical area.",
        function="Gate sensory input by arousal state; route messages between cortical areas through the thalamus.",
        mechanism="Relay cells switch between tonic (faithful) and burst (alerting) modes; L6 feedback adjusts their gain (Sherman 2016).",
        cites=(SHERMAN,),
        ho_labels=("Left Thalamus", "Right Thalamus", "Postcentral Gyrus"),
        analogs=(Analog("ai.block.residual", "analogy",
                        "Both are the path by which every stage reads a shared signal and writes back to it.",
                        (SHERMAN,)),),
        order=5,
    ),
    Node(
        id="brain.circuit.v1", side="brain", level=3, name="V1 orientation circuit", parent="brain.region.v1", group="cortex",
        description="LGN center-surround cells → layer-4 simple cells (oriented, phase-sensitive) → complex cells (oriented, phase-invariant).",
        function="Turn pixel-like retinal input into an edge map.",
        mechanism="Simple cell = linear filter (Gabor) + threshold; complex cell = sum of squared quadrature-pair simple cells (energy model).",
        cites=(HUBEL,),
        ho_labels=("Intracalcarine Cortex",),
        widget="v1",
        analogs=(Analog("ai.block.mlp", "analogy",
                        "Filter → nonlinearity → pool is the convolutional block; the transformer MLP keeps the filter→nonlinearity part without spatial pooling.",
                        (HUBEL,)),),
        order=6,
    ),
    Node(
        id="brain.circuit.working_memory", side="brain", level=3, name="Prefrontal working-memory attractor", parent="brain.region.prefrontal", group="cortex",
        description="Recurrently connected prefrontal pyramidal cells whose firing persists through a delay after the stimulus is gone.",
        function="Hold an item (a location, a rule) online for seconds.",
        mechanism="Recurrent NMDA-receptor-mediated excitation balanced by inhibition creates a stable bump of activity (Wong & Wang 2006).",
        cites=(FUNAHASHI, GOLDMAN, WONGWANG),
        ho_labels=("Middle Frontal Gyrus",),
        analogs=(Analog("ai.aug.kvcache", "analogy",
                        "Persistent state for the current task. The brain re-generates it every ~100 ms; the cache stores it losslessly.",
                        (GOLDMAN,)),),
        order=7,
    ),
    # ---- level 4: cells -----------------------------------------------------
    Node(
        id="brain.cell", side="brain", level=4, name="Neuron types (census)", parent="brain.organ", group="all",
        description="The current human census: 461 clusters and 3,313 subclusters of cells from ~3 million single nuclei sampled across ~100 brain locations (Siletti 2023).",
        function="Different types compute differently: excitatory projection cells carry signals between areas; inhibitory interneurons shape timing and gain; neuromodulatory cells broadcast state.",
        mechanism="Type is set by gene expression, which sets ion channels, receptors, morphology and wiring rules.",
        cites=(SILETTI, CONNORS, TREMBLAY),
        facts=(Fact("human cell types", "461 clusters / 3,313 subclusters", SILETTI),),
        analogs=(Analog("ai.unit.neuron", "none",
                        "An artificial network has one unit type repeated; a brain has thousands of cell types with different dynamics. There is no mapping from cell types onto anything in a transformer.",
                        (SILETTI,)),),
        order=0,
    ),
    Node(
        id="brain.cell.pyramidal", side="brain", level=4, name="Cortical pyramidal neuron", parent="brain.cell", group="cortex",
        description="The principal excitatory cell of cortex: a pyramid-shaped soma, a long apical dendrite reaching layer 1, basal dendrites, one axon.",
        function="Integrate thousands of inputs and decide when to spike; L5 cells associate feedforward input on basal dendrites with feedback on the apical tuft (Larkum 2013).",
        mechanism="Regular-spiking or bursting (Connors & Gutnick 1990). Dendritic branches act as separate nonlinear subunits (Polsky 2004); reproducing one cell's I/O needs a 5-8 layer temporal CNN (Beniaguev 2021).",
        cites=(CONNORS, LARKUM, POLSKY, LONDON, BENIAGUEV, HH),
        ho_labels=("Precentral Gyrus", "Frontal Pole"),
        neuromorpho={"region": "neocortex", "cell_type": "pyramidal"},
        widget="hh",
        analogs=(Analog("ai.unit.neuron", "analogy",
                        "The artificial neuron was abstracted from this cell (McCulloch-Pitts 1943) but a real pyramidal cell is itself a small deep network — the unit-to-cell analogy is the weakest link in the whole ladder.",
                        (MCP, BENIAGUEV, POLSKY)),),
        order=1,
    ),
    Node(
        id="brain.cell.pv", side="brain", level=4, name="Parvalbumin (PV) fast-spiking interneuron", parent="brain.cell", group="cortex",
        description="Basket and chandelier cells; ~40% of cortical interneurons; GABAergic.",
        function="Fast feedforward and feedback inhibition onto pyramidal somas; sets spike timing and gain; generates gamma rhythms.",
        mechanism="Kv3 channels allow >200 Hz non-adapting firing; synapses onto the soma/initial segment veto spikes precisely.",
        cites=(TREMBLAY, CONNORS),
        neuromorpho={"region": "neocortex", "cell_type": "basket"},
        analogs=(Analog("ai.block.norm", "analogy",
                        "Divisive gain control by inhibition is one biological implementation of normalization (Carandini & Heeger); layer norm is the transformer's normalization.",
                        (CARANDINI, TREMBLAY)),),
        order=2,
    ),
    Node(
        id="brain.cell.sst", side="brain", level=4, name="Somatostatin (SST) Martinotti interneuron", parent="brain.cell", group="cortex",
        description="~30% of cortical interneurons; axons ascend to layer 1 and inhibit pyramidal apical dendrites.",
        function="Dendritic inhibition — gates the feedback input arriving on apical tufts; disinhibited by VIP cells during attention.",
        mechanism="Facilitating synapses recruit SST cells during sustained activity, producing delayed lateral inhibition.",
        cites=(TREMBLAY,),
        neuromorpho={"region": "neocortex", "cell_type": "Martinotti"},
        no_analog_note="No counterpart: transformers have no mechanism that selectively gates one input pathway of a unit while leaving the other open.",
        order=3,
    ),
    Node(
        id="brain.cell.ca3", side="brain", level=4, name="CA3 pyramidal neuron", parent="brain.cell", group="subcortex",
        description="Hippocampal pyramidal cell receiving giant mossy-fiber synapses from dentate granule cells and ~12,000 recurrent collateral synapses from other CA3 cells.",
        function="The storage element of the autoassociative memory.",
        mechanism="Recurrent collaterals with Hebbian plasticity store patterns as attractors (Marr 1971, Treves & Rolls 1994).",
        cites=(MARR71, TREVES, AMARAL),
        ho_labels=("Left Hippocampus", "Right Hippocampus"),
        neuromorpho={"region": "CA3", "cell_type": "pyramidal"},
        widget="hopfield",
        analogs=(Analog("ai.block.attention", "strong",
                        "A stored pattern in a Hopfield model of CA3 ↔ a key-value pair in attention (Ramsauer 2021).",
                        (RAMSAUER, TREVES)),),
        order=4,
    ),
    Node(
        id="brain.cell.granule", side="brain", level=4, name="Dentate granule cell", parent="brain.cell", group="subcortex",
        description="Small, densely packed excitatory cells of the dentate gyrus; one of two sites of adult neurogenesis.",
        function="Pattern separation: make similar inputs dissimilar before storage.",
        mechanism="Very sparse firing (most are silent) and expansion in number (~1M granule cells per ~200k entorhinal inputs in rat) decorrelate inputs.",
        cites=(AMARAL, TREVES),
        ho_labels=("Left Hippocampus", "Right Hippocampus"),
        neuromorpho={"region": "dentate gyrus", "cell_type": "granule"},
        analogs=(Analog("ai.unit.feature", "analogy",
                        "Sparse expansion coding — the same idea that makes sparse-autoencoder features separable (Bricken 2023).",
                        (BRICKEN,)),),
        order=5,
    ),
    Node(
        id="brain.cell.purkinje", side="brain", level=4, name="Purkinje cell", parent="brain.cell", group="hindbrain",
        description="The largest dendritic tree in the brain: a flat fan receiving ~150,000 parallel-fiber synapses and one climbing fiber.",
        function="The cerebellum's only output from its cortex; learns which input patterns to suppress.",
        mechanism="Simple spikes (parallel fibers) and complex spikes (climbing fiber); coincidence of the two triggers LTD at active parallel-fiber synapses.",
        cites=(MARR69, ITO),
        cerebellum=True,
        neuromorpho={"region": "cerebellum", "cell_type": "Purkinje"},
        analogs=(Analog("ai.unit.neuron", "analogy",
                        "A single trained readout unit with a teacher signal — the closest biological thing to a perceptron.",
                        (MARR69,)),),
        order=6,
    ),
    Node(
        id="brain.cell.msn", side="brain", level=4, name="Medium spiny neuron (striatum)", parent="brain.cell", group="subcortex",
        description="~95% of striatal neurons; GABAergic projection cells with spine-covered dendrites; express D1 (direct) or D2 (indirect) dopamine receptors.",
        function="Vote for or against an action; the site where dopamine changes future votes.",
        mechanism="Cortical glutamate on spines; dopamine modulates plasticity at those spines (three-factor rule).",
        cites=(ALEXANDER, REDGRAVE),
        ho_labels=("Left Caudate", "Right Caudate", "Left Putamen", "Right Putamen"),
        neuromorpho={"region": "striatum", "cell_type": "medium spiny"},
        analogs=(Analog("ai.train.rlhf", "analogy",
                        "The parameters that the reward signal actually updates.",
                        (SCHULTZ97,)),),
        order=7,
    ),
    Node(
        id="brain.cell.dopamine", side="brain", level=4, name="Dopamine neuron", parent="brain.cell", group="brainstem",
        description="Pacemaking cells of VTA/SNc (~2-8 Hz tonic) with vast axonal arbors — one SNc axon can carry ~400,000 release sites in rat.",
        function="Emit the phasic burst/pause that reports reward prediction error.",
        mechanism="Tonic firing from intrinsic pacemaker channels; bursts driven by glutamatergic input; pauses by GABA (habenula → RMTg).",
        cites=(SCHULTZ98, SCHULTZ97),
        pauli=("VTA", "SNc"),
        neuromorpho={"region": "substantia nigra", "cell_type": "dopaminergic"},
        widget="dopamine_rpe",
        analogs=(Analog("ai.train.rlhf", "strong", "Its firing rate is the δ of TD learning (Schultz 1997).", (SCHULTZ97,)),),
        order=8,
    ),
    Node(
        id="brain.cell.relay", side="brain", level=4, name="Thalamic relay neuron", parent="brain.cell", group="subcortex",
        description="Glutamatergic projection cells of thalamic nuclei with bushy dendrites.",
        function="Pass sensory or cortical input to cortex in tonic or burst mode.",
        mechanism="T-type Ca²⁺ channels: hyperpolarized → burst mode; depolarized → tonic mode (Sherman 2016).",
        cites=(SHERMAN,),
        ho_labels=("Left Thalamus", "Right Thalamus"),
        neuromorpho={"region": "thalamus", "cell_type": ""},
        no_analog_note="No counterpart: no unit in a transformer switches its input-output mode by internal state.",
        order=9,
    ),
    # ---- level 5: synapse / molecule ---------------------------------------
    Node(
        id="brain.synapse.glutamate", side="brain", level=5, name="Glutamatergic synapse (AMPA + NMDA)", parent="brain.cell.pyramidal", group="all",
        description="The brain's main excitatory synapse: vesicles of glutamate onto a dendritic spine carrying AMPA and NMDA receptors.",
        function="AMPA: fast depolarization (~2 ms). NMDA: slow current that only flows when the postsynaptic cell is already depolarized — a coincidence detector for Hebbian learning.",
        mechanism="NMDA's pore is blocked by Mg²⁺ at rest; the block is voltage-dependent: B(V) = 1/(1 + [Mg]/3.57 mM · e^(−0.062V)) (Jahr & Stevens 1990). Ca²⁺ through unblocked NMDA receptors triggers LTP.",
        cites=(DESTEXHE, JAHR, COLLINGRIDGE),
        widget="synapse",
        analogs=(Analog("ai.param.weight", "strong",
                        "Synaptic efficacy is the physical quantity every connectionist model calls 'the weight'. What is NOT shared: a weight is one number; a synapse is two receptor populations with different kinetics and a voltage-dependent gate.",
                        (DESTEXHE,)),),
        order=0,
    ),
    Node(
        id="brain.synapse.gaba", side="brain", level=5, name="GABAergic synapse (GABA-A)", parent="brain.cell.pv", group="all",
        description="The main inhibitory synapse: GABA opens Cl⁻ channels with a ~10 ms decay.",
        function="Hyperpolarize or shunt the postsynaptic cell; sets the excitation/inhibition balance that keeps cortex from seizing.",
        mechanism="Reversal potential near −70 mV, so GABA-A current is small at rest and strongly inhibitory once the cell depolarizes (shunting).",
        cites=(DESTEXHE, TREMBLAY),
        widget="synapse",
        analogs=(Analog("ai.param.weight", "analogy",
                        "A negative weight. But inhibition in cortex is divisive/shunting, not merely subtractive.",
                        (CARANDINI,)),),
        order=1,
    ),
    Node(
        id="brain.synapse.ltp", side="brain", level=5, name="Long-term potentiation / depression", parent="brain.synapse.glutamate", group="all",
        description="Lasting strengthening (LTP) or weakening (LTD) of a synapse after patterned activity — first shown by Bliss & Lømo 1973.",
        function="The physical change that stores a memory; Hebb's rule made real.",
        mechanism="High Ca²⁺ via NMDA receptors → CaMKII → more AMPA receptors inserted (LTP); modest Ca²⁺ → phosphatases → AMPA removal (LTD). Late LTP needs new protein synthesis via CREB (Kandel 2001).",
        cites=(BLISS, MALENKA, COLLINGRIDGE, KANDEL),
        ho_labels=("Left Hippocampus", "Right Hippocampus"),
        widget="hebbian",
        analogs=(Analog("ai.param.gradient", "analogy",
                        "Both change the weight. LTP is local (depends only on pre- and post-activity at that synapse); a gradient step depends on the error at the OUTPUT, propagated back — a global signal the synapse has no known access to.",
                        (LILLICRAP, MALENKA)),),
        order=2,
    ),
    Node(
        id="brain.synapse.stdp", side="brain", level=5, name="Spike-timing-dependent plasticity", parent="brain.synapse.ltp", group="all",
        description="The sign of plasticity depends on the order of pre- and postsynaptic spikes within ~20 ms.",
        function="Encode causality: inputs that predict the postsynaptic spike get stronger.",
        mechanism="Pre-before-post → strong NMDA Ca²⁺ → LTP; post-before-pre → weak Ca²⁺ → LTD (Bi & Poo 1998).",
        cites=(BIPOO,),
        widget="stdp",
        analogs=(Analog("ai.param.gradient", "analogy",
                        "A local, timing-based weight update. Neuromorphic chips (Loihi) implement it in hardware; it is not what trains transformers.",
                        (BIPOO,)),),
        order=3,
    ),
    Node(
        id="brain.synapse.release", side="brain", level=5, name="Vesicle release machinery", parent="brain.synapse.glutamate", group="all",
        description="Synaptic vesicles docked at the active zone fuse within ~1 ms of Ca²⁺ entry through voltage-gated channels.",
        function="Convert a presynaptic spike into transmitter release — probabilistically, with short-term facilitation and depression.",
        mechanism="SNARE complex (synaptobrevin/syntaxin/SNAP-25) primed by Munc18/Munc13; synaptotagmin senses Ca²⁺ and triggers fusion (Südhof 2013). Quantal release (Fatt & Katz 1952). Release probability changes over tens of ms (Tsodyks & Markram 1997).",
        cites=(SUDHOF, KATZ, TSODYKS),
        no_analog_note="No counterpart: transformer weights are deterministic and history-independent; a synapse's effective weight fluctuates trial-to-trial and with recent use.",
        order=4,
    ),
    Node(
        id="brain.synapse.channels", side="brain", level=5, name="Voltage-gated Na⁺ / K⁺ channels", parent="brain.cell.pyramidal", group="all",
        description="Membrane proteins whose open probability depends on voltage — the parts list of the action potential.",
        function="Generate and propagate the spike: Na⁺ channels open fast for the upstroke, K⁺ channels open slower for repolarization.",
        mechanism="Hodgkin-Huxley 1952: I = g_Na m³h (V−E_Na) + g_K n⁴ (V−E_K) + g_L (V−E_L). Single-channel currents recorded by patch clamp (Neher & Sakmann 1976); structure by Catterall.",
        cites=(HH, NEHER, CATTERALL),
        widget="hh",
        analogs=(Analog("ai.param.activation", "analogy",
                        "The spike threshold is the biological nonlinearity; ReLU/GELU are its cartoon. HH gives a rate-vs-current curve with a threshold and saturation; GELU has neither dynamics nor refractoriness.",
                        (HH, HENDRYCKS)),),
        order=5,
    ),
    Node(
        id="brain.synapse.neuromod", side="brain", level=5, name="Neuromodulator receptors", parent="brain.cell", group="all",
        description="G-protein-coupled receptors for dopamine, serotonin, noradrenaline, acetylcholine, histamine, opioids, cannabinoids — mapped in living humans by PET (Hansen 2022, 19 receptors).",
        function="Change how a circuit computes without changing what it is connected to: gain, learning rate, excitability, mode.",
        mechanism="Second-messenger cascades (cAMP, PKA, etc.) alter ion channels and plasticity over seconds to minutes.",
        cites=(HANSEN,),
        analogs=(Analog("ai.param.temperature", "analogy",
                        "A global knob that changes behaviour without retraining — like sampling temperature or the learning rate. The brain has ~a dozen such knobs with regional maps.",
                        (HANSEN,)),),
        order=6,
    ),
    Node(
        id="brain.synapse.molecular", side="brain", level=5, name="Gene → protein → synapse", parent="brain.synapse.ltp", group="all",
        description="Long-term memory requires new gene expression: CREB-driven transcription builds proteins that stabilize potentiated synapses.",
        function="Convert a transient electrical event into a structural change that lasts years.",
        mechanism="Ca²⁺/cAMP → PKA → CREB phosphorylation → immediate-early genes → protein synthesis at tagged synapses (Kandel 2001). Whole-genome expression atlas: Hawrylycz 2012.",
        cites=(KANDEL, HAWRYLYCZ),
        no_analog_note="No counterpart: a trained model has no separate consolidation step; weights are the memory the moment they are written.",
        order=7,
    ),
    Node(
        id="brain.synapse.homeostasis", side="brain", level=5, name="Synaptic scaling & pruning", parent="brain.synapse.glutamate", group="all",
        description="Neurons multiplicatively scale all their synapses to keep firing in range (Turrigiano 1998); developing cortex overproduces synapses then prunes ~40% (Huttenlocher 1979).",
        function="Stability and regularization: keep learning from saturating, remove unused connections.",
        mechanism="Activity-dependent AMPA receptor trafficking over hours (scaling); microglia and complement-tagged elimination (pruning).",
        cites=(TURRIGIANO, HUTTENLOCHER),
        analogs=(Analog("ai.train.regularization", "analogy",
                        "Weight decay ↔ scaling; dropout / sparsification ↔ pruning. Same purpose, unrelated mechanism.",
                        (SRIVASTAVA, TURRIGIANO)),),
        order=8,
    ),
)

# ---------------------------------------------------------------------------
# AI  (decoder-only transformer language model + its training loop)
# ---------------------------------------------------------------------------
AI: tuple[Node, ...] = (
    # ---- level 1 -----------------------------------------------------------
    Node(
        id="ai.system", side="ai", level=1, name="Deployed language model", parent=None, group="system",
        description="A trained transformer's weights plus the runtime that feeds it tokens, caches its state, samples its outputs, and optionally retrieves documents or calls tools.",
        function="Map a context of tokens to a probability distribution over the next token, repeatedly.",
        mechanism="Autoregressive inference: one forward pass per generated token, reusing cached keys/values for the prefix.",
        cites=(VASWANI, BROWN, FEDUS),
        facts=(
            Fact("GPT-3 parameters", "175 billion", BROWN),
            Fact("Switch Transformer", "1.6 trillion parameters (sparse MoE)", FEDUS),
            Fact("GPT-3 training tokens", "~300 billion", BROWN),
        ),
        analogs=(Analog("brain.organ", "analogy", "Top of the ladder on both sides; see the brain node for why the parts are not equivalent.", (HASSABIS,)),),
        order=0,
    ),
    # ---- level 2: architecture --------------------------------------------
    Node(
        id="ai.arch", side="ai", level=2, name="Transformer architecture", parent="ai.system", group="inference",
        description="Embedding → positional encoding → N identical blocks (attention + MLP with residual connections and normalization) → final norm → unembedding → softmax.",
        function="Build a contextual representation of every token in parallel, then read the next-token distribution off the last position.",
        mechanism="Every block adds a small update to the residual stream; depth composes those updates.",
        cites=(VASWANI,),
        analogs=(Analog("brain.region.cortex", "strong",
                        "Hierarchical depth with layer-wise representations that predict brain areas (Yamins 2014; Schrimpf 2021).",
                        (YAMINS, SCHRIMPF)),),
        order=0,
    ),
    Node(
        id="ai.arch.tokenizer", side="ai", level=2, name="Tokenizer", parent="ai.arch", group="inference",
        description="Splits text into ~50k-200k subword units by a fixed byte-pair-encoding table.",
        function="Discretize input into the vocabulary the model was trained on.",
        mechanism="Greedy merges of frequent byte pairs learned once from the corpus; not learned by gradient.",
        cites=(BROWN,),
        no_analog_note="No counterpart: sensory receptors transduce continuous signals; nothing in the brain pre-segments input into a fixed symbol table.",
        order=1,
    ),
    Node(
        id="ai.arch.embedding", side="ai", level=2, name="Token embedding", parent="ai.arch", group="inference",
        description="A learned lookup table: each vocabulary token → a d-dimensional vector (d ≈ 12,288 in GPT-3).",
        function="Give every token a position in a semantic space where related tokens are near each other.",
        mechanism="Trained end-to-end; the same matrix (tied) is often used for unembedding.",
        cites=(VASWANI, BROWN),
        analogs=(Analog("brain.region.cortex", "analogy",
                        "Word meaning is represented as a distributed map across cortex (Huth 2016) with a semantic hub in anterior temporal lobe (Patterson 2007); embeddings are a distributed semantic space. The LLM embedding can be decoded FROM fMRI (Tang 2023) — a correlational, not mechanistic, link.",
                        (HUTH, PATTERSON, Cite("Tang J, LeBel A, Jain S, Huth AG. Semantic reconstruction of continuous language from non-invasive brain recordings. Nat Neurosci. 2023;26(5):858-866.", "10.1038/s41593-023-01304-9"))),),
        order=2,
    ),
    Node(
        id="ai.arch.position", side="ai", level=2, name="Positional encoding (RoPE)", parent="ai.arch", group="inference",
        description="Injects each token's position so attention can tell order; modern models rotate query/key vectors by position-dependent angles (RoPE).",
        function="Let attention depend on relative distance between tokens.",
        mechanism="Rotary embedding: q_m·k_n depends only on m−n through a rotation by mθ.",
        cites=(SU, VASWANI),
        analogs=(Analog("brain.circuit.hippocampus", "analogy",
                        "Grid cells give the brain a periodic positional code (Hafting 2005); networks trained to navigate develop grid-like units (Banino 2018), and the Tolman-Eichenbaum Machine relates transformer position codes to grid/place cells (Whittington 2022). A formal model connects them; the biology is spatial, the model's is sequential.",
                        (HAFTING, BANINO, WHITTINGTON22)),),
        order=3,
    ),
    Node(
        id="ai.arch.blocks", side="ai", level=2, name="Stack of N transformer blocks", parent="ai.arch", group="inference",
        description="N identical blocks (96 in GPT-3), each reading the residual stream, computing attention and an MLP, and adding the result back.",
        function="Depth: early blocks resolve syntax and local features, later blocks compose abstract, task-level features.",
        mechanism="Residual composition — each block's output is a delta added to a shared d-dimensional stream (He 2016).",
        cites=(VASWANI, HE, BROWN),
        analogs=(
            Analog("brain.region.cortex", "strong",
                   "Layer depth aligns with the cortical hierarchy: successive CNN layers best predict V1 → V4 → IT (Yamins 2014); intermediate LLM layers best predict language cortex (Schrimpf 2021).",
                   (YAMINS, SCHRIMPF)),
            Analog("brain.region.v1", "strong",
                   "First-layer filters of vision networks are Hubel-Wiesel simple cells.",
                   (HUBEL, YAMINS)),
        ),
        order=4,
    ),
    Node(
        id="ai.arch.unembed", side="ai", level=2, name="Unembedding + softmax", parent="ai.arch", group="inference",
        description="Project the final residual vector onto every vocabulary token to get logits; softmax turns them into probabilities.",
        function="Read out the model's belief about the next token.",
        mechanism="logits = W_U · h_final; p = softmax(logits / T).",
        cites=(VASWANI,),
        analogs=(Analog("brain.region.basal_ganglia", "analogy", "Competition among candidate outputs resolved into one choice.", (REDGRAVE,)),),
        order=5,
    ),
    Node(
        id="ai.arch.sampler", side="ai", level=2, name="Sampler (temperature / top-p)", parent="ai.arch", group="inference",
        description="Draw one token from the output distribution — greedy, temperature-scaled, or nucleus (top-p).",
        function="Commit to an action; control the exploration/exploitation trade-off of generation.",
        mechanism="Temperature T rescales logits; top-p truncates to the smallest set with cumulative probability p.",
        cites=(BROWN,),
        analogs=(Analog("brain.circuit.basal_ganglia", "analogy",
                        "Action selection with lateral suppression (Redgrave 1999) does in ~100 ms of disinhibition what argmax/sampling does in one call.",
                        (REDGRAVE,)),),
        order=6,
    ),
    # training loop
    Node(
        id="ai.train", side="ai", level=2, name="Training loop", parent="ai.system", group="training",
        description="Corpus → forward pass → next-token loss → backpropagation → optimizer step, repeated ~10⁶ times; then preference fine-tuning (RLHF).",
        function="Set every weight so that the model assigns high probability to the text it was shown.",
        mechanism="Stochastic gradient descent on a cross-entropy objective with regularization; the gradient is computed exactly by the chain rule.",
        cites=(RUMELHART, BROWN, OUYANG),
        no_analog_note="Taken as a whole, no counterpart: the brain has no separate training and deployment phases — it learns while it runs.",
        order=7,
    ),
    Node(
        id="ai.train.data", side="ai", level=2, name="Pretraining corpus", parent="ai.train", group="training",
        description="Hundreds of billions to trillions of tokens of text scraped from the web, books and code.",
        function="The only source of everything the base model knows.",
        mechanism="Shuffled, deduplicated, streamed in batches of ~millions of tokens.",
        cites=(BROWN, FRANK),
        facts=(Fact("child vs LLM data", "children hear ~10⁷ words by age 10; LLMs train on ~10¹¹-10¹³ — a gap of 4-5 orders of magnitude", FRANK),),
        analogs=(Analog("brain.organ", "none",
                        "A child reaches adult-level language with ~10,000× less data (Frank 2023); Zador 2019 argues the difference is a genome-encoded prior no model has. The data regime is the sharpest disanalogy.",
                        (FRANK, ZADOR)),),
        order=8,
    ),
    Node(
        id="ai.train.loss", side="ai", level=2, name="Next-token prediction loss", parent="ai.train", group="training",
        description="Cross-entropy between the model's distribution and the actual next token, averaged over every position.",
        function="The single objective from which all capabilities emerge.",
        mechanism="L = −Σ log p(x_{t+1} | x_{≤t}). Its gradient flows back through every block.",
        cites=(BROWN, VASWANI),
        analogs=(Analog("brain.region.cortex", "strong",
                        "Predictive coding holds that cortex continuously predicts its input and propagates prediction errors (Rao & Ballard 1999; Friston 2010). Human language cortex predicts upcoming words and signals surprise — the same three principles as GPT-2 (Goldstein 2022); models that predict words better predict brains better (Schrimpf 2021).",
                        (RAO, FRISTON, GOLDSTEIN, SCHRIMPF)),),
        order=9,
    ),
    Node(
        id="ai.train.backprop", side="ai", level=2, name="Backpropagation", parent="ai.train", group="training",
        description="Exact computation of ∂L/∂w for every weight by applying the chain rule backward through the network.",
        function="Tell every weight how it contributed to the error at the output — global credit assignment.",
        mechanism="Reverse-mode automatic differentiation: the backward pass reuses the forward pass's activations and the transposed weights.",
        cites=(RUMELHART, LILLICRAP),
        analogs=(Analog("brain.circuit.column", "none",
                        "No confirmed biological implementation: it needs symmetric weights, a separate backward phase and non-local error signals. Candidate approximations use apical dendrites as error channels (Sacramento 2018); the cerebellum's climbing fiber is a one-layer teacher (Marr 1969). Open problem (Lillicrap 2020).",
                        (LILLICRAP, SACRAMENTO, MARR69)),),
        order=10,
    ),
    Node(
        id="ai.train.optimizer", side="ai", level=2, name="Optimizer (Adam)", parent="ai.train", group="training",
        description="Adaptive per-parameter step sizes from running estimates of the gradient's mean and variance.",
        function="Turn a gradient into a weight change that makes training stable at scale.",
        mechanism="m ← β₁m + (1−β₁)g; v ← β₂v + (1−β₂)g²; w ← w − η·m̂/(√v̂ + ε).",
        cites=(KINGMA,),
        no_analog_note="No counterpart: synapses have no second-moment memory of their own gradient history.",
        order=11,
    ),
    Node(
        id="ai.train.regularization", side="ai", level=2, name="Regularization (dropout, weight decay)", parent="ai.train", group="training",
        description="Randomly zero units during training (dropout); shrink all weights each step (weight decay).",
        function="Prevent overfitting; keep weights small and representations redundant.",
        mechanism="Dropout samples a thinned network per batch; weight decay adds λ‖w‖² to the loss.",
        cites=(SRIVASTAVA, KINGMA),
        analogs=(Analog("brain.synapse.homeostasis", "analogy", "Synaptic scaling and developmental pruning serve the same stabilizing purpose by unrelated mechanisms.", (TURRIGIANO, HUTTENLOCHER)),),
        order=12,
    ),
    Node(
        id="ai.train.rlhf", side="ai", level=2, name="RLHF: reward model + policy optimization", parent="ai.train", group="training",
        description="Humans rank model outputs → a reward model learns to score text → the language model is fine-tuned by reinforcement learning (PPO) to maximize that score.",
        function="Align the model's behaviour with human preference rather than corpus likelihood.",
        mechanism="A scalar reward at the end of each response; a KL penalty keeps the policy near the pretrained model.",
        cites=(OUYANG, SUTTON),
        widget="dopamine_rpe",
        analogs=(Analog("brain.circuit.dopamine", "strong",
                        "Same algorithm family — reward prediction error driving policy change. Dopamine neurons literally fire δ (Schultz 1997); the distributional-RL refinement was later found in dopamine too (Dabney 2020). What differs: the brain's reward is multidimensional and internally generated.",
                        (SCHULTZ97, SUTTON, DABNEY)),),
        order=13,
    ),
    Node(
        id="ai.train.replay", side="ai", level=2, name="Data shuffling / experience replay", parent="ai.train", group="training",
        description="Training samples are interleaved at random; in RL, past transitions are stored in a buffer and replayed.",
        function="Break temporal correlations so gradient descent does not overwrite old knowledge with new (catastrophic forgetting).",
        mechanism="Uniform or prioritized sampling from a replay buffer (Mnih 2015).",
        cites=(MNIH, MCCLELLAND),
        analogs=(Analog("brain.circuit.hippocampus", "strong",
                        "Hippocampal replay during sleep (Wilson & McNaughton 1994) is the stated inspiration for DQN's replay buffer, and complementary-learning-systems theory (McClelland 1995) explains why both need it.",
                        (WILSON, MNIH, MCCLELLAND)),),
        order=14,
    ),
    # augmentation
    Node(
        id="ai.aug.kvcache", side="ai", level=2, name="KV cache (context window)", parent="ai.system", group="augmentation",
        description="Keys and values of every previous token in every layer, kept in accelerator memory so generation is O(n) per token instead of O(n²).",
        function="The model's working memory: what it can attend to right now.",
        mechanism="Append per token; evict or compress when the window fills.",
        cites=(VASWANI,),
        analogs=(Analog("brain.circuit.working_memory", "analogy",
                        "Prefrontal persistent activity holds ~4 items for seconds (Goldman-Rakic 1995); a KV cache holds 10⁵-10⁶ tokens losslessly. Same role, opposite constraints.",
                        (GOLDMAN, FUNAHASHI)),),
        order=15,
    ),
    Node(
        id="ai.aug.rag", side="ai", level=2, name="Retrieval-augmented generation", parent="ai.system", group="augmentation",
        description="Embed the query, fetch nearest documents from an external index, prepend them to the context.",
        function="Give the model an updatable episodic memory separate from its weights.",
        mechanism="Dense vector search over a document store; the model reads the results through attention.",
        cites=(LEWIS,),
        analogs=(Analog("brain.region.hippocampus", "analogy",
                        "Complementary learning systems: a fast, indexable episodic store (hippocampus) beside a slow statistical learner (cortex). RAG is that split built deliberately.",
                        (MCCLELLAND, LEWIS)),),
        order=16,
    ),
    Node(
        id="ai.aug.moe", side="ai", level=2, name="Mixture of experts", parent="ai.arch.blocks", group="augmentation",
        description="Each MLP is replaced by several 'experts'; a learned router sends each token to one or two of them.",
        function="Grow parameters without growing per-token compute.",
        mechanism="Top-k gating; load-balancing loss keeps experts evenly used (Shazeer 2017, Fedus 2022).",
        cites=(SHAZEER, FEDUS),
        analogs=(Analog("brain.region.networks", "analogy",
                        "Cortex has specialized modules (face area: Kanwisher 1997) and networks; but they are fixed by anatomy, not chosen per input by a gate.",
                        (KANWISHER, YEO)),),
        order=17,
    ),
    Node(
        id="ai.aug.icl", side="ai", level=2, name="In-context learning", parent="ai.system", group="augmentation",
        description="The model performs a new task from examples in its prompt with no weight change.",
        function="Fast adaptation at inference time.",
        mechanism="Implemented by attention circuits such as induction heads that copy and generalize patterns from context (Olsson 2022).",
        cites=(BROWN, OLSSON),
        analogs=(Analog("brain.region.hippocampus", "analogy",
                        "One-shot learning without slow weight change is what the hippocampus does for cortex (McClelland 1995). In the model it happens in activations, not in a separate structure.",
                        (MCCLELLAND,)),),
        order=18,
    ),
    # ---- level 3: block internals ------------------------------------------
    Node(
        id="ai.block", side="ai", level=3, name="One transformer block", parent="ai.arch.blocks", group="inference",
        description="h ← h + Attn(LN(h)); h ← h + MLP(LN(h)).",
        function="Move information between positions (attention), then transform it within each position (MLP).",
        mechanism="Two residual sub-layers with pre-normalization.",
        cites=(VASWANI, HE, BA),
        analogs=(Analog("brain.circuit.column", "analogy", "A repeated computational motif — the resemblance ends at 'repeated'.", (DOUGLAS,)),),
        order=0,
    ),
    Node(
        id="ai.block.attention", side="ai", level=3, name="Self-attention head", parent="ai.block", group="inference",
        description="For each token: a query q, and keys k_j / values v_j for every earlier token. Output = Σ_j softmax(q·k_j/√d) v_j.",
        function="Retrieve, from the whole context, the information most relevant to this position — content-addressable memory.",
        mechanism="softmax(QKᵀ/√d)V. This is exactly one update of a modern continuous Hopfield network with the stored patterns as keys/values (Ramsauer 2021).",
        cites=(VASWANI, RAMSAUER, KROTOV, DEMIRCIGIL),
        widget="modern_hopfield",
        facts=(Fact("capacity", "classic Hopfield: 0.138·d patterns; modern Hopfield/attention: exponential in d", DEMIRCIGIL),),
        analogs=(Analog("brain.circuit.hippocampus", "strong",
                        "Attention ≡ modern Hopfield update (proved, Ramsauer 2021); Hopfield nets are the standard model of CA3 autoassociative recall (Marr 1971, Treves & Rolls 1994). The proof links attention to the MODEL; the model's fit to CA3 is strong but not an equivalence.",
                        (RAMSAUER, MARR71, TREVES)),),
        order=1,
    ),
    Node(
        id="ai.block.multihead", side="ai", level=3, name="Multi-head attention", parent="ai.block", group="inference",
        description="h independent attention heads (96 in GPT-3) run in parallel on d/h-dimensional projections; their outputs are concatenated and mixed by W_O.",
        function="Let different heads attend by different criteria (syntax, coreference, position) at once.",
        mechanism="Concat(head₁…head_h)·W_O.",
        cites=(VASWANI,),
        analogs=(Analog("brain.circuit.column", "analogy", "Parallel channels with different tuning inside one motif.", (DOUGLAS,)),),
        order=2,
    ),
    Node(
        id="ai.block.induction", side="ai", level=3, name="Induction-head circuit", parent="ai.block.attention", group="inference",
        description="Two heads in consecutive layers: the first copies the previous token's identity into each position; the second attends to wherever the current token appeared before and copies what came next.",
        function="'[A][B] … [A] → [B]': the mechanism behind most in-context learning.",
        mechanism="Found by mechanistic interpretability; its emergence coincides with a sharp drop in in-context loss during training (Olsson 2022).",
        cites=(OLSSON,),
        analogs=(Analog("brain.circuit.hippocampus", "analogy",
                        "Sequence completion from a cue is what CA3 recurrent memory does; no evidence for a two-stage induction motif in the brain.",
                        (MARR71,)),),
        order=3,
    ),
    Node(
        id="ai.block.mlp", side="ai", level=3, name="MLP (feed-forward) block", parent="ai.block", group="inference",
        description="Two linear maps with a nonlinearity between: expand d → 4d, apply GELU, project back. ~2/3 of all parameters.",
        function="Per-token knowledge lookup and feature transformation; where most factual associations are stored.",
        mechanism="Each first-layer row is a key that fires on an input pattern; the matching second-layer column is the value written to the residual stream (Geva 2021).",
        cites=(VASWANI, GEVA, HENDRYCKS),
        analogs=(Analog("brain.circuit.column", "analogy",
                        "Expand-nonlinearity-compress is the cortical L4 → L2/3 → L5 shape; key-value memories resemble how cortex is thought to store semantic associations. Not demonstrated.",
                        (DOUGLAS, GEVA)),),
        order=4,
    ),
    Node(
        id="ai.block.residual", side="ai", level=3, name="Residual stream", parent="ai.block", group="inference",
        description="The d-dimensional vector per position that every block reads from and adds to; the identity path through the whole network.",
        function="A shared communication bus: any layer can write a feature that any later layer can read.",
        mechanism="h_{l+1} = h_l + f_l(h_l) (He 2016). Features live in superposition in this space (Elhage 2022).",
        cites=(HE, ELHAGE),
        analogs=(Analog("brain.region.thalamus", "analogy",
                        "A global workspace that all modules broadcast into (Dehaene 1998); thalamocortical loops are one candidate substrate. Conceptual parallel only.",
                        (DEHAENE, SHERMAN)),),
        order=5,
    ),
    Node(
        id="ai.block.norm", side="ai", level=3, name="Layer normalization", parent="ai.block", group="inference",
        description="Rescale each token's vector to zero mean and unit variance, then apply a learned gain and bias.",
        function="Keep activations in a fixed range so depth is trainable.",
        mechanism="y = γ (x − μ)/σ + β (Ba 2016).",
        cites=(BA,),
        analogs=(Analog("brain.cell.pv", "strong",
                        "Divisive normalization — a neuron's response divided by the summed activity of its pool — is a canonical computation found in retina, V1, MT and beyond (Carandini & Heeger 2012), implemented by inhibitory interneurons. Layer norm is a divisive normalization.",
                        (CARANDINI, TREMBLAY)),),
        order=6,
    ),
    # ---- level 4: units -------------------------------------------------------
    Node(
        id="ai.unit.neuron", side="ai", level=4, name="Artificial neuron", parent="ai.block.mlp", group="inference",
        description="y = φ(Σᵢ wᵢxᵢ + b): a weighted sum and a fixed nonlinearity. Every MLP unit is one of these.",
        function="Detect one pattern in its input and report how strongly it is present.",
        mechanism="McCulloch-Pitts 1943 (threshold), Rosenblatt 1958 (learnable), ReLU/GELU today.",
        cites=(MCP, ROSENBLATT, NAIR, HENDRYCKS),
        widget="mcp",
        analogs=(Analog("brain.cell.pyramidal", "analogy",
                        "Named after the neuron and abstracted from it; but one real pyramidal cell needs a 5-8-layer network to imitate (Beniaguev 2021) and its dendrites are nonlinear subunits (Polsky 2004). The 'neuron' in 'neural network' is a 1943 cartoon.",
                        (MCP, BENIAGUEV, POLSKY)),),
        order=0,
    ),
    Node(
        id="ai.unit.feature", side="ai", level=4, name="Feature (direction in activation space)", parent="ai.block.residual", group="inference",
        description="A meaningful direction in the residual stream — often not aligned with any single unit because the model stores more features than it has dimensions (superposition).",
        function="What the model actually represents: 'this is code', 'this refers to a city', 'the Golden Gate Bridge'.",
        mechanism="Recovered by sparse autoencoders trained to reconstruct activations from a sparse dictionary (Cunningham 2023).",
        cites=(ELHAGE, BRICKEN),
        analogs=(Analog("brain.cell.pyramidal", "analogy",
                        "'Concept cells' in human medial temporal lobe respond to one person across pictures, names and text (Quiroga 2005); population codes in V1 are high-dimensional (Stringer 2019). Whether cortex uses superposition the way models do is open.",
                        (QUIROGA, STRINGER)),),
        order=1,
    ),
    Node(
        id="ai.unit.attention_token", side="ai", level=4, name="Attention weight (one query-key pair)", parent="ai.block.attention", group="inference",
        description="The scalar softmax(q·k/√d) telling how much one position reads from one other position.",
        function="A dynamic, input-dependent connection — the transformer's 'fast weight'.",
        mechanism="Recomputed every forward pass from the current activations; never stored.",
        cites=(VASWANI, RAMSAUER),
        analogs=(Analog("brain.synapse.release", "analogy",
                        "Short-term synaptic dynamics make effective connection strength depend on recent activity (Tsodyks & Markram 1997) — a biological fast weight. Different timescale and mechanism.",
                        (TSODYKS,)),),
        order=2,
    ),
    # ---- level 5: parameters --------------------------------------------------
    Node(
        id="ai.param.weight", side="ai", level=5, name="Weight", parent="ai.unit.neuron", group="training",
        description="One floating-point number wᵢⱼ multiplying input i into unit j. GPT-3 has 1.75 × 10¹¹ of them.",
        function="Store everything the model has learned.",
        mechanism="Set once by gradient descent; frozen at inference.",
        cites=(BROWN, RUMELHART),
        analogs=(Analog("brain.synapse.glutamate", "strong",
                        "The weight IS the abstraction of synaptic efficacy — every neuroscience model from Hebb to Hopfield uses the same variable. Disanalogies: a synapse is stochastic, kinetic, history-dependent and keeps changing during use.",
                        (DESTEXHE, TSODYKS)),),
        order=0,
    ),
    Node(
        id="ai.param.gradient", side="ai", level=5, name="Gradient ∂L/∂w", parent="ai.param.weight", group="training",
        description="How much the loss would change per unit change of this weight; the signal that updates it.",
        function="Credit assignment: tells each weight its share of the output error.",
        mechanism="Computed by backpropagation; applied by the optimizer as Δw = −η·g.",
        cites=(RUMELHART, KINGMA),
        analogs=(Analog("brain.synapse.ltp", "analogy",
                        "LTP/LTD and STDP change synaptic strength from LOCAL activity; the gradient needs the GLOBAL error. Whether the brain approximates gradients is the central open question of the field (Lillicrap 2020).",
                        (LILLICRAP, BIPOO, MALENKA)),),
        order=1,
    ),
    Node(
        id="ai.param.activation", side="ai", level=5, name="Activation function (ReLU / GELU)", parent="ai.unit.neuron", group="inference",
        description="The fixed nonlinearity applied to each unit's weighted sum: ReLU(x) = max(0, x); GELU(x) = x·Φ(x).",
        function="Without it, any depth of network is one linear map.",
        mechanism="Elementwise; no state, no time.",
        cites=(NAIR, HENDRYCKS),
        analogs=(Analog("brain.synapse.channels", "analogy",
                        "The spike threshold set by Na⁺ channel activation is the biological nonlinearity; the HH firing-rate curve is roughly rectifying with saturation. ReLU keeps the threshold and drops the dynamics.",
                        (HH,)),),
        order=2,
    ),
    Node(
        id="ai.param.embedding", side="ai", level=5, name="Embedding vector / activation vector", parent="ai.arch.embedding", group="inference",
        description="The d-dimensional state of one token at one layer.",
        function="The model's representation of 'what this token means here'.",
        mechanism="A point in a high-dimensional space; geometry (distances, directions) carries meaning.",
        cites=(VASWANI, ELHAGE),
        analogs=(Analog("brain.cell", "analogy",
                        "A population vector across thousands of neurons; V1 population geometry is high-dimensional with a power-law spectrum (Stringer 2019).",
                        (STRINGER,)),),
        order=3,
    ),
    Node(
        id="ai.param.temperature", side="ai", level=5, name="Temperature / learning rate", parent="ai.arch.sampler", group="inference",
        description="Global scalar knobs: temperature reshapes the output distribution at inference; learning rate scales every weight update in training.",
        function="Change behaviour without changing the wiring.",
        mechanism="logits/T; Δw = −η·g.",
        cites=(KINGMA, BROWN),
        analogs=(Analog("brain.synapse.neuromod", "analogy",
                        "Neuromodulators are the brain's global knobs — dopamine as learning rate for reward learning, noradrenaline/acetylcholine as gain — each with its own receptor map (Hansen 2022).",
                        (HANSEN, SCHULTZ97)),),
        order=4,
    ),
)

EDGES: tuple[Edge, ...] = (
    # brain projections
    Edge("brain.region.thalamus", "brain.region.cortex", "projects_to", "Relay of every sense but smell into layer 4.", SHERMAN),
    Edge("brain.region.cortex", "brain.region.basal_ganglia", "projects_to", "Cortex → striatum: every area sends a copy of its plan.", ALEXANDER),
    Edge("brain.region.basal_ganglia", "brain.region.thalamus", "projects_to", "GPi/SNr inhibit thalamus; disinhibition releases action.", REDGRAVE),
    Edge("brain.region.midbrain_da", "brain.region.basal_ganglia", "modulates", "Dopamine teaching signal to striatum.", SCHULTZ97),
    Edge("brain.region.midbrain_da", "brain.region.prefrontal", "modulates", "Mesocortical dopamine.", SCHULTZ98),
    Edge("brain.region.cortex", "brain.region.hippocampus", "projects_to", "Via entorhinal cortex — the input to the trisynaptic loop.", AMARAL),
    Edge("brain.region.hippocampus", "brain.region.cortex", "teaches", "Replay consolidates episodes into cortex.", WILSON),
    Edge("brain.region.cortex", "brain.region.cerebellum", "projects_to", "Via pontine nuclei — efference copy of motor commands.", ITO),
    Edge("brain.region.cerebellum", "brain.region.thalamus", "projects_to", "Deep nuclei → VL thalamus → motor cortex.", ITO),
    Edge("brain.region.amygdala", "brain.region.prefrontal", "modulates", "Emotional value biases decision.", Cite("LeDoux JE. Brain mechanisms of emotion and emotional learning. Curr Opin Neurobiol. 1992;2(2):191-197.", "10.1016/0959-4388(92)90011-9")),
    Edge("brain.region.v1", "brain.region.cortex", "projects_to", "Start of the ventral and dorsal streams.", FELLEMAN),
    # ai data flow
    Edge("ai.arch.tokenizer", "ai.arch.embedding", "data_flow", "token ids", VASWANI),
    Edge("ai.arch.embedding", "ai.arch.position", "data_flow", "vectors", SU),
    Edge("ai.arch.position", "ai.arch.blocks", "data_flow", "residual stream in", VASWANI),
    Edge("ai.arch.blocks", "ai.arch.unembed", "data_flow", "final hidden state", VASWANI),
    Edge("ai.arch.unembed", "ai.arch.sampler", "data_flow", "probabilities", BROWN),
    Edge("ai.arch.sampler", "ai.arch.tokenizer", "data_flow", "the sampled token is appended and fed back", BROWN),
    Edge("ai.aug.kvcache", "ai.arch.blocks", "data_flow", "cached keys/values for the prefix", VASWANI),
    Edge("ai.aug.rag", "ai.arch.tokenizer", "data_flow", "retrieved documents prepended to the prompt", LEWIS),
    Edge("ai.train.data", "ai.arch.tokenizer", "data_flow", "batches of text", BROWN),
    Edge("ai.arch.unembed", "ai.train.loss", "data_flow", "logits vs actual next token", BROWN),
    Edge("ai.train.loss", "ai.train.backprop", "gradient", "∂L/∂output", RUMELHART),
    Edge("ai.train.backprop", "ai.train.optimizer", "gradient", "∂L/∂w for every weight", RUMELHART),
    Edge("ai.train.optimizer", "ai.arch.blocks", "teaches", "weight update", KINGMA),
    Edge("ai.train.rlhf", "ai.train.optimizer", "gradient", "policy gradient from reward", OUYANG),
    Edge("ai.train.replay", "ai.train.data", "data_flow", "sampling order", MNIH),
    Edge("ai.train.regularization", "ai.train.optimizer", "modulates", "dropout mask / weight decay", SRIVASTAVA),
    # block internals
    Edge("ai.block.norm", "ai.block.attention", "data_flow", "normalized input", BA),
    Edge("ai.block.attention", "ai.block.residual", "data_flow", "attention output added", HE),
    Edge("ai.block.residual", "ai.block.mlp", "data_flow", "normalized residual", GEVA),
    Edge("ai.block.mlp", "ai.block.residual", "data_flow", "MLP output added", HE),
    # circuit internals
    Edge("brain.circuit.thalamocortical", "brain.circuit.column", "projects_to", "thalamus → L4", SHERMAN),
    Edge("brain.circuit.column", "brain.circuit.thalamocortical", "projects_to", "L6 → thalamus feedback", SHERMAN),
    Edge("brain.circuit.dopamine", "brain.circuit.basal_ganglia", "modulates", "δ to striatal spines", SCHULTZ97),
)

NODES: tuple[Node, ...] = BRAIN + AI
_BY_ID: dict[str, Node] = {n.id: n for n in NODES}


def node(node_id: str) -> Node:
    return _BY_ID[node_id]


def all_dois() -> dict[str, str]:
    """DOI → owning node id (first owner wins), for scripts/verify_dois.py."""
    out: dict[str, str] = {}
    for n in NODES:
        for c in n.cites:
            if c.doi:
                out.setdefault(c.doi, n.id)
        for f in n.facts:
            if f.cite.doi:
                out.setdefault(f.cite.doi, n.id)
        for a in n.analogs:
            for c in a.cites:
                if c.doi:
                    out.setdefault(c.doi, n.id)
    for e in EDGES:
        if e.cite and e.cite.doi:
            out.setdefault(e.cite.doi, f"edge:{e.source}->{e.target}")
    return out
