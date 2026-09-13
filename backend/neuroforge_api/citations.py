"""Canonical citation registry for NeuroForge.

Every published reference NeuroForge depends on lives here, with its full
metadata + DOI. Used by:
  - the BibTeX export endpoint (/api/citations/bibtex)
  - scripts/verify_dois.py (CI gate that resolves each DOI)

Anti-theater: every entry MUST correspond to a real published work. New
entries belong here only if a module imports / cites them at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Reference:
    bibtex_key: str
    entry_type: str  # "article", "book", "incollection", "techreport", etc.
    fields: dict[str, str]
    doi: str | None
    used_by: tuple[str, ...]  # which NeuroForge module(s) cite this

    def to_bibtex(self) -> str:
        body = ",\n".join(f"  {k} = {{{v}}}" for k, v in self.fields.items())
        return f"@{self.entry_type}{{{self.bibtex_key},\n{body}\n}}"


REFERENCES: tuple[Reference, ...] = (
    Reference(
        bibtex_key="hodgkin1952quantitative",
        entry_type="article",
        fields={
            "author": "Hodgkin, A. L. and Huxley, A. F.",
            "title": "A quantitative description of membrane current and its application to conduction and excitation in nerve",
            "journal": "The Journal of Physiology",
            "volume": "117",
            "number": "4",
            "pages": "500--544",
            "year": "1952",
            "doi": "10.1113/jphysiol.1952.sp004764",
        },
        doi="10.1113/jphysiol.1952.sp004764",
        used_by=("hodgkin_huxley",),
    ),
    Reference(
        bibtex_key="bipoo1998synaptic",
        entry_type="article",
        fields={
            "author": "Bi, Guo-qiang and Poo, Mu-ming",
            "title": "Synaptic modifications in cultured hippocampal neurons: dependence on spike timing, synaptic strength, and postsynaptic cell type",
            "journal": "Journal of Neuroscience",
            "volume": "18",
            "number": "24",
            "pages": "10464--10472",
            "year": "1998",
            "doi": "10.1523/JNEUROSCI.18-24-10464.1998",
        },
        doi="10.1523/JNEUROSCI.18-24-10464.1998",
        used_by=("stdp",),
    ),
    Reference(
        bibtex_key="hubelwiesel1962receptive",
        entry_type="article",
        fields={
            "author": "Hubel, D. H. and Wiesel, T. N.",
            "title": "Receptive fields, binocular interaction and functional architecture in the cat's visual cortex",
            "journal": "The Journal of Physiology",
            "volume": "160",
            "number": "1",
            "pages": "106--154",
            "year": "1962",
            "doi": "10.1113/jphysiol.1962.sp006837",
        },
        doi="10.1113/jphysiol.1962.sp006837",
        used_by=("hubel_wiesel",),
    ),
    Reference(
        bibtex_key="daugman1980two",
        entry_type="article",
        fields={
            "author": "Daugman, John G.",
            "title": "Two-dimensional spectral analysis of cortical receptive field profiles",
            "journal": "Vision Research",
            "volume": "20",
            "number": "10",
            "pages": "847--856",
            "year": "1980",
            "doi": "10.1016/0042-6989(80)90065-6",
        },
        doi="10.1016/0042-6989(80)90065-6",
        used_by=("hubel_wiesel",),
    ),
    Reference(
        bibtex_key="adelsonbergen1985spatiotemporal",
        entry_type="article",
        fields={
            "author": "Adelson, Edward H. and Bergen, James R.",
            "title": "Spatiotemporal energy models for the perception of motion",
            "journal": "Journal of the Optical Society of America A",
            "volume": "2",
            "number": "2",
            "pages": "284--299",
            "year": "1985",
            "doi": "10.1364/JOSAA.2.000284",
        },
        doi="10.1364/JOSAA.2.000284",
        used_by=("hubel_wiesel",),
    ),
    Reference(
        bibtex_key="lecun1989backpropagation",
        entry_type="article",
        fields={
            "author": "LeCun, Y. and Boser, B. and Denker, J. S. and Henderson, D. and Howard, R. E. and Hubbard, W. and Jackel, L. D.",
            "title": "Backpropagation Applied to Handwritten Zip Code Recognition",
            "journal": "Neural Computation",
            "volume": "1",
            "number": "4",
            "pages": "541--551",
            "year": "1989",
            "doi": "10.1162/neco.1989.1.4.541",
        },
        doi="10.1162/neco.1989.1.4.541",
        used_by=("hubel_wiesel",),
    ),
    Reference(
        bibtex_key="hebb1949organization",
        entry_type="book",
        fields={
            "author": "Hebb, Donald O.",
            "title": "The Organization of Behavior",
            "publisher": "Wiley",
            "year": "1949",
            "address": "New York",
        },
        doi=None,
        used_by=("hebbian",),
    ),
    Reference(
        bibtex_key="blisslomo1973long",
        entry_type="article",
        fields={
            "author": "Bliss, T. V. P. and L{\\o}mo, T.",
            "title": "Long-lasting potentiation of synaptic transmission in the dentate area of the anaesthetized rabbit following stimulation of the perforant path",
            "journal": "The Journal of Physiology",
            "volume": "232",
            "number": "2",
            "pages": "331--356",
            "year": "1973",
            "doi": "10.1113/jphysiol.1973.sp010273",
        },
        doi="10.1113/jphysiol.1973.sp010273",
        used_by=("hebbian",),
    ),
    Reference(
        bibtex_key="oja1982simplified",
        entry_type="article",
        fields={
            "author": "Oja, Erkki",
            "title": "A simplified neuron model as a principal component analyzer",
            "journal": "Journal of Mathematical Biology",
            "volume": "15",
            "number": "3",
            "pages": "267--273",
            "year": "1982",
            "doi": "10.1007/BF00275687",
        },
        doi="10.1007/BF00275687",
        used_by=("hebbian",),
    ),
    Reference(
        bibtex_key="hopfield1982neural",
        entry_type="article",
        fields={
            "author": "Hopfield, J. J.",
            "title": "Neural networks and physical systems with emergent collective computational abilities",
            "journal": "Proceedings of the National Academy of Sciences",
            "volume": "79",
            "number": "8",
            "pages": "2554--2558",
            "year": "1982",
            "doi": "10.1073/pnas.79.8.2554",
            "note": "Nobel Prize in Physics 2024",
        },
        doi="10.1073/pnas.79.8.2554",
        used_by=("hopfield",),
    ),
    Reference(
        bibtex_key="amitgutfreundsompolinsky1987statistical",
        entry_type="article",
        fields={
            "author": "Amit, Daniel J. and Gutfreund, Hanoch and Sompolinsky, H.",
            "title": "Statistical mechanics of neural networks near saturation",
            "journal": "Annals of Physics",
            "volume": "173",
            "number": "1",
            "pages": "30--67",
            "year": "1987",
            "doi": "10.1016/0003-4916(87)90092-3",
        },
        doi="10.1016/0003-4916(87)90092-3",
        used_by=("hopfield",),
    ),
    Reference(
        bibtex_key="ramsauer2021hopfield",
        entry_type="inproceedings",
        fields={
            "author": "Ramsauer, Hubert and Sch{\\\"a}fl, Bernhard and Lehner, Johannes and Seidl, Philipp and Widrich, Michael and Adler, Thomas and Gruber, Lukas and Holzleitner, Markus and Pavlovi{\\'c}, Milena and Sandve, Geir Kjetil and others",
            "title": "Hopfield Networks is All You Need",
            "booktitle": "International Conference on Learning Representations (ICLR)",
            "year": "2021",
            "doi": "10.48550/arXiv.2008.02217",
        },
        doi="10.48550/arXiv.2008.02217",
        used_by=("hopfield", "modern_hopfield"),
    ),
    Reference(
        bibtex_key="krotovhopfield2016dense",
        entry_type="inproceedings",
        fields={
            "author": "Krotov, Dmitry and Hopfield, John J.",
            "title": "Dense Associative Memory for Pattern Recognition",
            "booktitle": "Advances in Neural Information Processing Systems (NeurIPS)",
            "year": "2016",
            "doi": "10.48550/arXiv.1606.01164",
        },
        doi="10.48550/arXiv.1606.01164",
        used_by=("modern_hopfield",),
    ),
    Reference(
        bibtex_key="demircigil2017huge",
        entry_type="article",
        fields={
            "author": "Demircigil, Mete and Heusel, Judith and L{\\\"o}we, Matthias and Upgang, Sven and Vermet, Franck",
            "title": "On a Model of Associative Memory with Huge Storage Capacity",
            "journal": "Journal of Statistical Physics",
            "volume": "168",
            "number": "2",
            "pages": "288--299",
            "year": "2017",
            "doi": "10.1007/s10955-017-1806-y",
        },
        doi="10.1007/s10955-017-1806-y",
        used_by=("modern_hopfield",),
    ),
    Reference(
        bibtex_key="schultzdayanmontague1997",
        entry_type="article",
        fields={
            "author": "Schultz, Wolfram and Dayan, Peter and Montague, P. Read",
            "title": "A Neural Substrate of Prediction and Reward",
            "journal": "Science",
            "volume": "275",
            "number": "5306",
            "pages": "1593--1599",
            "year": "1997",
            "doi": "10.1126/science.275.5306.1593",
        },
        doi="10.1126/science.275.5306.1593",
        used_by=("dopamine_rpe",),
    ),
    Reference(
        bibtex_key="montague1996framework",
        entry_type="article",
        fields={
            "author": "Montague, P. Read and Dayan, Peter and Sejnowski, Terrence J.",
            "title": "A framework for mesencephalic dopamine systems based on predictive Hebbian learning",
            "journal": "Journal of Neuroscience",
            "volume": "16",
            "number": "5",
            "pages": "1936--1947",
            "year": "1996",
            "doi": "10.1523/JNEUROSCI.16-05-01936.1996",
        },
        doi="10.1523/JNEUROSCI.16-05-01936.1996",
        used_by=("dopamine_rpe",),
    ),
    Reference(
        bibtex_key="sutton1988td",
        entry_type="article",
        fields={
            "author": "Sutton, Richard S.",
            "title": "Learning to predict by the methods of temporal differences",
            "journal": "Machine Learning",
            "volume": "3",
            "number": "1",
            "pages": "9--44",
            "year": "1988",
            "doi": "10.1007/BF00115009",
        },
        doi="10.1007/BF00115009",
        used_by=("dopamine_rpe",),
    ),
    Reference(
        bibtex_key="schultz1998predictive",
        entry_type="article",
        fields={
            "author": "Schultz, Wolfram",
            "title": "Predictive Reward Signal of Dopamine Neurons",
            "journal": "Journal of Neurophysiology",
            "volume": "80",
            "number": "1",
            "pages": "1--27",
            "year": "1998",
            "doi": "10.1152/jn.1998.80.1.1",
        },
        doi="10.1152/jn.1998.80.1.1",
        used_by=("dopamine_rpe",),
    ),
    Reference(
        bibtex_key="dabney2020distributional",
        entry_type="article",
        fields={
            "author": "Dabney, Will and Kurth-Nelson, Zeb and Uchida, Naoshige and Starkweather, Clara Kwon and Hassabis, Demis and Munos, R{\\'e}mi and Botvinick, Matthew",
            "title": "A distributional code for value in dopamine-based reinforcement learning",
            "journal": "Nature",
            "volume": "577",
            "number": "7792",
            "pages": "671--675",
            "year": "2020",
            "doi": "10.1038/s41586-019-1924-6",
        },
        doi="10.1038/s41586-019-1924-6",
        used_by=("dopamine_rpe",),
    ),
    Reference(
        bibtex_key="destexhe1994efficient",
        entry_type="article",
        fields={
            "author": "Destexhe, Alain and Mainen, Zachary F. and Sejnowski, Terrence J.",
            "title": "An Efficient Method for Computing Synaptic Conductances Based on a Kinetic Model of Receptor Binding",
            "journal": "Neural Computation",
            "volume": "6",
            "number": "1",
            "pages": "14--18",
            "year": "1994",
            "doi": "10.1162/neco.1994.6.1.14",
        },
        doi="10.1162/neco.1994.6.1.14",
        used_by=("synapse",),
    ),
    Reference(
        bibtex_key="jahrstevens1990voltage",
        entry_type="article",
        fields={
            "author": "Jahr, Craig E. and Stevens, Charles F.",
            "title": "Voltage dependence of NMDA-activated macroscopic conductances predicted by single-channel kinetics",
            "journal": "Journal of Neuroscience",
            "volume": "10",
            "number": "9",
            "pages": "3178--3182",
            "year": "1990",
            "doi": "10.1523/JNEUROSCI.10-09-03178.1990",
        },
        doi="10.1523/JNEUROSCI.10-09-03178.1990",
        used_by=("synapse",),
    ),
    Reference(
        bibtex_key="collingridge1983excitatory",
        entry_type="article",
        fields={
            "author": "Collingridge, G. L. and Kehl, S. J. and McLennan, H.",
            "title": "Excitatory amino acids in synaptic transmission in the Schaffer collateral-commissural pathway of the rat hippocampus",
            "journal": "The Journal of Physiology",
            "volume": "334",
            "number": "1",
            "pages": "33--46",
            "year": "1983",
            "doi": "10.1113/jphysiol.1983.sp014478",
        },
        doi="10.1113/jphysiol.1983.sp014478",
        used_by=("synapse",),
    ),
    Reference(
        bibtex_key="mccullochpitts1943logical",
        entry_type="article",
        fields={
            "author": "McCulloch, Warren S. and Pitts, Walter",
            "title": "A logical calculus of the ideas immanent in nervous activity",
            "journal": "The Bulletin of Mathematical Biophysics",
            "volume": "5",
            "number": "4",
            "pages": "115--133",
            "year": "1943",
            "doi": "10.1007/BF02478259",
        },
        doi="10.1007/BF02478259",
        used_by=("mcp",),
    ),
    Reference(
        bibtex_key="minskypapert1969perceptrons",
        entry_type="book",
        fields={
            "author": "Minsky, Marvin and Papert, Seymour",
            "title": "Perceptrons: An Introduction to Computational Geometry",
            "publisher": "MIT Press",
            "year": "1969",
            "address": "Cambridge, MA",
        },
        doi=None,
        used_by=("mcp",),
    ),
    Reference(
        bibtex_key="rumelhart1986learning",
        entry_type="article",
        fields={
            "author": "Rumelhart, David E. and Hinton, Geoffrey E. and Williams, Ronald J.",
            "title": "Learning representations by back-propagating errors",
            "journal": "Nature",
            "volume": "323",
            "number": "6088",
            "pages": "533--536",
            "year": "1986",
            "doi": "10.1038/323533a0",
        },
        doi="10.1038/323533a0",
        used_by=("mcp",),
    ),
)


def all_dois() -> list[str]:
    """All DOIs cited in NeuroForge that should resolve at doi.org."""
    return [r.doi for r in REFERENCES if r.doi]


def to_bibtex_dump() -> str:
    """Produce a single .bib-formatted string of every reference."""
    return "\n\n".join(r.to_bibtex() for r in REFERENCES) + "\n"
