import csv

hash_rows = []
with open('output/results/hash_robustness_results.csv') as f:
    reader = csv.DictReader(f)
    for r in reader:
        hash_rows.append(r)

main_algos = ['phash', 'dhash', 'ahash', 'pdq']
transforms = sorted(set(r['transform_name'] for r in hash_rows))

print("=== OVERALL PER ALGO ===")
for a in main_algos:
    rows = [r for r in hash_rows if r['hash_algorithm'] == a]
    hamming = [int(r['hamming_distance']) for r in rows]
    total_bits = 256 if a == 'pdq' else 64
    mean_h = sum(hamming) / len(hamming)
    mean_pct = mean_h / total_bits * 100
    print(f"{a}: n={len(rows)}, mean_hamming={mean_h:.2f}, bits={total_bits}, mean_pct_changed={mean_pct:.1f}%")

print("\n=== PDQ per transform ===")
for t in transforms:
    rows = [r for r in hash_rows if r['hash_algorithm'] == 'pdq' and r['transform_name'] == t]
    hamming = [int(r['hamming_distance']) for r in rows]
    mean_h = sum(hamming) / len(hamming)
    mean_pct = mean_h / 256 * 100
    print(f"{t}: mean_hamming={mean_h:.2f}, mean_pct={mean_pct:.1f}%")

print("\n=== aHash per transform ===")
for t in transforms:
    rows = [r for r in hash_rows if r['hash_algorithm'] == 'ahash' and r['transform_name'] == t]
    hamming = [int(r['hamming_distance']) for r in rows]
    mean_h = sum(hamming) / len(hamming)
    mean_pct = mean_h / 64 * 100
    print(f"{t}: mean_hamming={mean_h:.2f}, mean_pct={mean_pct:.1f}%")

print("\n=== dHash per transform ===")
for t in transforms:
    rows = [r for r in hash_rows if r['hash_algorithm'] == 'dhash' and r['transform_name'] == t]
    hamming = [int(r['hamming_distance']) for r in rows]
    mean_h = sum(hamming) / len(hamming)
    mean_pct = mean_h / 64 * 100
    print(f"{t}: mean_hamming={mean_h:.2f}, mean_pct={mean_pct:.1f}%")

print("\n=== LETTERBOX SPECIFIC ===")
for a in main_algos:
    rows = [r for r in hash_rows if r['hash_algorithm'] == a and r['transform_name'] == 'letterbox']
    hamming = [int(r['hamming_distance']) for r in rows]
    total_bits = 256 if a == 'pdq' else 64
    mean_h = sum(hamming) / len(hamming)
    print(f"{a}: mean_hamming={mean_h:.2f}, mean_pct={mean_h/total_bits*100:.1f}%")

# Trustmark analysis
print("\n\n=== TRUSTMARK ===")
tm_rows = []
with open('output/results/trustmark_robustness_results.csv') as f:
    reader = csv.DictReader(f)
    for r in reader:
        tm_rows.append(r)

print("Per transform:")
for t in sorted(set(r['transform_name'] for r in tm_rows)):
    rows = [r for r in tm_rows if r['transform_name'] == t]
    ba = [float(r['bit_accuracy']) for r in rows]
    decode = [r['decode_present'] == 'True' for r in rows]
    print(f"{t}: mean_bit_acc={sum(ba)/len(ba):.4f}, decode_rate={sum(decode)/len(decode)*100:.0f}%")

# Overall
ba_all = [float(r['bit_accuracy']) for r in tm_rows]
decode_all = [r['decode_present'] == 'True' for r in tm_rows]
print(f"Overall: mean_bit_acc={sum(ba_all)/len(ba_all):.4f}, decode_rate={sum(decode_all)/len(decode_all)*100:.0f}%")

# Geometric vs content
print("Geometric (rotation, scaling, crop_center, crop_random, letterbox):")
geo = [r for r in tm_rows if r['transform_name'] in ('rotation','scaling','crop_center','crop_random','letterbox')]
ba_geo = [float(r['bit_accuracy']) for r in geo]
decode_geo = [r['decode_present'] == 'True' for r in geo]
print(f"  mean_bit_acc={sum(ba_geo)/len(ba_geo):.4f}, decode_rate={sum(decode_geo)/len(decode_geo)*100:.0f}%, n={len(geo)}")

