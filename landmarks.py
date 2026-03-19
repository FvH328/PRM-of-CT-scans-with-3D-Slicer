import json
import numpy as np

# -------------------------------------------------------
# CHANGE ONLY THESE TWO LINES WITH THE .mrk.json files
# Use the fixed/insp landmarks and the transformed+hardened expiration landmarks
# -------------------------------------------------------
FIXED_FILE = "NAME_OF_YOUR_INSP_LANDMARKS"
MOVING_TRANSFORMED_FILE = "NAME_OF_EXP_TRANSFORMED_LANDMARKS.mrk.json"
# -------------------------------------------------------

def load_markups_positions(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)

    if "markups" not in data or len(data["markups"]) == 0:
        raise ValueError(f"No markups found in file: {json_file}")

    cps = data["markups"][0]["controlPoints"]

    points = {}
    for cp in cps:
        label = cp.get("label", "")
        pos = cp.get("position", None)
        status = cp.get("positionStatus", "")
        if label and pos is not None and status == "defined":
            points[label] = np.array(pos, dtype=float)

    return points

fixed_pts = load_markups_positions(FIXED_FILE)
moving_pts = load_markups_positions(MOVING_TRANSFORMED_FILE)

common_labels = sorted(set(fixed_pts.keys()) & set(moving_pts.keys()))
missing_in_fixed = sorted(set(moving_pts.keys()) - set(fixed_pts.keys()))
missing_in_moving = sorted(set(fixed_pts.keys()) - set(moving_pts.keys()))

if len(common_labels) == 0:
    raise RuntimeError("No matching landmark labels found between the two files.")

distances = []
print("\nPer-landmark TRE (mm):")
for lbl in common_labels:
    d = np.linalg.norm(fixed_pts[lbl] - moving_pts[lbl])
    distances.append(d)
    print(f"  {lbl}: {d:.3f}")

distances = np.array(distances, dtype=float)

print("\n=== TRE summary ===")
print("Matched landmarks:", len(common_labels))
print("Mean TRE (mm):", float(np.mean(distances)))
print("Median TRE (mm):", float(np.median(distances)))
print("Std TRE (mm):", float(np.std(distances, ddof=1)) if len(distances) > 1 else 0.0)
print("Min TRE (mm):", float(np.min(distances)))
print("Max TRE (mm):", float(np.max(distances)))
print("95th percentile TRE (mm):", float(np.percentile(distances, 95)))

if missing_in_fixed:
    print("\nLabels missing in fixed file:", missing_in_fixed)
if missing_in_moving:
    print("Labels missing in moving/transformed file:", missing_in_moving)