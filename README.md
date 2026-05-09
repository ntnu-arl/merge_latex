# merge_latex

Merge several latex files (including the .bbl) into a single file for source submission (e.g. through the ManuscriptCentral portal).

## Usage

Copy the `merge_latex.py` script into your latex root folder, set the input/output filenames and run the python script.

The features are:
1. Every `\input` will be expanded to the content of the corresponding file.
2. The figures are converted to jpg and copied to the output folder, removing the subfolder structure.
3. The `\bibliography{whatever}` is expanded to the content of the pre-generated `.bbl`. Make sure to have it in the root folder.
4. Commented lines are ignored. (not handle `\iffalse ... \fi`)

## Acro package

The script expands the acro package macros manually, in case the package is not working with online compilers.
The `\DeclareAcronym` should all be in a single separate file named `...glossary.tex` (you should put your `\usepackage{acro}` therein, since this file is not expanded into the final `.tex`).
Once the corresponding `\input` is encountered, the file is parsed and a glossary dict is created.
The subsequent `\ac*` commands will be expanded in the same way the acro package does.
The following features are handled so far:
* `\ac`, `\acs`, `\acl`, `\acf`, `\acsp` (`\acps`), `\aclp` (`\acpl`), `\acfp` (`\acpf`)
* `\acresetall`
* `\DeclareAcronym` with the following keywords
  * `short`, `long` (required)
  * `first-style = short`, `first-style = long`
  * `short-plural-form`, `long-plural-form`

Moreover, if you declare shortcuts for acronyms (e.g., `\newcommand{\fov}{\ac{FOV}\xspace}`), they will also be expanded in the output latex file.

## TODO handle SI package

Replacement of `\usepackage{siunitx}`:
```latex
\newcommand{\num}[1]{#1}
\newcommand{\unit}[1]{\ensuremath{\mathrm{#1}}}
\newcommand{\si}[1]{\ensuremath{\mathrm{#1}}}
\newcommand{\SI}[2]{\ensuremath{#1\,\mathrm{#2}}}
```