# Non-geometric
nongeo = [r for r in tm_rows if r['transform_name'] not in ('rotation','scaling','crop_center','crop_random','letterbox')]
ba_ng = [float(r['bit_accuracy']) for r in nongeo]
decode_ng = [r['decode_present'] == 'True' for r in nongeo]
print(f"Non-geometric: mean_bit_acc={sum(ba_ng)/len(ba_ng):.4f}, decode_rate={sum(decode_ng)/len(decode_ng)*100:.0f}%, n={len(nongeo)}")

# LSB analysis
print("\n\n=== LSB ===")
lsb_rows = []
with open('output/results/lsb_robustness_results.csv') as f:
    reader = csv.DictReader(f)
    for r in reader:
        lsb_rows.append(r)

print("Per transform:")
for t in sorted(set(r['transform_name'] for r in lsb_rows)):
    rows = [r for r in lsb_rows if r['transform_name'] == t]
    ba = [float(r['bit_accuracy']) for r in rows]
    decode = [r['decode_present'] == 'True' for r in rows]
    print(f"{t}: mean_bit_acc={sum(ba)/len(ba):.4f}, decode_rate={sum(decode)/len(decode)*100:.0f}%")

ba_lsb = [float(r['bit_accuracy']) for r in lsb_rows]
decode_lsb = [r['decode_present'] == 'True' for r in lsb_rows]
print(f"Overall LSB: mean_bit_acc={sum(ba_lsb)/len(ba_lsb):.4f}, decode_rate={sum(decode_lsb)/len(decode_lsb)*100:.0f}%")

# DCT analysis
print("\n\n=== DCT ===")
dct_rows = []
with open('output/results/dct_robustness_results.csv') as f:
    reader = csv.DictReader(f)
    for r in reader:
        dct_rows.append(r)

print("Per transform:")
for t in sorted(set(r['transform_name'] for r in dct_rows)):
    rows = [r for r in dct_rows if r['transform_name'] == t]
    ba = [float(r['bit_accuracy']) for r in rows]
    decode = [r['decode_present'] == 'True' for r in rows]
    print(f"{t}: mean_bit_acc={sum(ba)/len(ba):.4f}, decode_rate={sum(decode)/len(decode)*100:.0f}%")

ba_dct = [float(r['bit_accuracy']) for r in dct_rows]
decode_dct = [r['decode_present'] == 'True' for r in dct_rows]
print(f"Overall DCT: mean_bit_acc={sum(ba_dct)/len(ba_dct):.4f}, decode_rate={sum(decode_dct)/len(decode_dct)*100:.0f}%")

# Ensemble analysis
print("\n\n=== ENSEMBLE ===")
ens_rows = []
with open('output/results/ensemble_decision_matrix.csv') as f:
    reader = csv.DictReader(f)
    for r in reader:
        ens_rows.append(r)

print("Columns:", list(ens_rows[0].keys()))
for method in ['hash','trustmark','lsb','dct']:
    key = f'{method}_ok'
    vals = [r[key] == 'True' for r in ens_rows]
    print(f"{method}: pass_rate={sum(vals)/len(vals)*100:.1f}% ({sum(vals)}/{len(vals)})")

best_methods = [r['best_method'] for r in ens_rows]
from collections import Counter
print(f"Best method distribution: {dict(Counter(best_methods))}")
fallback_methods = [r['fallback_method'] for r in ens_rows if r['fallback_method']]
print(f"Fallback method distribution: {dict(Counter(fallback_methods))}")

# Pass count per image
print("\nPer-image pass count distribution:")
pass_counts = []
for r in ens_rows:
    pc = sum(1 for m in ['hash','trustmark','lsb','dct'] if r[f'{m}_ok'] == 'True')
    pass_counts.append(pc)
print(dict(Counter(pass_counts)))
