# domain_viz subskill

Handle visualizations that fall outside the standard chart types and need a domain-specific python package — EEG/MEG topomaps (`mne`), fMRI brain renders (`nilearn`, `surfplot`), molecular structures (`py3Dmol`, `nglview`), genomic tracks (`pyGenomeTracks`, `pyranges`), network graphs (`networkx` + `pyvis`/`igraph`), phylogenetic trees (`ete3`, `dendropy`), spatial / GIS (`geopandas`, `cartopy`), microscopy (`napari`), …

This subskill is the *learning* hook for the skill: when plot_gen's seaborn/matplotlib grammar isn't enough, you escalate here, learn the API the user (or you) propose, attempt the plot, and persist what you learned to `info/project_specific_knowledge.md` so future sessions don't have to relearn from scratch.

Read this together with `../../SKILL.md` for the top-level rules.

---

## When to run

Trigger phrases: anything where the user names a domain-specific viz the standard chart types don't cover, e.g.:

- "Plot the EEG topography averaged over the alpha band."
- "Show the BOLD signal projected onto the cortical surface."
- "Render this PDB structure with the binding pocket highlighted."
- "Draw a chord diagram of cell-cell interactions."
- "Plot the gene track with these called peaks overlaid."
- "Visualize the protein-protein interaction graph."

If the standard chart types (scatter / violin / heatmap / line / hist / bar / facet / small multiples) genuinely cover the request, use **plot_gen** instead — don't reach for a heavy domain package just because the data is from an unusual source.

## Python only

This skill is python-end-to-end. If the user names a package that's not python (Matlab toolbox, R-only library, a Mathematica notebook, a C++ binary):

- be honest: "I can only work with python packages in this skill — that's an R library, so I can't drive it from here."
- offer alternatives: most domains have at least one python equivalent; suggest one if you know it.
- if there genuinely isn't a python option, say so plainly. Don't try to wrap a non-python tool — fragile and out-of-scope.

## How to learn the package

