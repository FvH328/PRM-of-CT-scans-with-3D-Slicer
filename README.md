# PRM-of-CT-scans-with-3D-Slicer
Collection of Python code snippets, which allow Parametric response mapping analysis of lung CT scans with the Python console within Slicer3D. The code was originally based on the paper of Ram et al. "Quantitative CT Correlates with Local Inflammation in Lung of Patients with Subtypes of Chronic Lung Allograft Dysfunction" (2022).

PRM provides a regional and quantitative assessment of lung function that goes beyond global pulmonary function tests (PFTs), which lack spatial resolution. In diseases such as bronchiolitis obliterans syndrome (BOS), where small airway obstruction is the dominant pathology, PRM is particularly valuable because it allows the detection and localization of functional small airways disease (fSAD) that may not yet be reflected in conventional metrics.

In this project, PRM was used to longitudinally assess disease progression and to relate imaging-derived markers (e.g. fSAD, emphysema) to clinical measurements such as FEV1 and FEV1/FVC.  It was heavily based on the works of Ram et al. *"Quantitative CT Correlates with Local Inflammation in Lung of Patients with Subtypes of Chronic Lung Allograft Dysfunction"* (2022). They found for CLAD patients respective to their specific subtype:
- **BOS**: marked elevation in fSAD, lower PD compared to RAS, minimal emphysema in early-moderate stages, progressive reduction of normal lung
- **RAS**: increased PD, less dominant fSAD, higher inspiratory density (fibrosis-like)

As a software, 3D Slicer was used for all the analysis with integrated Python code via the command console. Its important to check via the metadata if settings of scanners of different timepoints in the CT scan differ. **Differences that make a resampling necessary or comparing difficult**:
- different resolution -> resample "better" scans to the scan of the lowest resolution
- different kernel -> currently no fix implemented for this
- different CT Scanner ->  currently no fix implemented for this

### Steps:
Utilize the github repo. If python code is mentioned, change the respective variable names and then copy and paste the code into the python console of 3D Slicer:

1. Masking & Registration:
	- The lungs of the inspiratory (TLC) and expiratory (RV) CT scans were segmented via the 3D Slicer Lung CT Segmentor module of the Chest Image Plattform to only contain the lung and these segmentations were used to only contain 
	- The 3D Slicer Elastix module was then used to register the already masked expiratory scan to the inspiratory scan. Recommended settings that were used (edit the parameter file):
		- NumberOfResolutions 4 (default 3)
		- MaximumNumberOfIterations 1000 (default 500)
2. Preprocessing:
	-  Resampling (if necessary, see above) the better resolution of scans to the lowest resolution of the series via the resampling code of Resampling.py. Set the INPUT_NAME and TARGET_SPACING to receive a new volume resampled to the target specs
	-  Median Image filter 1,1,1 (built-in Slicer3D feature) was applied after registration to reduce noise before using the PRM
3. Run PRM:
	- In the PRM_MAP_merge.py file rename lung-masked&filtered Inspiration "Insp_masked" and lung-masked, registered & filtered Expiration "Exp_masked" according to your naming will sort into classes according to the following Hounsfield Unit classes (HU) following Ram et al. but "normal" and "parenchymal disease (PD)" were merged due to sensitivity issues of PD (see legacy code note at the bottom):
		- **Emphysema** insp < −950 ∧ exp < −856 
		- **fSAD** insp ≥ −950 ∧ < −810 ∧ exp < −856
		- **Normal / Parenchymal tissue** (remaining voxels) 

4. Outputs of the PRM_MAP_merge:
	- PRM segmentation and map (with a majority filter which can be turned off via the code if needed):
		- Emphysema: RED
		- fSAD: YELLOW
		- Normal & PD: GREEN
	- Multiple metrics as an output in the console:
		- Spacing, voxel volume, PRM voxel count (needs to stay linear during timeseries, otherwise check resampling section/metadata for differences in scan)
		- PRM % per class
		- Volume mL per class
		- Density-based metrics and Volume-normalized metrics:
			- MLD insp (HU)
			- MLD exp (HU)
			- ΔMLD (HU)
			- LAA%-950 on inspiration (TLC)
			- Exp air-trapping index (% voxels < -856) (%)
5. Validation/TRE:
	- Registration accuracy was assessed using a landmark-based Target Registration Error (TRE). The "landmark registration" tool of 3D Slicer was used to create a node containing the anatomical features within Insp and respective features in Exp, afterwards the transformation from the registration was used to transform a copy of these nodes and harden it. Then with the landmarks.py file correct naming of the FIXED_FILE and MOVING_TRANSFORMED_FILE multiple values of the TRE can be calculated:
		- Per-landmark TRE (mm)
		- Matched landmarks
		- Mean TRE (mm)
		- Median TRE (mm)
		- Std TRE (mm)
		- Min TRE (mm)
		- Max TRE (mm)
		- 95th percentile TRE (mm)

NOTE: the PRM_MAP_final.py will work similar to the PRM_MAP_merge.py but will also entail the Parenchymal Disease (in pink, separate from "normal") as originally described by Ram et al.  
