# LaTeX Migration Plan — JKU thesis template v2.2

*Polish-pass step 6. Written to plan the transition from the nine
committed Markdown chapter drafts into the JKU LaTeX template. No
LaTeX files are produced by this document, no chapter drafts are
edited, no figures are generated, no compile is attempted. That
work belongs to a later polish step (Step 6b: the actual
migration). Sources: the JKU LaTeX template zip
`jku-templates-report-latex-v2.2.zip` (unpacked to the local
scratchpad for inspection), `docs/THESIS_ASSEMBLY_PLAN.md`,
`docs/THESIS_TABLES_FIGURES.md`, and the committed thesis drafts
under `docs/thesis_draft/`.*

---

## 1. Template structure found

The JKU LaTeX template ships as an MPL-2.0 licensed source
package by Michael Roland (INS, JKU) — see
`https://github.com/michaelroland/jku-templates-report-latex`.
The v2.2 zip contains:

- **Main entry points** (choose one per document type)
  - `main-thesis.tex` — thesis entry file (this is the one this
    plan uses).
  - `main-report.tex` — technical report entry file (not used).
  - `main-seminarreport.tex` — seminar report entry file (not
    used).

- **Style package**
  - `jkureport.sty` — the template's LaTeX style. Loaded as
    `\usepackage[bathesis,fancyfonts]{jkureport}` for a
    bachelor thesis.

- **Chapter / matter stubs**
  - `00-abstract.tex` — English + German abstract skeleton.
  - `01-introduction.tex` — Chapter 1 skeleton.
  - `02-example.tex` — worked example (LaTeX tricks: tables,
    figures, citations, cross-references).
  - `09-conclusion.tex` — Chapter 9 skeleton.
  - `91-appendix.tex` — appendix skeleton.
  - `acknowledgements.tex` — optional acknowledgements.
  - `acronyms.tex` — optional list of abbreviations (uses the
    `acronym` LaTeX package).

- **Bibliography**
  - `references.bib` — template's sample bib (four Roland-lab
    entries — will be replaced by the thesis' own
    `references.bib`).
  - `ACM-Reference-Format.{bbx,bst,cbx,dbx}` — biblatex style
    files for the ACM Reference Format. Bundled so the
    bibliography compiles without downloading extra packages.