1. **Ask the user for a starting point.** "Which package would you like me to use? A link to its docs / a quickstart example would help me get the API right." A concrete docs URL or a working code snippet is worth a lot more than a name alone.
2. **If the user doesn't have one**, search online for the canonical package and a quickstart. Be conservative — pick the most-cited / most-maintained option; flag your choice to the user before installing.
3. **Read enough to do this one task, not the whole API.** You're not writing a tutorial; you're trying to produce one specific figure. Skim the docs, find the function that takes the user's data shape, build a minimal working call, iterate.
4. **Install discipline** — same as the rest of the skill: ask before installing (`references/env-management.md`), prefer the project's venv if there is one, and pin the version in `info/project_specific_knowledge.md` so the user can recreate the env later.
5. **Attempt the plot, share with the user, iterate.** Domain packages often have surprising data-shape requirements (a `mne.Epochs` object isn't just a numpy array; a `nilearn` surface needs an `fsaverage` template) — share your first attempt and the data path, and be ready to fix shape issues.

## Intermediate data: use the native format

The standard parser writes `<dataset>__parsed.csv` because tabular data lives happily in CSV. **Domain pipelines often shouldn't.** EEG raw / epoched / evoked, fMRI volumes, protein structures, single-cell expression matrices, microscopy stacks — each has an established binary format that preserves metadata, dtypes, channel layouts, affines, etc. Forcing a round-trip through CSV either loses that or produces a giant unwieldy frame.

Keep the project's `<dataset>__<stage>.<ext>` naming pattern but pick the extension the next step in the pipeline actually loads:

| Domain | Typical raw / intermediate format | Loader |
|---|---|---|
| EEG / MEG (`mne`) | `.fif` (Raw / Epochs / Evoked / ICA) | `mne.io.read_raw_fif`, `mne.read_epochs`, `mne.read_evokeds` |
| Volumetric imaging / fMRI (`nilearn`, `nibabel`) | `.nii.gz` (NIfTI) | `nibabel.load` / `nilearn.image.load_img` |
| Surface meshes (`nilearn`, `surfplot`) | `.gii` (GIFTI), `.mgh` | `nibabel.load` |
| Protein / molecular structures | `.pdb`, `.mmcif` | `Bio.PDB`, `mdtraj.load`, `py3Dmol.view` |
| Trajectories (MD) | `.xtc` / `.dcd` + `.pdb` topology | `mdtraj.load` / `MDAnalysis.Universe` |
| Single-cell (`scanpy`) | `.h5ad` (AnnData) | `scanpy.read_h5ad` |
| Genomic intervals / tracks | `.bed`, `.bigwig`, `.bam` | `pyranges`, `pyBigWig`, `pysam` |
| Networks | `.gml`, `.graphml`, `.pickle` | `networkx.read_gml` / `read_graphml` |
| Microscopy / volumetric arrays | `.zarr`, `.tif`, `.h5` | `zarr`, `tifffile`, `h5py` |
| Phylogenetic trees | `.nwk` (Newick) | `ete3.Tree`, `dendropy.Tree.get` |

Examples following the naming convention:

- `subj01__parsed.fif`, `subj01__alpha_band.fif`, `subj01__epochs_correct.fif`
- `bold_run1__motion_corrected.nii.gz`, `bold_run1__masked.nii.gz`
- `complex_AB__aligned.pdb`, `complex_AB__pocket.pdb`
- `cells__filtered.h5ad`, `cells__umap.h5ad`
- `volume__downsampled.zarr`, `volume__segmented.zarr`

The `parsed_index.json` `parsed_path` field is just a string — non-CSV paths slot in fine. Add an explicit `format` key to the index entries when it's not obvious from the extension (e.g. `"format": "mne.Epochs"` vs `"format": "mne.Raw"` — both `.fif`).

If the project mixes tabular and non-tabular intermediates (e.g. event tables in CSV alongside `.fif` recordings), keep them in the same `intermediate_data/` tree — the suffix and extension already disambiguate.

Document the format choice in `info/project_specific_knowledge.md` for the relevant section ("we save Epochs as `.fif` because `mne.read_epochs` reloads the channel montage and event metadata; CSV would force re-attaching them every time"). A future agent shouldn't have to re-derive *why* a particular format was picked.

## Persisting what you learn

The point of this subskill is that the next session shouldn't relearn the same package from scratch.

### Light touch — `info/project_specific_knowledge.md`

After the figure works, write a concise note to `visualizations/info/project_specific_knowledge.md`. Format:

```markdown
# Project-specific knowledge

> **For agents:** read this before producing any plot in a domain that's listed below. The standard plot_gen grammar doesn't cover these — load the relevant section, follow the patterns, and add new entries when you learn something new.

## EEG topomaps via `mne`

- **Package:** `mne` 1.6.x. Install: `pip install mne`.
- **Reference:** <https://mne.tools/stable/auto_tutorials/visualization/index.html>
- **Intermediate format:** `.fif` (not CSV). We save each subject's preprocessed Epochs as `subj<NN>__parsed.fif` and the band-passed evoked as `subj<NN>__alpha_band.fif`. Reloading with `mne.read_epochs` restores the channel montage and event metadata in one call — going through CSV would force us to re-attach those every time.
- **Data shape we use:** `mne.Epochs` objects with a BioSemi-64 montage; channel order in the source CSVs (`data/`) is converted on intake.
- **Minimal call:**
  ```python
  evoked = mne.read_evokeds(path)[0]
  fig = evoked.plot_topomap(times=[0], ch_type="eeg", show=False)
  ```
- **Gotcha:** the channel order in our CSVs follows the BioSemi 64 layout, *not* mne's default — use `info.set_montage("biosemi64")` or topomaps come out flipped.
- **Where it's used in this project:** `PROJECT_RECIPES["alpha-band-topomap"]` in `plot_gen.py`. Reads from `intermediate_data/<subj>__alpha_band.fif` (listed in `parsed_index.json` with `"format": "mne.Evoked"`).
```

Keep each section short and concrete — the goal is enough to reconstruct the next plot, not a textbook.

### When the knowledge gets long — `info/knowledge/<topic>.md`

If a single topic outgrows ~40 lines of `project_specific_knowledge.md` (e.g. "we ended up writing five `mne` recipes with different montages and we keep stumbling on the same caveats"):

1. Create `visualizations/info/knowledge/<topic>.md` and move the long-form content there.
2. Replace the `project_specific_knowledge.md` section with a short pointer:

   ```markdown
   ## EEG topomaps via `mne`

   See [`knowledge/mne-topomaps.md`](knowledge/mne-topomaps.md) — covers montages, evoked vs. epochs, custom colormaps, and our project-specific quirks.
   ```

3. Add an entry to `info/context.md` noting the new file.

### When the topic gets *really* established — suggest a real skill

Once a domain has accumulated multiple `info/knowledge/<topic>.md` files and is being reused across the project, surface a next-step prompt:

> "We've built up a fair amount of `mne` knowledge in this project — `info/knowledge/{mne-topomaps,mne-evoked-grand-avg,mne-epochs-from-csv}.md`. If you reuse this stack a lot, it might be worth condensing this into its own skill so other projects can install it directly. Want me to outline that?"

Don't push it; just offer.

## Cross-link with plot_gen

Domain plots are still plots — they should:

- live alongside other plots in `plots/<slug>/` with `figure.png` (and `.pdf` if vector-renderable), `data.csv`, and `spec.json`,
- be reproducible via `bash generate_plot.sh --recipe <slug>` if it's a project-canonical figure (register it in `PROJECT_RECIPES` with a `data` path and any extra package-specific kwargs),
- follow `info/style_guide.md` palette / typography to the extent the domain package allows it.

If the package can't honor the project palette (some surface-rendering libraries pin their own colormaps), say so in `project_specific_knowledge.md` and in the recipe's caveats.

## Closing the loop

Two `info/` files get touched:

- `info/project_specific_knowledge.md` — what was learned (or a pointer to `info/knowledge/<topic>.md`).
- `info/context.md` — one-liner: subskill ran, package learned, slug, where the figure lives.
