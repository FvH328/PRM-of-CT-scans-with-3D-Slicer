import slicer

# -------------------------------------------------------
# Rename INPUT_NAME to the name of your Volume to be resampled
# -------------------------------------------------------
INPUT_NAME = "6: Tor inspirio  1.0  B70f"
# -------------------------------------------------------

# -------------------------------------------------------
# set target space to lowest scan of time-series, here e.g. 
# it is set to 0.615234375 x 0.615234375mm with 1.0mm slice thickness 
# -------------------------------------------------------
TARGET_SPACING = "0.615234375,0.615234375,1.0"
# -------------------------------------------------------

inputNode = slicer.util.getNode(INPUT_NAME)
OUTPUT_NAME = inputNode.GetName() + "_0615mm_resampled"
try:
    existing = slicer.util.getNode(OUTPUT_NAME)
    slicer.mrmlScene.RemoveNode(existing)
    print("Removed existing node:", OUTPUT_NAME)
except slicer.util.MRMLNodeNotFoundException:
    pass

outputNode = slicer.mrmlScene.AddNewNodeByClass(
    "vtkMRMLScalarVolumeNode",
    OUTPUT_NAME
)
outputNode.CreateDefaultDisplayNodes()

params = {
    "InputVolume": inputNode.GetID(),
    "OutputVolume": outputNode.GetID(),
    "outputPixelSpacing": TARGET_SPACING,
    "interpolationType": "linear"
}

cliNode = slicer.cli.runSync(
    slicer.modules.resamplescalarvolume,
    None,
    params
)

print("CLI status:", cliNode.GetStatusString())
if cliNode.GetErrorText():
    print("CLI error text:\n", cliNode.GetErrorText())


img = outputNode.GetImageData()
if img is None:
    raise RuntimeError("Resampling failed — no image data in output.")

print("Resampling OK.")
print("Output name:", OUTPUT_NAME)
print("New spacing:", outputNode.GetSpacing())
print("New dimensions:", img.GetDimensions())

slicer.util.setSliceViewerLayers(background=outputNode)