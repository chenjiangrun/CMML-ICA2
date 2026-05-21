#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  .libPaths(unique(c("C:/Rlibs", .libPaths())))
  library(Matrix)
  library(SingleCellExperiment)
  library(scDblFinder)
})

args <- commandArgs(trailingOnly = TRUE)
processed_dir <- ifelse(length(args) >= 1, args[[1]], "data/processed")
output_dir <- ifelse(length(args) >= 2, args[[2]], "results/method_predictions")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

run_one <- function(dataset_dir) {
  dataset_id <- basename(dataset_dir)
  counts <- readMM(file.path(dataset_dir, "counts.mtx"))
  genes <- read.table(file.path(dataset_dir, "genes.tsv"), stringsAsFactors = FALSE)[, 1]
  cells <- read.table(file.path(dataset_dir, "cells.tsv"), stringsAsFactors = FALSE)[, 1]

  rownames(counts) <- make.unique(genes)
  colnames(counts) <- cells

  start <- proc.time()[["elapsed"]]
  set.seed(7)
  sce <- SingleCellExperiment(list(counts = counts))
  sce <- scDblFinder(sce)
  runtime <- proc.time()[["elapsed"]] - start

  out <- data.frame(
    cell_id = colnames(sce),
    method = "scDblFinder",
    score = colData(sce)$scDblFinder.score,
    prediction = ifelse(colData(sce)$scDblFinder.class == "doublet", "doublet", "singlet"),
    runtime_seconds = runtime
  )
  write.csv(out, file.path(output_dir, paste0(dataset_id, "__scDblFinder.csv")), row.names = FALSE)
  message("scDblFinder complete: ", dataset_id)
}

dataset_dirs <- list.dirs(processed_dir, recursive = FALSE, full.names = TRUE)
for (dataset_dir in dataset_dirs) {
  run_one(dataset_dir)
}