- **Assets**
  - `fonts/` — bundled TTFs: Merriweather (serif), PublicSans
    (sans), Inconsolata (mono), InconsolataCondensed. Each font
    family carries its own `LICENSE.txt` (OFL / Ubuntu Font
    License — redistributable, but see Section 8's risk item).
  - `logos/` — JKU logo PDFs (English, German; colour, black,
    white; LIT variants). MPL-2.0 with the template.
  - `images/` — sample image `jku_learningcenter.jpg` used by
    `02-example.tex`.

- **Reference PDFs**
  - `EXAMPLE-THESIS.pdf`, `EXAMPLE-REPORT.pdf`,
    `EXAMPLE-SEMINARREPORT.pdf` — pre-built reference outputs
    of the three main entry files. Not part of the compile;
    useful for visual comparison during migration.

- **Misc**
  - `README.md`, `LICENSE` (MPL 2.0), `.gitignore` (LaTeX build
    artefacts).

### 1.1 Toolchain

Magic comments at the top of `main-thesis.tex`:

- `% !TeX program = xelatex` — the template prefers XeLaTeX
  (needed for the custom TTF fonts). `lualatex` also works.
  `pdflatex` compiles but loses the professional font
  experience.
- `% !BIB program = biber` — bibliography is compiled with
  Biber (biblatex, not the older bibtex).

Recommended thesis compile pipeline:

```bash
xelatex main-thesis
biber main-thesis
xelatex main-thesis
xelatex main-thesis
```

Or via `latexmk -xelatex -bibtex- main-thesis.tex` (Biber
auto-detected).

### 1.2 Document class and package options

- Document class: `\documentclass[a4paper,oneside,10pt,ngerman,english]{scrbook}`
  (KOMA-Script `scrbook`). The bachelor thesis will use the
  same options.
- Template package: `\usepackage[bathesis,fancyfonts]{jkureport}`
  (option `bathesis` instead of the template default
  `mathesis`).
- Additional packages loaded by the template: `csquotes`,
  `biblatex` (backend Biber, ACM style), `todonotes`, `import`,
  `amsfonts`, `subfigure`, and optionally `acronym`.

### 1.3 Front-/main-/back-matter skeleton in `main-thesis.tex`

Skeleton the template provides (comments trimmed for brevity):

- `\frontmatter` — roman page numbers.
  - `\title{...}`, `\author{...}`, `\supervisor{...}`,
    `\degree{...}{...}`, `\submissiondepartment{...}`,
    optional `\date{YYYY-MM-DD}`, `\keywords{...}`.
  - `\maketitle` — renders the JKU title page.
  - `\import{./}{00-abstract}` — English + German abstract.
  - `\import{./}{acknowledgements}` — optional; commented out
    in the shipped template.
  - `\cleardoubleoddpage \tableofcontents`
  - `\listoftables`, `\listoffigures`, `\import{./}{acronyms}` —
    all commented out in the shipped template; enabled per
    thesis need.
- `\mainmatter` — arabic page numbers.
  - `\import{./}{01-introduction}`, ..., `\import{./}{09-conclusion}`
    — one `\import` per chapter file.
- `\cleardoubleoddpage \printbibliography`
- `\appendix`
  - `\import{./}{91-appendix}` — one `\import` per appendix
    chapter file.

### 1.4 Citations, cross-references, tables, figures — template idioms

From `02-example.tex`:

- Bibliography citations: `\cite{key}` (already the syntax
  used in the committed chapter drafts — no rewrite needed).
  `\citeauthor{key}` for author-name mentions.
- Cross-references: `\autoref{sec:...}`, `\autoref{fig:...}`,
  `\autoref{tab:...}` (auto-prefixes with "Section", "Figure",
  "Table").
- Labels: `\label{sec:chapter:section}` inside `\section{...}`;
  `\label{fig:name}` inside `\begin{figure}...\end{figure}`;
  `\label{tab:name}` inside `\begin{table}...\end{table}`.
- Figures:
  ```latex
  \begin{figure}[t]
  \centering
  \includegraphics[width=\linewidth]{images/name}
  \caption{Caption above / below (figures below).}
  \label{fig:name}
  \end{figure}
  ```
- Tables:
  ```latex
  \begin{table}[b]
  \centering
  \caption{Caption above the table.}
  \label{tab:name}
  \begin{tabularx}{\linewidth}{l>{\raggedright\arraybackslash}X}
  \toprule
  \textbf{Header 1} & \textbf{Header 2} \\
  \midrule
  ...
  \bottomrule
  \end{tabularx}
  \end{table}
  ```
- Code blocks: not shown in the shipped example; the template
  loads `listings` via `nocompactverb` option support (see
  `jkureport.sty` options). Fallback is a plain `verbatim`
  environment.

---

## 2. Where the LaTeX thesis will live in this repository

**Directory (proposed)**: `thesis_latex/` at the repository
root. Rationale:

- Isolates the LaTeX build tree from the Markdown drafts under
  `docs/thesis_draft/`.
- Simple gitignore additions: `thesis_latex/*.aux`, `.pdf`,
  `.log`, etc., using the template's existing `.gitignore`
  contents.
- The Markdown drafts remain the primary editable source until
  migration is complete; the LaTeX tree becomes primary from
  Step 6b onward.

**Alternative locations considered (not chosen)**:

- `thesis/` at repo root — simpler name, but risks colliding
  with a future `thesis/` release directory for the compiled PDF.
- Inside `docs/thesis_latex/` — keeps everything thesis-related
  under `docs/`, but adds a redundant path segment (`docs/thesis_latex/main-thesis.tex`
  is longer than `thesis_latex/main-thesis.tex`).

**What the initial `thesis_latex/` directory will contain
(when Step 6b runs)**:

- All template files copied in as-is: `jkureport.sty`,
  `main-thesis.tex`, `00-abstract.tex`, `01-introduction.tex`,
  `02-example.tex`, `09-conclusion.tex`, `91-appendix.tex`,
  `acronyms.tex`, `acknowledgements.tex`, all four
  `ACM-Reference-Format.*` files, `fonts/`, `logos/`, `images/`,
  `README.md`, `LICENSE`, `.gitignore`.
- A fresh `references.bib` copied from the repository root (see
  Section 5).
- Nine chapter files converted from Markdown (see Section 3).
- Renamed / customised `main-thesis.tex` with the thesis'
  actual title, author, supervisor, degree, and department
  metadata (see Section 4).

**Which template file becomes the final thesis main file**:
`thesis_latex/main-thesis.tex` — the shipped `main-thesis.tex`
customised for the bachelor thesis. `main-report.tex` and
`main-seminarreport.tex` are not used and will be deleted from
the `thesis_latex/` directory after copy-in.

---

## 3. Chapter-file mapping

The nine committed Markdown chapters map one-to-one to nine
LaTeX chapter files. File names follow the JKU template's
`NN-name.tex` convention with hyphenated lowercase suffixes,
matching your specification exactly:

| Markdown source | LaTeX target |
|---|---|
| `docs/thesis_draft/01_introduction.md` | `thesis_latex/01-introduction.tex` |
| `docs/thesis_draft/02_background_related_work.md` | `thesis_latex/02-background-related-work.tex` |
| `docs/thesis_draft/03_data_and_methodology.md` | `thesis_latex/03-data-and-methodology.tex` |
| `docs/thesis_draft/04_detector_verification_and_setup.md` | `thesis_latex/04-detector-verification-and-setup.tex` |
| `docs/thesis_draft/05_main_results.md` | `thesis_latex/05-main-results.tex` |
| `docs/thesis_draft/06_mitigation_experiment.md` | `thesis_latex/06-mitigation-experiment.tex` |
| `docs/thesis_draft/07_subgroup_diagnostics.md` | `thesis_latex/07-subgroup-diagnostics.tex` |
| `docs/thesis_draft/08_discussion_limitations.md` | `thesis_latex/08-discussion-limitations.tex` |
| `docs/thesis_draft/09_conclusion_future_work.md` | `thesis_latex/09-conclusion-future-work.tex` |

**Appendix files** (Step 6b will create these — no Markdown
sources yet):

- `91-appendix-reproducibility.tex` — Appendix A: reproducibility
  index (from assembly plan Section 6).
- `92-appendix-mitigation-v2-parameters.tex` — Appendix B:
  mitigation v2 trainable-parameter breakdown.
- `93-appendix-vctk-slate.tex` — Appendix C: VCTK 20-speaker
  slate composition.
- `94-appendix-low-n-subgroups.tex` — Appendix D: low-n subgroup
  diagnostic table.
- `95-appendix-spoof-generation-counts.tex` — Appendix E:
  spoof generation counts (**T2 lives here** — see Section 6).

The `main-thesis.tex` `\import{./}{NN-name}` block will be
updated to include all nine main chapters plus these five
appendix chapters.

**Note on the template's shipped `02-example.tex`**: this file
should be deleted from `thesis_latex/` once migration is done.
Keep it during the migration itself as a live-reference example
of template idioms.

---

## 4. Front-matter plan

The `main-thesis.tex` front-matter block will be filled out as
follows.

### 4.1 Title page metadata

- `\title{Does Your Accent Make You Vulnerable? Dialect and
  Generator Effects in Audio Deepfake Detection}`
- `\titleshort{Dialect and Generator Effects in Audio Deepfake
  Detection}` — for page heads.
- `\author{...}` — TODO before Step 6b: exact name + any
  suffixes / immatriculation number.
- `\supervisor{...}` — TODO: supervisor's name with title.
- `\assistantsupervisor{...}` — TODO if an assistant supervisor
  is involved.
- `\degree{Bachelor of Science}{Artificial Intelligence}` —
  bachelor thesis at JKU, BSc AI.
- `\submissiondepartment{Institute of Computational Perception}`
- `\date{YYYY-MM-DD}` — TODO: submission date once fixed.
- `\keywords{audio deepfake detection, anti-spoofing, dialect,
  dialect / domain gap, generator-specific corpus interaction,
  DECTE, VCTK, XTTS v2, OpenVoice v2, AASIST, LFCC + LR,
  controlled adaptation, subgroup diagnostics, bootstrap
  confidence intervals}` — comma-separated keyword list for PDF
  metadata.
- Template option: switch `[mathesis,fancyfonts]` to
  `[bathesis,fancyfonts]` in the `\usepackage[...]{jkureport}`
  line, since this is a bachelor thesis.

### 4.2 Abstract

- File: `thesis_latex/00-abstract.tex`.
- Content: two `abstract*` blocks — English (`\begin{abstract*}
  ... \end{abstract*}`) then German (`\begin{otherlanguage}{ngerman}
  \begin{abstract*} ... \end{abstract*} \end{otherlanguage}`).
- Draft status: the assembly plan flags the English abstract as
  "not yet drafted" (~ 250 words target). The German abstract
  ("Kurzfassung") must also be drafted — a translation of the
  English abstract is the standard approach.
- Wording contract: same as the body chapters — use *dialect /
  domain gap*, *generator-specific corpus interaction*,
  *cross-detector replication*, *controlled adaptation*, and
  *diagnostic (not fairness audit)*.

### 4.3 Acknowledgements

- File: `thesis_latex/acknowledgements.tex`.
- Uses `acks*` environment (JKU template's own).
- Optional — the shipped template comments out the
  `\import{./}{acknowledgements}` line by default. Enable if
  the supervisor confirms the thesis should include
  acknowledgements (typical only when external funding must be
  acknowledged, or for personal thanks).
- Draft status: not yet drafted.

### 4.4 Table of contents

- Rendered by `\tableofcontents` in `main-thesis.tex`.
- Automatic; the template handles depth and formatting.
- No action needed beyond leaving the `\tableofcontents`
  command enabled in the front-matter.

### 4.5 List of figures

- Rendered by `\listoffigures` in `main-thesis.tex`.
- Shipped template comments it out by default.
- **Enable** for this thesis: five main-text figures (F1, F4,
  F5, F6 plus optional F2) plus any generated in the appendices
  make a list-of-figures worthwhile.
- No content authoring needed — figure captions written in the
  chapter files are picked up automatically.

### 4.6 List of tables

- Rendered by `\listoftables` in `main-thesis.tex`.
- Shipped template comments it out by default.
- **Enable** for this thesis: six main-text tables (T1, T3, T4,
  T5, T6, T7) plus T2 in the appendix, all warrant a list-of-
  tables.

### 4.7 Acronyms

- File: `thesis_latex/acronyms.tex`.
- Uses the `acronym` package (must uncomment `\usepackage{acronym}`
  in `main-thesis.tex` package block).
- Draft status: ~ 15–20 acronyms to list, per the assembly plan.
  Draft list (to be finalised in Step 6b):
  AASIST, ASV, ASVspoof, ADD, AUC, CI, CQCC, DECTE, EER, FAR,
  FRR, GAT, GMM, LFCC, LR, NECTE, ROC, RQ, TTS, VC, VCTK,
  WAV.

---

## 5. Bibliography plan

### 5.1 Source of truth

The repository-root `references.bib` (30 entries after
`ShadishCookCampbell2002_Validity` was added in polish Step 3)
is the source of truth for the thesis bibliography. All
citation keys used in the chapter drafts already match this
file — polish Step 3 verified this.

### 5.2 Copy vs. point-to

**Decision (proposed)**: **copy** the repo-root
`references.bib` into `thesis_latex/references.bib` during
Step 6b, and add a note at the top of both files that they
must stay in sync until final submission.

Rationale for **copy** rather than symlink or path-to:

- Windows-friendly: symlinks are awkward on Windows and require
  admin privileges.
- Template-native: `jkureport`'s `\addbibresource{references.bib}`
  looks for a local file — no cross-directory path needed.
- Robust to future repo rearrangements: the LaTeX tree is
  self-contained and can be zipped up for the supervisor
  without extra path plumbing.

**Sync discipline**: any citation-key change must be applied to
both files, or to `thesis_latex/references.bib` alone once the
LaTeX tree is the primary source (after Step 6b).

### 5.3 Bibliography style

The template ships and uses the ACM Reference Format
(`ACM-Reference-Format.bbx / .bst / .cbx / .dbx`) via
`biblatex` with:

```latex
\usepackage[backend=biber,citestyle=numeric,sortcites=true,maxcitenames=2,style=ACM-Reference-Format]{biblatex}
```

**Decision (proposed)**: keep the ACM Reference Format as
shipped. Rationale: it is the JKU-shipped default; ACM
citations are widely accepted in engineering / CS theses; and
the .bbx / .bst / .cbx / .dbx files are bundled so no external
dependency is added.

Alternative styles the template supports (via `biblatex`) include
`authoryear`, `numeric-comp`, `alphabetic`, and any other
`biblatex` style — a supervisor preference override is easy to
apply if requested.

### 5.4 Citation-key preservation

**No citation key will change during LaTeX migration.** All 30
keys in the current `references.bib` are already in the
`\cite{Author20YY_Slug}` form used in the chapter drafts. The
Markdown → LaTeX conversion (Section 7) leaves `\cite{...}`
untouched.

### 5.5 TODO items still open on the bibliography

Carried over from Step 2 (see `references.bib` inline `%
TODO:` comments):

- Verify volume / issue / page numbers / DOIs at final
  proofread.
- Confirm ambiguous entries with the supervisor
  (`Corrigan_DECTE`, `Allen2007_NECTE`, `Gasenzer2023_...`,
  `WangHansen2024_...`, `Aksenova2022_AccentASR` — some fields
  are TODO'd against uncertain publication details).
- Decide whether to rename `Liu2022_ASVspoofInTheWild` to
  `Muller2022_InTheWild` in a single coordinated commit
  (chapter markers + bib key together — see the entry's own
  TODO note).

---

## 6. Tables and figures migration plan

Refers to `docs/THESIS_TABLES_FIGURES.md` for the full
inventory and locked placements. Summarised here for the LaTeX
migration workflow.

### 6.1 Locked main-text tables (six)

| ID | LaTeX target chapter | Migration status |
|---|---|---|
| T1 — Dataset and corpus overview | `03-data-and-methodology.tex` | Needs authoring (new `tabularx` block) |
| T3 — Detector verification summary | `04-detector-verification-and-setup.tex` | Needs authoring (compact form) |
| T4 — 2 × 2 × 2 result matrix | `05-main-results.tex` | Convert existing Markdown table |
| T5 — Mitigation v1 vs v2 | `06-mitigation-experiment.tex` | Needs authoring (side-by-side form) |
| T6 — Mitigation v2 guardrail summary | `06-mitigation-experiment.tex` | Convert existing Markdown table |
| T7 — Subgroup diagnostics summary | `07-subgroup-diagnostics.tex` | Convert existing Markdown table; keep the *diagnostic, not fairness audit* label |

### 6.2 Locked appendix table (one)

| ID | LaTeX target | Migration status |
|---|---|---|
| T2 — Spoof generation coverage | `95-appendix-spoof-generation-counts.tex` | Needs authoring; count query over the two manifest files |

### 6.3 Locked main-text figures (four)

| ID | LaTeX target chapter | Generation status |
|---|---|---|
| F1 — Experimental design overview | `03-data-and-methodology.tex` | **Needs generation** — hand-drawn flow diagram (TikZ / mermaid / external) |
| F4 — Gap direction forest plot | `05-main-results.tex` | **Needs generation** — Python script reading the four gap CIs |
| F5 — Mitigation effect before / after | `06-mitigation-experiment.tex` | **Needs generation** — Python script reading baseline and mitigated prediction CSVs |
| F6 — Per-subgroup mitigation delta | `07-subgroup-diagnostics.tex` | **Needs generation** — Python script reading `results/subgroup_diagnostics/decte_subgroup_metrics.csv`. **Diagnostic-only label required on the figure surface** (see risk item Section 8) |

### 6.4 Optional / skipped figures

- F2 — Detector verification flow: optional / appendix; no
  generation required unless the final template layout has
  room.
- F3 — Per-cell EER bar chart: **locked as skipped**; do not
  generate.
- T8 — Limitations-to-future-work matrix: optional; author
  only if space permits.

### 6.5 Figure-generation directory conventions (proposed for Step 6b)

- Generating scripts live in `scripts/figures/`, one script per
  final figure (e.g. `scripts/figures/gen_f4_gap_forest.py`).
- Rendered images live in `docs/figures/`, gitignored *except*
  for the final PDFs / PNGs that ship with the thesis.
- LaTeX-side, images referenced via
  `\includegraphics[width=\linewidth]{../docs/figures/f4_gap_forest}`
  (or the images are copied into `thesis_latex/images/`; the
  path decision is deferred to Step 6b).

### 6.6 Table format conventions

- All main-text tables: `booktabs` rules (`\toprule` /
  `\midrule` / `\bottomrule`), `tabularx` for full-width layouts
  with a wrapping text column, right-aligned numeric columns.
- Every table's caption above the tabular environment (as in
  the template's `02-example.tex`).
- Every table carries `\label{tab:name}` for `\autoref{...}`
  cross-references.

### 6.7 Figure format conventions

- All figures wrapped in `\begin{figure}[t] ... \end{figure}`
  (or `[b]` where explicitly needed).
- Caption **below** the artwork (as in the template's
  `02-example.tex`).
- `\label{fig:name}` for cross-references.
- Figures kept at `width=\linewidth` unless a specific figure
  needs a fixed width.

---

## 7. Markdown → LaTeX conversion rules

Rules the Step-6b migration will apply mechanically to each
chapter file. Ordered from most common to least common.

### 7.1 Headings

| Markdown | LaTeX |
|---|---|
| `# Chapter N — Title` | `\chapter{Title} \label{sec:chapter-name}` |
| `## N.M Section Title` | `\section{Section Title} \label{sec:chapter-name:section-name}` |
| `### N.M.K Subsection Title` | `\subsection{Subsection Title} \label{sec:chapter-name:section-name:subsection-name}` |

Chapter labels use a stable slug (e.g. `sec:intro`,
`sec:background`, `sec:data-methodology`) — the chapter number
is not part of the label so LaTeX can renumber freely.

### 7.2 Bold / italic / inline code

| Markdown | LaTeX |
|---|---|
| `**bold**` | `\textbf{bold}` |
| `*italic*` | `\emph{italic}` |
| `` `inline code` `` | `\texttt{inline code}` or `\verb|inline code|` when the code contains LaTeX special chars |

### 7.3 Bulleted and numbered lists

| Markdown | LaTeX |
|---|---|
| `- item` (bulleted) | `\begin{itemize} \item ... \end{itemize}` |
| `1. item` (numbered) | `\begin{enumerate} \item ... \end{enumerate}` |
| `> quote` (blockquote) | `\begin{quote} ... \end{quote}` |

### 7.4 Tables

Markdown pipe tables convert to `tabularx` + `booktabs`.
Example:

Markdown:
```
| Column A | Column B |
|---|---:|
| left    | right |
```

LaTeX:
```latex
\begin{table}[t]
\centering
\caption{Caption.}
\label{tab:name}
\begin{tabularx}{\linewidth}{X r}
\toprule
\textbf{Column A} & \textbf{Column B} \\
\midrule
left & right \\
\bottomrule
\end{tabularx}
\end{table}
```

Right-alignment of numeric columns via `r` (or `>{\raggedleft\arraybackslash}X`
for wrappable right-aligned columns).

### 7.5 Code blocks

Markdown fenced code blocks (```` ``` ````) → `verbatim`
environment, or `listings` (`lstlisting`) if language-specific
syntax highlighting is desired. Default choice: `verbatim` for
consistency with the shipped template's default packages.

### 7.6 Citations

Markdown drafts already use the LaTeX-native `\cite{Key}`
syntax (converted in polish Step 3). **No change needed** —
`\cite{...}` passes through the migration verbatim.

### 7.7 Percentages, en-dashes, em-dashes, minus signs

| Markdown source | LaTeX target | Notes |
|---|---|---|
| `40.70 %` | `40.70\,\%` | Thin space + escaped percent |
| `–` (U+2013 en-dash) | `--` | LaTeX ligature |
| `—` (U+2014 em-dash) | `---` | LaTeX ligature |
| `−` (U+2212 minus) | `$-$` or `\ensuremath{-}` | Proper math minus |
| `≤`, `≥` | `$\leq$`, `$\geq$` | Math mode |
| `×` | `$\times$` | Math mode |

Under XeLaTeX with UTF-8 input, several of these UTF-8 glyphs
render correctly without conversion; the safe path is still to
convert them for the pdfLaTeX-compatible fallback.

### 7.8 Special characters requiring escape

| Character | LaTeX escape |
|---|---|
| `%` | `\%` |
| `_` | `\_` (or `\textunderscore` in text mode) |
| `&` | `\&` |
| `$` | `\$` |
| `#` | `\#` |
| `{`, `}` | `\{`, `\}` |
| `~` | `\textasciitilde{}` |
| `^` | `\textasciicircum{}` |
| `\` | `\textbackslash{}` |

Backslash in Markdown paths (e.g. `C:\Users\AYO\...`) is a
special case — see Section 7.9.

### 7.9 Paths and backslashes

Drafts contain a small number of Windows-style absolute paths
inside `` `...` `` code spans (e.g. the AuralGuard checkpoint
location in Chapter 3). Two rules:

- **Anonymise absolute paths.** Convert
  `C:\Users\AYO\Desktop\JKU\Extra Semester\THESIS AND
  PRACTICAL\dialect-deepfake-bias\auralguard-aasistpp\...`
  to `<AURALGUARD_ROOT>/...` before wrapping in LaTeX. The
  assembly plan's Section 9.2 flags this as a submission-
  readiness requirement.
- **Escape backslashes.** Any remaining backslash in
  `\path{...}` or `\verb|...|` needs proper LaTeX escaping.
  The `\path{...}` command from the `url` / `hyperref` packages
  is the cleanest way to render literal paths without escaping
  every backslash individually.

Recommendation: after anonymisation, use forward-slash paths
inside `\path{<AURALGUARD_ROOT>/results/.../best.pt}` — clean
and readable in both Markdown and LaTeX.

### 7.10 Figure and table cross-references

| Markdown | LaTeX |
|---|---|
| "Figure 3 shows..." | `\autoref{fig:name} shows...` |
| "Table 5 lists..." | `\autoref{tab:name} lists...` |
| "Chapter 5, Section 5.7" | `\autoref{sec:main-results:table} on \autoref{page:main-results}` — or keep textual form `Chapter~\ref{sec:main-results}, Section~\ref{sec:main-results:table}` |
| "Entry 7 of the findings log" | Rewrite as prose reference to the appendix reproducibility index, since the findings log is not a compiled part of the thesis |

Chapter drafts currently have 250+ fully-qualified
`Chapter N, Section N.M` cross-references (per the Step-4
audit). Each becomes a `\autoref{sec:...}` or
`\ref{sec:...}` reference in the LaTeX target. This is
straightforward mechanical work — no ref is ambiguous.

### 7.11 Findings-log references

Chapter drafts cite `Entry N` from
`docs/THESIS_FINDINGS_LOG.md` (Entries 1, 3, 5, 6, 7, 8, 9,
10, 11 across the body). The findings log itself will **not**
be part of the compiled thesis PDF. Two options for these
references:

- (a) Rewrite `"see Entry 7 of the findings log"` to `"see
  Appendix A"` where Appendix A is the reproducibility index
  and lists each Entry's commit hash and script.
- (b) Keep the `"Entry N"` phrasing and add a footnote at the
  first `Entry N` reference pointing the reader to the
  reproducibility appendix.

Recommendation: **(a)**, since Entry-N naming is a working-doc
artefact that has little meaning to a first-time reader.

---

## 8. Risk checklist

Every item below must pass before the thesis is considered
submission-ready.

### 8.1 Font redistribution

- **Fonts bundled with the template**: Merriweather, PublicSans,
  Inconsolata, InconsolataCondensed. Each carries its own
  `LICENSE.txt` under `fonts/` — typically SIL Open Font License
  (OFL) or Ubuntu Font License, both of which permit
  redistribution as part of the derived work.
- **Action for Step 6b**: read each font's `LICENSE.txt` before
  copying `fonts/` into the repository. Confirm the licence
  permits redistribution in the thesis' Git repository. If any
  font's licence is restrictive, either replace it or ship only
  the font's LICENSE (not the .ttf) and rely on the reader's
  system to provide it.
- **Do not delete the fonts' `LICENSE.txt` files.** They must
  ship alongside the font binaries.

### 8.2 JKU logo redistribution

- Bundled with the template under `logos/`. Licensed under
  MPL 2.0 with the template package.
- **Action for Step 6b**: confirm the JKU brand guidelines
  permit thesis-scope usage of the logos (the template is
  intended for JKU theses, so this should be fine, but a
  sanity check is cheap).

### 8.3 Absolute Windows paths in the final thesis

- Chapter 3 §3.4.1 and §3.9.6 and Chapter 4 §4.2 reference the
  local AuralGuard project at absolute
  `C:\Users\AYO\Desktop\JKU\Extra Semester\...` paths inside
  code spans.
- **Action for Step 6b**: anonymise every absolute path to a
  placeholder like `<AURALGUARD_ROOT>/results/.../best.pt`.
- **Grep target before compile**: `\bC:\\` or `\/C:\/` or
  `AYO` should return zero hits inside `thesis_latex/`.

### 8.4 No generated audio or datasets ship with the thesis

- The thesis distributes source code, LaTeX, figure PDFs, and
  the compiled `main-thesis.pdf` — nothing under `data/`,
  `results/`, `checkpoints/`, `data/generated_spoofs*/`.
- **Action for Step 6b**: ensure the `thesis_latex/.gitignore`
  covers any accidental result-CSV / audio-file inclusion, and
  ensure no `\includegraphics{...}` path escapes into
  `results/` or `data/`.

### 8.5 Results CSVs

- Some results CSVs (Entry 11's `decte_subgroup_metrics.csv`,
  etc.) will be *used* as data sources for figures — the CSV
  files are not committed to the repo, but the derived PNGs
  are.
- **Action for Step 6b**: figure-generation scripts read from
  the local (gitignored) `results/` directory; the produced
  PNGs get committed under `docs/figures/`. The CSVs
  themselves never make it into the thesis.
- Exception: if a small (~10-row) result table is used as an
  appendix table (e.g., T2 spoof generation counts), the
  numbers get typed into a LaTeX table by hand — the CSV
  itself is not included.

### 8.6 Compile verification before submission

- After Step 6b, the LaTeX tree must compile cleanly on both a
  Linux and a Windows environment with TeX Live / MiKTeX +
  Biber.
- **Action before submission**: run the four-step compile
  pipeline (Section 1.1) and confirm the produced PDF matches
  the intended layout. Manually inspect: title page (correct
  bachelor thesis template variant + correct author /
  supervisor / degree / department), table of contents, list
  of figures, list of tables, list of acronyms, chapter
  numbering, cross-references, bibliography, appendices.
- **Compile-warning threshold**: zero unresolved `??` cross-
  reference markers, zero missing citation warnings, zero
  overfull `\hbox`es greater than a few pt, zero undefined
  reference warnings.

### 8.7 Wording contract preservation

The five contract phrases from the polish passes must survive
migration intact:

- *dialect / domain gap* — never *pure dialect bias*, never
  *pure dialect effect*.
- *generator-specific corpus interaction* — never *OpenVoice
  is a worse generator*.
- *cross-detector replication* — never *the AASIST result
  generalises*.
- *controlled adaptation* — never *the mitigation works*
  without qualification.
- *diagnostic, not a formal fairness audit* — mandatory
  labelling on Chapter 7 tables and F6.

**Action after Step 6b compile**: grep the LaTeX tree for the
forbidden phrases and confirm they are absent.

### 8.8 Numbers, tables, and citations preservation

- No result number is allowed to change during migration.
- No table row / column is allowed to change.
- No citation key is allowed to rename during migration.
- **Action for Step 6b**: run the same structural fingerprint
  check used in polish passes (comparing the number-token
  count / heading count / citation-key set between the
  Markdown source and the LaTeX output) on each converted
  chapter. Any drift is a bug in the conversion.

---

## 9. Open decisions

Items where a supervisor or author input is needed before
Step 6b can proceed.

### 9.1 Title-page metadata

- **Exact author name** (with any prefix, suffix, immatriculation
  number).
- **Supervisor name and title** (`\prefix{}` + name +
  `\suffix{}`).
- **Assistant supervisor** (if any).
- **Degree program string** — proposed: `\degree{Bachelor of
  Science}{Artificial Intelligence}`. Confirm this matches the
  official JKU wording.
- **Institute string** — proposed: `\submissiondepartment{Institute
  of Computational Perception}`. Confirm the JKU-registered
  name.
- **Submission date** — TBD.

### 9.2 Acknowledgements yes / no

- The shipped template comments out the acknowledgements block.
- Decision: enable if the thesis should thank supervisors,
  reviewers, funding sources, or the DECTE corpus custodians.

### 9.3 List of figures / list of tables / acronyms — enable?

- Proposed: enable all three. All three add reader value at
  low authoring cost.
- Requires: uncomment `\listoffigures`, `\listoftables`,
  `\import{./}{acronyms}` in `main-thesis.tex`, and finalise
  the acronyms list in `acronyms.tex`.

### 9.4 Bibliography style: keep ACM Reference Format?

- Proposed: keep the shipped ACM format.
- Alternative: switch to `authoryear` (biblatex option) or
  another style — a single edit to the `\usepackage[...]{biblatex}`
  options line in `main-thesis.tex`.

### 9.5 Legacy-mode compatibility

- The template supports `\usepackage[bathesis,fancyfonts,legacymode={<mode>}]{jkureport}`
  for older formal requirements.
- Proposed: **do not enable any legacy mode.** The current v2.2
  template is up-to-date with 2024W JKU cover-sheet
  requirements.

### 9.6 pdfLaTeX vs XeLaTeX vs LuaLaTeX

- Proposed: **XeLaTeX** (the template's default, needed for
  fancy fonts).
- Alternative: LuaLaTeX (equivalent font support) or pdfLaTeX
  (loses custom fonts). Any of the three compiles, per the
  template's magic-comment notes.

### 9.7 Findings-log references migration

- Proposed rewrite: `"see Entry 7 of the findings log"` →
  `"see Appendix A"`, where Appendix A is the reproducibility
  index.
- Alternative: keep the "Entry N" phrasing and cross-reference
  via a footnote at first use.

---

## 10. What this plan does NOT do

- It does not create `thesis_latex/` or any file inside it.
- It does not convert any chapter draft.
- It does not generate any figure or figure-generation script.
- It does not compile a PDF.
- It does not copy fonts, logos, or the template files anywhere.
- It does not modify the repository-root `references.bib`.
- It does not touch code, data, results, checkpoints,
  manifests, or generated audio.
- It does not run any experiment.

The scope of this document is planning and specification only.
The actual migration is **Step 6b**, a separate polish-pass
step that will act on this plan under the same review-before-
commit protocol used throughout.

---

*End of LaTeX migration plan.*
