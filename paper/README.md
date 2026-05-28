# Memoria PFI QKD BB84 Time-Bin

Esta carpeta contiene una memoria técnica en LaTeX para el Proyecto Final Integrador de Ingeniería en Telecomunicaciones UNSAM.

## Estructura

- `main.tex`: archivo principal.
- `references.bib`: bibliografía.
- `chapters/`: capítulos y apéndices.
- Las figuras se referencian desde `../experiments/results/`.

## Compilación

Desde esta carpeta:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Si `latexmk` está instalado:

```bash
latexmk -pdf main.tex
```

En este entorno local no se detectaron `pdflatex` ni `latexmk`; la fuente queda lista para compilar en una instalación LaTeX completa.
