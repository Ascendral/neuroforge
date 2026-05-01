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
        },
        doi=None,
        used_by=("hopfield",),
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
