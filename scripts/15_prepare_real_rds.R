#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  .libPaths(unique(c("C:/Rlibs", .libPaths())))
  library(Matrix)
})

args <- commandArgs(trailingOnly = TRUE)
input_dir <- ifelse(length(args) >= 1, args[[1]], "data/raw/real_datasets")
output_dir <- ifelse(length(args) >= 2, args[[2]], "data/processed_real")
max_datasets <- ifelse(length(args) >= 3, as.integer(args[[3]]), 2L)
max_cells <- ifelse(length(args) >= 4, as.integer(args[[4]]), 3000L)
requested <- ifelse(length(args) >= 5, args[[5]], "")

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

write_standard_dataset <- function(dataset_id, counts, labels, output_dir, max_cells) {
  if (nrow(counts) > ncol(counts)) {
    # Expected orientation is genes x cells. This branch is only a guard for
    # unusually shaped inputs and does not transpose typical scRNA-seq matrices.
    counts <- counts
  }

  labels <- as.character(labels)
  if (length(labels) != ncol(counts)) {
    stop(dataset_id, ": label length does not match number of cells")
  }

  keep <- seq_len(ncol(counts))
  if (!is.na(max_cells) && ncol(counts) > max_cells) {
    set.seed(7)
    positives <- which(tolower(labels) == "doublet")
    negatives <- which(tolower(labels) != "doublet")
    n_pos <- min(length(positives), ceiling(max_cells * 0.35))
    n_neg <- max_cells - n_pos
    keep <- sort(c(
      sample(positives, n_pos),
      sample(negatives, min(length(negatives), n_neg))
    ))
  }

  counts <- counts[, keep, drop = FALSE]
  labels <- labels[keep]
  labels <- ifelse(tolower(labels) == "doublet", "doublet", "singlet")

  dataset_dir <- file.path(output_dir, dataset_id)
  dir.create(dataset_dir, recursive = TRUE, showWarnings = FALSE)

  if (is.null(rownames(counts))) {
    rownames(counts) <- paste0("gene_", seq_len(nrow(counts)))
  }
  if (is.null(colnames(counts))) {
    colnames(counts) <- paste0(dataset_id, "_cell_", seq_len(ncol(counts)))
  }

  writeMM(as(counts, "dgCMatrix"), file.path(dataset_dir, "counts.mtx"))
  write.table(rownames(counts), file.path(dataset_dir, "genes.tsv"),
              quote = FALSE, row.names = FALSE, col.names = FALSE)
  write.table(colnames(counts), file.path(dataset_dir, "cells.tsv"),
              quote = FALSE, row.names = FALSE, col.names = FALSE)
  metadata <- data.frame(
    cell_id = colnames(counts),
    ground_truth = labels,
    source_dataset = dataset_id,
    n_counts = Matrix::colSums(counts),
    n_genes = Matrix::colSums(counts > 0),
    stringsAsFactors = FALSE
  )
  write.csv(metadata, file.path(dataset_dir, "metadata.csv"), row.names = FALSE)
  message("Prepared real dataset: ", dataset_id, " (", ncol(counts), " cells)")
}

extract_count_label <- function(obj) {
  if (is.list(obj) && all(c("count", "label") %in% names(obj))) {
    return(list(counts = obj$count, labels = obj$label))
  }
  if (is.list(obj) && all(c("counts", "labels") %in% names(obj))) {
    return(list(counts = obj$counts, labels = obj$labels))
  }
  if (is.list(obj) && length(obj) >= 2) {
    return(list(counts = obj[[1]], labels = obj[[2]]))
  }
  stop("Unsupported RDS structure")
}

rds_files <- list.files(input_dir, pattern = "\\.rds$", recursive = TRUE, full.names = TRUE)
if (length(rds_files) == 0) {
  stop("No .rds files found under ", input_dir)
}

if (nzchar(requested)) {
  requested_ids <- strsplit(requested, ",", fixed = TRUE)[[1]]
  requested_ids <- trimws(requested_ids)
  rds_files <- rds_files[tools::file_path_sans_ext(basename(rds_files)) %in% requested_ids]
  missing <- setdiff(requested_ids, tools::file_path_sans_ext(basename(rds_files)))
  if (length(missing) > 0) {
    stop("Requested datasets not found: ", paste(missing, collapse = ", "))
  }
} else {
  rds_files <- head(sort(rds_files), max_datasets)
}
for (path in rds_files) {
  dataset_id <- tools::file_path_sans_ext(basename(path))
  obj <- readRDS(path)
  parsed <- extract_count_label(obj)
  counts <- parsed$counts
  labels <- parsed$labels
  if (!inherits(counts, "Matrix")) {
    counts <- Matrix(as.matrix(counts), sparse = TRUE)
  }
  write_standard_dataset(dataset_id, counts, labels, output_dir, max_cells)
}
