# assets-creator.py

"""
This script creates visualisation charts/plots/infographics for the Bengaluru Cable Network project.
You can choose which visualisations to generate using command-line arguments.
It can also save outputs as PNG or SVG files in the same directory.

Usage:
    - Generate only Seaborn bar chart:
    ```powershell
    uv run python assets-creator.py --charts seaborn
    ```

    - Plotly bar + radar charts together
    ```powershell
    uv run python assets-creator.py --charts plotly-bar plotly-radar
    ```

    - Generate all charts:
    ```powershell
    uv run python assets-creator.py --charts seaborn plotly-bar plotly-radar
    ```

    - With file outputs:
    ```powershell
    uv run python assets-creator.py --charts plotly-radar --output png
    uv run python assets-creator.py --charts seaborn plotly-bar plotly-radar --output svg
    ```
"""

import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# -----------------------------
# Sample dataset
# -----------------------------
data = {
    "Component": ["Electromagnetic Tower", "Micro Transport Pod", "Building System", "Cable per km"],
    "Cable Network": [115, 0.45, 7.5, 150],
    "Conventional System": [350, 2.5, 25, 500]
}
df = pd.DataFrame(data)
df_melted = df.melt(id_vars="Component", var_name="System", value_name="Cost")

# -----------------------------
# Visualization functions
# -----------------------------
def seaborn_bar(df_melted, output=None):
    """Static grouped bar chart using Seaborn/Matplotlib."""
    plt.figure(figsize=(8, 5))
    sns.barplot(data=df_melted, x="Component", y="Cost", hue="System")
    plt.title("Manufacturing Cost per Unit vs Conventional (Seaborn)")
    plt.xticks(rotation=30)
    plt.tight_layout()
    if output:
        plt.savefig(f"seaborn_bar.{output}", format=output)
    else:
        plt.show()
    plt.close()

def plotly_bar(df_melted, output=None):
    """Interactive grouped bar chart using Plotly Express."""
    fig = px.bar(df_melted, x="Component", y="Cost", color="System",
                 barmode="group", title="Manufacturing Cost per Unit vs Conventional (Plotly)")
    if output:
        fig.write_image(f"plotly_bar.{output}")
    else:
        fig.show()

def plotly_radar(df, output=None):
    """Radar/spider chart comparing Cable Network vs Conventional System."""
    categories = df["Component"]
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=df["Cable Network"],
        theta=categories,
        fill='toself',
        name='Cable Network'
    ))
    fig.add_trace(go.Scatterpolar(
        r=df["Conventional System"],
        theta=categories,
        fill='toself',
        name='Conventional System'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 500])),
        title="Radar Comparison of Manufacturing Costs"
    )
    if output:
        fig.write_image(f"plotly_radar.{output}")
    else:
        fig.show()

# -----------------------------
# Main function with args
# -----------------------------
def create_assets(charts, output):
    if "seaborn" in charts:
        seaborn_bar(df_melted, output)
    if "plotly-bar" in charts:
        plotly_bar(df_melted, output)
    if "plotly-radar" in charts:
        plotly_radar(df, output)

def main():
    parser = argparse.ArgumentParser(description="Generate visualisations for Bengaluru Cable Network project.")
    parser.add_argument(
        "--charts",
        nargs="+",
        choices=["seaborn", "plotly-bar", "plotly-radar"],
        default=["seaborn"],
        help="Choose one or more charts to generate."
    )
    parser.add_argument(
        "--output",
        choices=["png", "svg"],
        help="Save charts as PNG or SVG instead of showing interactively."
    )
    args = parser.parse_args()
    create_assets(args.charts, args.output)

if __name__ == "__main__":
    main()