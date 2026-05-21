#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  .libPaths(unique(c("C:/Rlibs", .libPaths())))
  library(Matrix)
  library(Seurat)
  library(DoubletFinder)
})

args <- commandArgs(trailingOnly = TRUE)
processed_dir <- ifelse(length(args) >= 1, args[[1]], "data/processed")
output_dir <- ifelse(length(args) >= 2, args[[2]], "results/method_predictions")
pK_value <- ifelse(length(args) >= 3, as.numeric(args[[3]]), 0.1)
dataset_filter <- ifelse(length(args) >= 4, args[[4]], "")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

doublet_finder_compat <- function(seu, PCs, pN, pK, nExp) {
  real_cells <- rownames(seu@meta.data)
  counts <- SeuratObject::LayerData(seu, assay = "RNA", layer = "counts")
  data <- counts[, real_cells]
  n_real <- length(real_cells)
  n_doublets <- round(n_real / (1 - pN) - n_real)

  set.seed(7)
  real_cells1 <- sample(real_cells, n_doublets, replace = TRUE)
  real_cells2 <- sample(real_cells, n_doublets, replace = TRUE)
  doublets <- (data[, real_cells1] + data[, real_cells2]) / 2
  colnames(doublets) <- paste0("artificial_doublet_", seq_len(n_doublets))
  data_wdoublets <- cbind(data, doublets)

  seu_wdoublets <- CreateSeuratObject(counts = data_wdoublets)
  seu_wdoublets <- NormalizeData(seu_wdoublets, verbose = FALSE)
  seu_wdoublets <- FindVariableFeatures(seu_wdoublets, verbose = FALSE)
  seu_wdoublets <- ScaleData(seu_wdoublets, verbose = FALSE)
  seu_wdoublets <- RunPCA(seu_wdoublets, npcs = max(PCs), verbose = FALSE)

  pca_coord <- seu_wdoublets@reductions$pca@cell.embeddings[, PCs, drop = FALSE]
  dist_mat <- fields::rdist(pca_coord)
  n_cells <- nrow(pca_coord)
  k <- max(1, round(n_cells * pK))

  pANN <- numeric(n_real)
  for (i in seq_len(n_real)) {
    neighbors <- order(dist_mat[, i])
    neighbors <- neighbors[2:(k + 1)]
    pANN[i] <- sum(neighbors > n_real) / k
  }

  classifications <- rep("Singlet", n_real)
  nExp <- min(max(1, nExp), n_real)
  classifications[order(pANN, decreasing = TRUE)[seq_len(nExp)]] <- "Doublet"

  pANN_col <- paste("pANN", pN, pK, nExp, sep = "_")
  class_col <- paste("DF.classifications", pN, pK, nExp, sep = "_")
  seu@meta.data[, pANN_col] <- pANN
  seu@meta.data[, class_col] <- classifications
  seu
}

run_one <- function(dataset_dir) {
  dataset_id <- basename(dataset_dir)
  counts <- readMM(file.path(dataset_dir, "counts.mtx"))
  genes <- read.table(file.path(dataset_dir, "genes.tsv"), stringsAsFactors = FALSE)[, 1]
  cells <- read.table(file.path(dataset_dir, "cells.tsv"), stringsAsFactors = FALSE)[, 1]
  metadata <- read.csv(file.path(dataset_dir, "metadata.csv"), stringsAsFactors = FALSE)

  rownames(counts) <- make.unique(genes)
  colnames(counts) <- cells
  expected_rate <- mean(tolower(metadata$ground_truth) == "doublet")
  expected_doublets <- max(1, round(ncol(counts) * expected_rate))

  start <- proc.time()[["elapsed"]]
  seu <- CreateSeuratObject(counts = counts, meta.data = metadata)
  seu <- NormalizeData(seu, verbose = FALSE)
  seu <- FindVariableFeatures(seu, verbose = FALSE)
  seu <- ScaleData(seu, verbose = FALSE)
  seu <- RunPCA(seu, npcs = 30, verbose = FALSE)
  seu <- FindNeighbors(seu, dims = 1:20, verbose = FALSE)
  seu <- FindClusters(seu, resolution = 0.5, verbose = FALSE)

  # The default pK keeps the benchmark reproducible across DoubletFinder/Seurat
  # versions; optional command-line values are used for sensitivity checks.
  pK <- pK_value

  cluster_labels <- as.vector(seu[["seurat_clusters"]][, 1])
  homotypic_prop <- modelHomotypic(cluster_labels)
  adjusted_n <- max(1, round(expected_doublets * (1 - homotypic_prop)))
  seu <- doublet_finder_compat(
    seu,
    PCs = 1:20,
    pN = 0.25,
    pK = pK,
    nExp = adjusted_n
  )
  runtime <- proc.time()[["elapsed"]] - start

  class_col <- grep("^DF.classifications", colnames(seu@meta.data), value = TRUE)[1]
  score_col <- grep("^pANN", colnames(seu@meta.data), value = TRUE)[1]
  classes <- ifelse(seu@meta.data[[class_col]] == "Doublet", "doublet", "singlet")
  scores <- seu@meta.data[[score_col]]

  out <- data.frame(
    cell_id = colnames(seu),
    method = "DoubletFinder",
    score = scores,
    prediction = classes,
    runtime_seconds = runtime
  )
  write.csv(out, file.path(output_dir, paste0(dataset_id, "__DoubletFinder.csv")), row.names = FALSE)
  message("DoubletFinder complete: ", dataset_id)
}

dataset_dirs <- list.dirs(processed_dir, recursive = FALSE, full.names = TRUE)
if (nzchar(dataset_filter)) {
  requested <- trimws(strsplit(dataset_filter, ",", fixed = TRUE)[[1]])
  dataset_dirs <- dataset_dirs[basename(dataset_dirs) %in% requested]
}
if (length(dataset_dirs) == 0) {
  stop("No matching datasets found for DoubletFinder run")
}
for (dataset_dir in dataset_dirs) {
  run_one(dataset_dir)
}
