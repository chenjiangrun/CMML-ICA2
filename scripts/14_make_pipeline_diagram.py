"""Create a simple pipeline diagram for the report."""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    figures_dir = Path("figures")
    figures_dir.mkdir(exist_ok=True)

    steps = [
        "Controlled\nsimulations",
        "Standardized\ncount matrices",
        "Scrublet\nDoubletFinder\nscDblFinder",
        "Metrics\nAUROC/AUPRC\nruntime",
        "Error analysis\nQC\nreport",
    ]
    fig, ax = plt.subplots(figsize=(12, 3.2))
    ax.set_axis_off()

    x_positions = [0.02, 0.22, 0.43, 0.64, 0.82]
    widths = [0.15, 0.16, 0.16, 0.15, 0.15]
    for i, (x, width, label) in enumerate(zip(x_positions, widths, steps)):
        box = FancyBboxPatch(
            (x, 0.30),
            width,
            0.40,
            boxstyle="round,pad=0.02,rounding_size=0.025",
            linewidth=1.4,
            edgecolor="#2b3a42",
            facecolor="#e8f1f2" if i % 2 == 0 else "#f4efe6",
        )
        ax.add_patch(box)
        ax.text(x + width / 2, 0.50, label, ha="center", va="center", fontsize=11)
        if i < len(steps) - 1:
            ax.annotate(
                "",
                xy=(x_positions[i + 1] - 0.018, 0.50),
                xytext=(x + width + 0.018, 0.50),
                arrowprops=dict(arrowstyle="->", lw=1.5, color="#2b3a42"),
            )

    ax.text(0.5, 0.88, "Reproducible doublet-detection benchmark workflow", ha="center", fontsize=14, weight="bold")
    fig.tight_layout()
    fig.savefig(figures_dir / "pipeline_workflow.png", dpi=300)
    plt.close(fig)
    print("Wrote figures/pipeline_workflow.png")


if __name__ == "__main__":
    main()
