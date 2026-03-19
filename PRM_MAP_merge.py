import slicer
import numpy as np
from slicer.util import arrayFromVolume, updateVolumeFromArray

# -------------------------------------------------------
# Rename lung-masked&filtered Inspiration "Insp_masked" 
# and lung-masked, registered & filtered Expiration "Exp_masked"
# -------------------------------------------------------
INSP_NAME = "Insp_masked"
EXP_NAME  = "Exp_masked"

inspNode = slicer.util.getNode(INSP_NAME)
expNode  = slicer.util.getNode(EXP_NAME)

insp = arrayFromVolume(inspNode).astype(np.float32)
exp  = arrayFromVolume(expNode).astype(np.float32)

# -------------------------------------------------------
# 0) BASIC GEOMETRY / VOXEL VOLUME
# -------------------------------------------------------
spacing = inspNode.GetSpacing()  # (dx, dy, dz) in mm
voxelVol_mm3 = float(spacing[0] * spacing[1] * spacing[2])
voxelVol_mL  = voxelVol_mm3 / 1000.0

# -------------------------------------------------------
# 1) VALID MASKS FOR METRICS
# -------------------------------------------------------
valid_insp = (insp != 0)
valid_exp  = (exp  != 0)
base_valid = valid_insp & valid_exp

# PRM analysis intensity window (-1000 to -250 HU) on BOTH scans
prm_window = (
    (insp >= -1000) & (insp <= -250) &
    (exp  >= -1000) & (exp  <= -250)
)
analysis = base_valid & prm_window

# -------------------------------------------------------
# 2) PRM CLASSIFICATION
# -------------------------------------------------------
# Class labels:
# 0 = outside / ignored
# 1 = Emphysema
# 2 = fSAD
# 3 = Normal_or_PD

prm = np.zeros_like(insp, dtype=np.uint8)

insp_emph = (insp < -950)
insp_mid  = (insp >= -950) & (insp < -810)
insp_pd   = (insp >= -810)

exp_norm  = (exp >= -856)
exp_low   = (exp <  -856)

# Merge PD into Normal_or_PD directly
prm[analysis & insp_pd] = 3
prm[analysis & insp_mid & exp_norm] = 3
prm[analysis & insp_mid & exp_low ] = 2
prm[analysis & insp_emph & exp_low] = 1

# -------------------------------------------------------
# 2b) Majority filter
# -------------------------------------------------------
import scipy.ndimage as ndi

labels = prm.copy()
labels[~analysis] = 0

def majority_filter(lbl, size=3):
    out = np.zeros_like(lbl, dtype=np.uint8)
    best = None
    for k in [1, 2, 3]:
        cnt = ndi.uniform_filter((lbl == k).astype(np.float32), size=size, mode="constant", cval=0.0)
        if best is None:
            best = cnt
            out[:] = k
        else:
            replace = cnt > best
            out[replace] = k
            best[replace] = cnt[replace]
    out[lbl == 0] = 0
    return out

prm = majority_filter(labels, size=3).astype(np.uint8)

# -------------------------------------------------------
# 3) CREATE PRM MAP VOLUME
# -------------------------------------------------------
prmNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", "PRM_Map")
prmNode.CopyOrientation(inspNode)
prmNode.SetSpacing(inspNode.GetSpacing())
prmNode.SetOrigin(inspNode.GetOrigin())
updateVolumeFromArray(prmNode, prm)

# -------------------------------------------------------
# 4) PRM % + VOLUME (mL) METRICS (within analysis mask)
# -------------------------------------------------------
total = int(np.count_nonzero(analysis))
if total == 0:
    raise RuntimeError("Total PRM voxels is 0. Check masking / HU window / fill values.")

counts = {
    "Emphysema": int(np.sum(prm == 1)),
    "fSAD": int(np.sum(prm == 2)),
    "Normal_or_PD": int(np.sum(prm == 3)),
}

perc = {k: (v / total * 100.0) for k, v in counts.items()}
vol_ml = {k: (v * voxelVol_mL) for k, v in counts.items()}

