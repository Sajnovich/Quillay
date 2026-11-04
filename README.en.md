<div align="center">

[Español](README.md) · **English**

<img src="src/quillay/assets/icono.png" width="96" alt="Quillay icon: a white leaf on a green background" />

# Quillay

**Get your images ready to publish: lightweight, the right size, and free of data you don't want to share.**

Quillay automates what you do before uploading a photo to your website or social media: it fits it, shrinks it, strips its GPS location and writes the code you need to paste. Save those steps as **recipes** and repeat them with one click or one command.

[![CI](https://github.com/sajnovich/quillay/actions/workflows/ci.yml/badge.svg)](https://github.com/sajnovich/quillay/actions/workflows/ci.yml)
![Python 3.11+](https://img.shields.io/badge/python-3.11+-2f7d5b)
![Windows · macOS · Linux](https://img.shields.io/badge/Windows%20%C2%B7%20macOS%20%C2%B7%20Linux-2f7d5b)
[![MIT License](https://img.shields.io/badge/license-MIT-1f5c42)](LICENSE)
[![Stars](https://img.shields.io/github/stars/sajnovich/quillay?style=social)](https://github.com/sajnovich/quillay/stargazers)

**[Download](https://github.com/sajnovich/quillay/releases/latest)** · [Contributing](CONTRIBUTING.md) · [Report a bug](https://github.com/sajnovich/quillay/issues/new/choose)

<img src="docs/capturas/inicio-oscuro.webp" width="860" alt="Quillay home screen with tools grouped into Web, Privacy, Editing and PDF" />

</div>

> [!NOTE]
> The interface is currently in **Spanish**. An English translation is on the roadmap, and help is very welcome!

> [!TIP]
> **Find Quillay useful?** Give it a ⭐. It takes one second and helps others discover it.

## What makes Quillay different

- **Reusable recipes.** A recipe is a YAML file with several steps (fit → watermark → WebP without GPS) that you run from the window, the terminal or a script, and share with your team.
- **First-class command line.** Every tool is also a command (`quillay favicons logo.png`), generated from the same code as the window, so they never disagree.
- **Built for the web.** You get files *and* code: the favicon `<head>`, the `<picture>` with `srcset`, CSS variables for your brand colors and loading placeholders.
- **Privacy before publishing.** It tells you which photos reveal where they were taken, blurs faces and finds duplicates without deleting anything.
- **Local, no accounts.** Everything runs on your computer; nothing is uploaded.

## Tools

| Category | Tools |
|---|---|
| **Automate** | Recipes (5 built-in + your own) |
| **Web** | Favicons & app icons · Responsive images (`<picture>`/`srcset`) · Social media sizes · Brand colors (CSS variables) · Loading placeholders (LQIP) |
| **Privacy** | GPS & metadata check and cleanup · Face blurring · Duplicate finder |
| **Editing** | Convert · Compress · Resize · Crop · Fit to size · Watermark · Batch rename |
| **PDF** | Images → PDF · PDF → images |

Supported formats: JPG, PNG, WebP, AVIF, HEIC, TIFF, BMP, GIF and ICO.

## Install

**Ready-to-run app:** grab the file for Windows, macOS or Linux from [Releases](https://github.com/sajnovich/quillay/releases/latest).

**With Python 3.11+:**

```bash
git clone https://github.com/sajnovich/quillay.git
cd quillay
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[gui]"
quillay-gui
```

## Command line

```bash
quillay herramientas                                  # list all tools
quillay convertir photos/ --formato webp --calidad 80
quillay favicons logo.png --nombre-sitio "My site"
quillay metadatos photo.jpg                           # does it have GPS?
quillay receta correr web-optimizado photos/ -o ready/
```

Commands and options are in Spanish for now; `quillay <tool> --help` lists everything.

## Contributing

Contributions of every size are welcome: bug reports, ideas, recipes, docs, **translations** and code. Start with [CONTRIBUTING.md](CONTRIBUTING.md) (in Spanish; feel free to open issues and PRs in English) and look for issues labeled [`buena primera tarea`](https://github.com/sajnovich/quillay/labels/buena%20primera%20tarea) (good first issue).

## License

[MIT](LICENSE) © 2026 Eduardo Sajnovich. Made in Chile 🇨🇱 for everyone.
