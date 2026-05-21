# Miniproject 7 Assignment Requirements

Source files are archived in `assignment/`.

## Assignment

Miniproject 7: Benchmarking doublet detection methods in single-cell RNA-seq
data.

Assigned student: 3127.

## Key Requirements Extracted From the Brief

- Understand doublets in single-cell sequencing, their sources, and their
  impacts on data quality and biological interpretation.
- Choose a publicly available scRNA-seq dataset with ground-truth doublet
  information, or use simulated datasets designed for doublet detection.
- Perform basic preprocessing, including quality control, normalization, and
  filtering.
- Explore computational methods for doublet detection:
  - DoubletFinder (CPU + R)
  - Scrublet (CPU + Python)
  - scDblFinder (CPU + R)
  - Solo is optional
- Benchmark methods using metrics such as:
  - precision
  - recall
  - F1 score
  - downstream impact such as clustering and differential expression
- Compare results against known doublet labels.
- Compile a comprehensive report detailing methods, results, insights,
  biological implications, and limitations.

## Consequence for This Project

The strongest alignment is to make the Xi and Li real benchmark datasets the
main analysis, because they are public scRNA-seq datasets with experimentally
annotated doublet labels. Controlled simulations are useful as supporting
analysis, but should not replace the real-data benchmark.