print("\n=== PRM (within analysis mask) ===")
print("Spacing (mm):", spacing)
print("Voxel volume (mm^3):", voxelVol_mm3)
print("Total PRM voxels:", total)
print("Total PRM volume (mL):", total * voxelVol_mL)

print("\nPRM percentages:")
print("  fSAD %:", perc["fSAD"])
print("  Emphysema %:", perc["Emphysema"])
print("  Normal+PD %:", perc["Normal_or_PD"])

print("\nPRM class volumes (mL):")
print("  fSAD (mL):", vol_ml["fSAD"])
print("  Emphysema (mL):", vol_ml["Emphysema"])
print("  Normal+PD (mL):", vol_ml["Normal_or_PD"])

# -------------------------------------------------------
# 5) DENSITY-BASED + VOLUME-NORMALIZED COMPANION METRICS
# -------------------------------------------------------
insp_lung_vox = int(np.count_nonzero(valid_insp))
exp_lung_vox  = int(np.count_nonzero(valid_exp))

insp_lung_ml = insp_lung_vox * voxelVol_mL
exp_lung_ml  = exp_lung_vox  * voxelVol_mL

mld_insp = float(np.mean(insp[valid_insp])) if insp_lung_vox > 0 else float("nan")
mld_exp  = float(np.mean(exp[valid_exp]))  if exp_lung_vox  > 0 else float("nan")

delta_mld = mld_exp - mld_insp

laa950_insp = int(np.sum((insp < -950) & valid_insp))
airtrap_exp = int(np.sum((exp  < -856) & valid_exp))

laa950_insp_pct = laa950_insp / insp_lung_vox * 100.0 if insp_lung_vox > 0 else float("nan")
airtrap_exp_pct = airtrap_exp / exp_lung_vox  * 100.0 if exp_lung_vox  > 0 else float("nan")

print("\n=== Companion metrics (scan-wise) ===")
print("Inspiratory lung volume (mL):", insp_lung_ml)
print("Expiratory lung volume (mL):", exp_lung_ml)

print("MLD insp (HU):", mld_insp)
print("MLD exp  (HU):", mld_exp)
print("ΔMLD (exp - insp) (HU):", delta_mld)

print("LAA%-950 on inspiration (TLC) (%):", laa950_insp_pct)
print("Exp air-trapping index (% voxels < -856) (%):", airtrap_exp_pct)

# -------------------------------------------------------
# 6) BUILD SEGMENTATION OVERLAY (3 classes) + SET COLORS
# -------------------------------------------------------
segNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode", "PRM_Segmentation")
segNode.CreateDefaultDisplayNodes()
segNode.SetReferenceImageGeometryParameterFromVolumeNode(inspNode)

def hex_to_rgb01(hex_color: str):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b)

colors = {
    "Emphysema": "#ff0000",
    "fSAD_airtrapping": "#ffff00",
    "Normal_plus_PD": "#55aa00",
}

seg = segNode.GetSegmentation()

for val, name in [
    (1, "Emphysema"),
    (2, "fSAD_airtrapping"),
    (3, "Normal_plus_PD")
]:
    label = (prm == val).astype(np.uint8)

    if np.count_nonzero(label) == 0:
        print(f"Skipping {name} (no voxels).")
        continue

    before = seg.GetNumberOfSegments()

    lm = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode", f"tmp_{name}")
    lm.CopyOrientation(prmNode)
    updateVolumeFromArray(lm, label)

    slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(lm, segNode)

    after = seg.GetNumberOfSegments()
    slicer.mrmlScene.RemoveNode(lm)

    if after == before:
        print(f"WARNING: Import produced no segment for {name} (unexpected).")
        continue

    lastSegmentId = seg.GetNthSegmentID(after - 1)
    segment = seg.GetSegment(lastSegmentId)

    segment.SetName(name)
    segment.SetColor(*hex_to_rgb01(colors[name]))

print("\nCreated PRM_Segmentation (3 classes: Emphysema, fSAD, Normal+PD).")