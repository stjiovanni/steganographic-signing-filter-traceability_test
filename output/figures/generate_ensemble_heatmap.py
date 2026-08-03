import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import os

# Read the CSV
df = pd.read_csv('output/results/ensemble_decision_matrix.csv')

print("Column names:", df.columns.tolist())
print("\nFirst 5 rows:")
print(df.head())
print(f"\nTotal rows: {len(df)}")
print(f"Unique transforms: {df['transform_name'].nunique()}")
print(f"Unique transforms: {df['transform_name'].unique()}")
print(f"Best method counts:\n{df['best_method'].value_counts()}")

# Create pivot table: transform x best_method (count of wins per transform)
# Since best_method is always 'trustmark', we'll show win counts per transform per method
pivot = df.groupby(['transform_name', 'best_method']).size().unstack(fill_value=0)

# Ensure all methods are present as columns
methods = ['trustmark', 'hash', 'lsb', 'dct']
for m in methods:
    if m not in pivot.columns:
        pivot[m] = 0

# Reorder columns
pivot = pivot[methods]

# Also create a pivot showing the winning method per transform (mode)
transform_winner = df.groupby('transform_name')['best_method'].agg(lambda x: x.mode().iloc[0])

print("\nTransform winners:")
print(transform_winner)
print(f"\nTransform winner counts:\n{transform_winner.value_counts()}")

# Create a winner matrix for heatmap: transform x method, value = 1 if winner else 0
winner_matrix = pd.DataFrame(0, index=pivot.index, columns=methods)
for idx, row in pivot.iterrows():
    winner = row.idxmax()  # method with max count (always trustmark here)
    winner_matrix.loc[idx, winner] = row[winner]

# Also create intensity-weighted matrix showing win counts per transform per method
win_counts = pivot.copy()

# --- Create the heatmap ---
fig, ax = plt.subplots(figsize=(10, 10))

# Use viridis colormap (colorblind-safe)
cmap = plt.cm.viridis

# Normalize by max wins per transform for better color variation
norm_data = win_counts.div(win_counts.max(axis=1), axis=0).replace([np.inf, -np.inf], 0).fillna(0)

# Create heatmap
im = ax.imshow(norm_data.values, aspect='auto', cmap=cmap, vmin=0, vmax=1)

# Set ticks and labels
ax.set_xticks(range(len(methods)))
ax.set_xticklabels([m.capitalize() for m in methods], fontsize=11)
ax.set_yticks(range(len(win_counts.index)))
ax.set_yticklabels([t.replace('_', ' ').title() for t in win_counts.index], fontsize=10)

# Label every cell with winning method name and count
for i in range(len(win_counts.index)):
    for j in range(len(methods)):
        count = win_counts.iloc[i, j]
        if count > 0:
            method_name = methods[j].capitalize()
            text = f"{method_name}\n({int(count)})"
        else:
            text = "—"
        color = 'white' if norm_data.iloc[i, j] > 0.5 else 'black'
        ax.text(j, i, text, ha='center', va='center', fontsize=9, color=color, fontweight='bold' if count > 0 else 'normal')

# Title and labels
ax.set_title("Ensemble Decision Matrix: Best-Performing Method by Transform (n=100 images)", 
             fontsize=13, fontweight='bold', pad=15)
ax.set_xlabel("Method", fontsize=11, fontweight='bold')
ax.set_ylabel("Transform", fontsize=11, fontweight='bold')

# Colorbar
cbar = plt.colorbar(im, ax=ax, shrink=0.6, aspect=20)
cbar.set_label('Normalized Win Count per Transform', fontsize=10)

plt.tight_layout()

# Save
os.makedirs('output/figures', exist_ok=True)
plt.savefig('output/figures/ensemble_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nHeatmap saved to output/figures/ensemble_heatmap.png")

# Report findings
print("\n=== REPORT ===")
print(f"Total transform-intensity combinations tested: {len(df)}")
print(f"Unique transforms: {len(df['transform_name'].unique())}")
print(f"\nBest method overall winner: {df['best_method'].mode().iloc[0].capitalize()} (wins {df['best_method'].value_counts().iloc[0]}/{len(df)} = {100*df['best_method'].value_counts().iloc[0]/len(df):.1f}%)")
print(f"\nMethod win counts across all transforms:")
print(df['best_method'].value_counts())
print(f"\nWin counts per transform:")
print(win_counts)

# Check for unexpected results
print("\n=== UNEXPECTED RESULTS TO DOUBLE-CHECK ===")
print(f"1. TrustMark wins 100% of all {len(df)} transform-intensity combinations - unexpectedly dominant")
print(f"2. LSB and DCT never win as best_method (they only appear as fallback or fail)")
print(f"3. Hash is always the fallback_method but never the best_method")
print(f"4. LSB and DCT fail (False in lsb_ok/dct_ok) on some transforms like brightness 0.7, 0.85, 1.5, jpeg_compression 20-80, scaling 0.25-0.5, crop_center 0.1-0.3, crop_random 0.1-0.5, rotation 90, scaling 3.0")
print(f"5. DCT fails on rotation 1°, 90° and scaling 3.0, crop_random 0.3, 0.7")
print("→ TRUSTMARK DOMINANCE (100% win rate) IS UNEXPECTED AND SHOULD BE DOUBLE-CHECKED AGAINST RAW SCORES")