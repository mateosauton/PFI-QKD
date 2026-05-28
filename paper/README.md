# Memoria PFI QKD BB84 Time-Bin

Esta carpeta contiene una memoria técnica en LaTeX para el Proyecto Final Integrador de Ingeniería en Telecomunicaciones UNSAM.

## Estructura

- `main.tex`: archivo principal.
- `references.bib`: bibliografía.
- `chapters/`: capítulos y apéndices.
- `assets/`: imágenes conceptuales generadas para la memoria.
- Las figuras de resultados se referencian desde `../experiments/results/`.
- La memoria expandida está organizada como documento técnico largo de PFI, con capítulos de teoría, estado del arte, diseño de campus, hardware, simulación, resultados, discusión, KMS y apéndices.

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

En este entorno también se puede compilar con Tectonic:

```bash
tectonic --keep-logs main.tex
```
