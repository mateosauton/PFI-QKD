# Trabajo PFI QKD BB84 Time-Bin

Esta carpeta contiene un trabajo técnico en LaTeX para el Proyecto Final Integrador de Ingeniería en Telecomunicaciones UNSAM, desarrollado por Mateo Sauton e Ignacio Polesello.

## Estructura

- `main.tex`: archivo principal.
- `proyecto3.tex`: entrega abreviada de Proyecto 3.
- `references.bib`: bibliografía.
- `chapters/`: capítulos y apéndices.
- `assets/`: imágenes conceptuales generadas para el trabajo.
- Las figuras de resultados se referencian desde `../experiments/results/`.
- El trabajo expandido está organizado como documento técnico largo de PFI, con capítulos de teoría, estado del arte, diseño de campus, hardware, simulación, resultados, discusión y apéndices.

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

La entrega abreviada se compila por separado:

```bash
tectonic --keep-logs proyecto3.tex
```
