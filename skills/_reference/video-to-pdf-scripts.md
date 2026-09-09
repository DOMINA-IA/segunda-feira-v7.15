# Video-to-PDF — Script Python Completo (Referência)

> Extraído de `$HOME/.claude/skills/video-to-pdf.md` (progressive disclosure, Sprint 2 A6). Script completo da classe `PDFGenerator` + função `generate_pdf_from_transcriptions`, usado na Fase 4 do pipeline (Geração do PDF).

### Script Python Completo para Geração do PDF

```python
#!/usr/bin/env python3
"""
Video-to-PDF Generator
Gera PDFs educacionais profissionais a partir de transcrições.
"""

import fitz  # PyMuPDF
import os
import re
import textwrap
from datetime import datetime
from pathlib import Path


class Config:
    """Configuração de cores, layout e fontes."""

    # Cores
    DARK_BG = fitz.pdfcolor["gray10"]    # #1a1a1a
    HEADER_BG = (0.102, 0.102, 0.180)    # #1a1a2e
    GREEN = (0, 0.784, 0.325)             # #00C853
    WHITE = (1, 1, 1)
    LIGHT_GRAY = (0.95, 0.95, 0.95)
    DARK_TEXT = (0.15, 0.15, 0.15)
    RED_ALERT = (0.898, 0.224, 0.208)     # #E53935
    GREEN_TIP = (0, 0.784, 0.325)

    # Layout A4
    PAGE_WIDTH = 595.28
    PAGE_HEIGHT = 841.89
    MARGIN_LEFT = 56
    MARGIN_RIGHT = 56
    MARGIN_TOP = 72
    MARGIN_BOTTOM = 72
    CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT

    # Caminhos de fontes com suporte a acentuação
    FONT_PATHS = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/SFPro.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]

    @classmethod
    def find_font(cls):
        """Encontra uma fonte TrueType com suporte a acentuação."""
        for path in cls.FONT_PATHS:
            if os.path.exists(path):
                return path
        # Fallback: baixar NotoSans
        fallback = os.path.expanduser("~/Downloads/video_temp/NotoSans-Regular.ttf")
        if not os.path.exists(fallback):
            import urllib.request
            url = (
                "https://github.com/google/fonts/raw/main/"
                "ofl/notosans/NotoSans%5Bwdth%2Cwght%5D.ttf"
            )
            urllib.request.urlretrieve(url, fallback)
        return fallback


class PDFGenerator:
    """Gerador de PDFs educacionais com layout profissional."""

    def __init__(self, brand: str, output_dir: str):
        self.brand = brand
        self.output_dir = output_dir
        self.font_path = Config.find_font()
        self.font = fitz.Font(fontfile=self.font_path)
        self.doc = None
        self.current_y = Config.MARGIN_TOP

    def _new_page(self):
        page = self.doc.new_page(
            width=Config.PAGE_WIDTH, height=Config.PAGE_HEIGHT
        )
        self.current_y = Config.MARGIN_TOP
        return page

    def _check_space(self, page, needed: float):
        """Se não há espaço suficiente, cria nova página."""
        if self.current_y + needed > Config.PAGE_HEIGHT - Config.MARGIN_BOTTOM:
            self._add_footer(page)
            page = self._new_page()
        return page

    def _draw_rect(self, page, x, y, w, h, color):
        rect = fitz.Rect(x, y, x + w, y + h)
        shape = page.new_shape()
        shape.draw_rect(rect)
        shape.finish(fill=color, color=color)
        shape.commit()

    def _write_text(self, page, x, y, text, size=11, color=Config.DARK_TEXT):
        tw = fitz.TextWriter(page.rect)
        tw.append(fitz.Point(x, y), text, fontsize=size, font=self.font)
        tw.write_text(page, color=color)
        return y

    def _wrap_and_write(self, page, x, y, text, size=11,
                        color=Config.DARK_TEXT, max_width=None):
        """Escreve texto com word wrap. Retorna página atual."""
        if max_width is None:
            max_width = Config.CONTENT_WIDTH
        chars_per_line = int(max_width / (size * 0.52))
        lines = textwrap.wrap(text, width=chars_per_line)
        line_height = size * 1.5
        for line in lines:
            page = self._check_space(page, line_height)
            self._write_text(
                page, x, self.current_y, line, size=size, color=color
            )
            self.current_y += line_height
        return page

    def _add_footer(self, page):
        """Rodapé: marca | título | data | página."""
        y = Config.PAGE_HEIGHT - 40
        self._draw_rect(page, 0, y - 5, Config.PAGE_WIDTH, 1, Config.GREEN)
        page_num = len(self.doc)
        footer = (
            f"{self.brand}  |  {self.title}  |  "
            f"{self.date_str}  |  Página {page_num}"
        )
        self._write_text(
            page, Config.MARGIN_LEFT, y + 10, footer,
            size=8, color=(0.5, 0.5, 0.5),
        )

    def _create_cover(self, title: str, subtitle: str, stats: dict):
        """Página de capa com header escuro e barra de estatísticas."""
        page = self._new_page()

        # Fundo escuro header (metade superior)
        self._draw_rect(page, 0, 0, Config.PAGE_WIDTH, 420, Config.HEADER_BG)

        # Nome do instituto em verde
        self._write_text(
            page, Config.MARGIN_LEFT, 120,
            self.brand.upper(), size=14, color=Config.GREEN,
        )

        # Título principal
        self._write_text(
            page, Config.MARGIN_LEFT, 200,
            title, size=28, color=Config.WHITE,
        )

        # Subtítulo
        if subtitle:
            self._write_text(
                page, Config.MARGIN_LEFT, 260,
                subtitle, size=14, color=(0.7, 0.7, 0.8),
            )

        # Barra de estatísticas
        stats_y = 350
        self._draw_rect(
            page, Config.MARGIN_LEFT, stats_y,
            Config.CONTENT_WIDTH, 40, Config.GREEN,
        )
        stats_text = "  |  ".join(
            [f"{k}: {v}" for k, v in stats.items()]
        )
        self._write_text(
            page, Config.MARGIN_LEFT + 15, stats_y + 25,
            stats_text, size=10, color=Config.WHITE,
        )

        # Data
        self._write_text(
            page, Config.MARGIN_LEFT, 500,
            f"Material gerado em {self.date_str}",
            size=11, color=Config.DARK_TEXT,
        )

        # Aviso
        self._write_text(
            page, Config.MARGIN_LEFT, 530,
            "Transcrição automática — conteúdo fiel ao vídeo original.",
            size=9, color=(0.5, 0.5, 0.5),
        )

    def _create_toc(self, chapters: list):
        """Página de sumário com capítulos numerados."""
        page = self._new_page()

        # Header
        self._draw_rect(page, 0, 0, Config.PAGE_WIDTH, 80, Config.HEADER_BG)
        self._write_text(
            page, Config.MARGIN_LEFT, 50,
            "SUMÁRIO", size=22, color=Config.WHITE,
        )

        self.current_y = 120
        for i, chapter in enumerate(chapters, 1):
            page = self._check_space(page, 50)

            # Número verde
            num_text = f"{i:02d}"
            self._write_text(
                page, Config.MARGIN_LEFT, self.current_y,
                num_text, size=18, color=Config.GREEN,
            )

            # Título do capítulo
            self._write_text(
                page, Config.MARGIN_LEFT + 40, self.current_y,
                chapter["title"], size=13, color=Config.DARK_TEXT,
            )

            # Descrição breve
            if chapter.get("description"):
                self.current_y += 18
                self._write_text(
                    page, Config.MARGIN_LEFT + 40, self.current_y,
                    chapter["description"], size=9, color=(0.5, 0.5, 0.5),
                )

            self.current_y += 35

    def _create_chapter(self, number: int, title: str, content: str):
        """Página de conteúdo com header numerado e corpo estruturado."""
        page = self._new_page()

        # Header do capítulo
        self._draw_rect(page, 0, 0, Config.PAGE_WIDTH, 90, Config.HEADER_BG)
        self._write_text(
            page, Config.MARGIN_LEFT, 40,
            f"{number:02d}", size=32, color=Config.GREEN,
        )
        self._write_text(
            page, Config.MARGIN_LEFT + 55, 45,
            title, size=18, color=Config.WHITE,
        )

        self.current_y = 120

        # Processar conteúdo em blocos
        blocks = self._parse_content(content)
        for block in blocks:
            if block["type"] == "paragraph":
                page = self._wrap_and_write(
                    page, Config.MARGIN_LEFT, self.current_y,
                    block["text"], size=11,
                )
                self.current_y += 8

            elif block["type"] == "heading":
                page = self._check_space(page, 30)
                self._write_text(
                    page, Config.MARGIN_LEFT, self.current_y,
                    block["text"], size=13, color=Config.HEADER_BG,
                )
                self.current_y += 22

            elif block["type"] == "bullet":
                page = self._check_space(page, 20)
                bullet_text = f"  •  {block['text']}"
                page = self._wrap_and_write(
                    page, Config.MARGIN_LEFT + 10, self.current_y,
                    bullet_text, size=10,
                )
                self.current_y += 4

            elif block["type"] == "tip":
                page = self._add_callout_box(page, block["text"], "tip")

            elif block["type"] == "alert":
                page = self._add_callout_box(page, block["text"], "alert")

        self._add_footer(page)

    def _add_callout_box(self, page, text, box_type="tip"):
        """Caixa de destaque: verde (dica) ou vermelha (alerta)."""
        page = self._check_space(page, 60)
        color = Config.GREEN_TIP if box_type == "tip" else Config.RED_ALERT
        label = "DICA" if box_type == "tip" else "ATENÇÃO"

        # Borda esquerda colorida
        self._draw_rect(
            page, Config.MARGIN_LEFT, self.current_y, 4, 50, color,
        )
        # Fundo claro
        self._draw_rect(
            page, Config.MARGIN_LEFT + 4, self.current_y,
            Config.CONTENT_WIDTH - 4, 50, Config.LIGHT_GRAY,
        )
        # Label
        self._write_text(
            page, Config.MARGIN_LEFT + 15, self.current_y + 15,
            label, size=9, color=color,
        )
        # Texto
        self._write_text(
            page, Config.MARGIN_LEFT + 15, self.current_y + 32,
            text[:100], size=10, color=Config.DARK_TEXT,
        )
        self.current_y += 65
        return page

    def _create_checklist(self, items: list):
        """Página final com checklist de ação."""
        page = self._new_page()

        self._draw_rect(page, 0, 0, Config.PAGE_WIDTH, 80, Config.HEADER_BG)
        self._write_text(
            page, Config.MARGIN_LEFT, 50,
            "CHECKLIST DE AÇÃO", size=22, color=Config.WHITE,
        )

        self.current_y = 120
        for item in items:
            page = self._check_space(page, 25)
            checkbox = f"[ ]  {item}"
            self._write_text(
                page, Config.MARGIN_LEFT + 10, self.current_y,
                checkbox, size=11, color=Config.DARK_TEXT,
            )
            self.current_y += 25

        self._add_footer(page)

    def _parse_content(self, text: str) -> list:
        """Converte texto bruto em blocos estruturados."""
        blocks = []
        paragraphs = text.split("\n\n")
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(para) < 80 and (para.isupper() or para.endswith(":")):
                blocks.append({"type": "heading", "text": para})
            elif para.startswith(("- ", "* ")):
                for line in para.split("\n"):
                    line = line.lstrip("- *").strip()
                    if line:
                        blocks.append({"type": "bullet", "text": line})
            elif para.lower().startswith(("dica:", "importante:", "lembre")):
                blocks.append({"type": "tip", "text": para})
            elif para.lower().startswith(("atenção:", "cuidado:", "alerta:")):
                blocks.append({"type": "alert", "text": para})
            else:
                blocks.append({"type": "paragraph", "text": para})
        return blocks

    def _organize_chapters(self, transcriptions: list) -> list:
        """Organiza transcrições em capítulos (cada arquivo = 1 capítulo)."""
        chapters = []
        for i, t in enumerate(transcriptions, 1):
            title = t["title"]
            clean_title = re.sub(r'^\d+\s*[-_.]\s*', '', title)
            chapters.append({
                "number": i,
                "title": clean_title,
                "description": f"Transcrição do vídeo {i}",
                "content": t["content"],
            })
        return chapters

    def generate(self, transcriptions: list, title: str, subtitle: str = ""):
        """
        Gera o PDF completo.

        Args:
            transcriptions: Lista de dicts {"title": str, "content": str}
            title: Título principal do documento
            subtitle: Subtítulo (opcional)
        """
        self.title = title
        self.date_str = datetime.now().strftime("%d/%m/%Y")
        self.doc = fitz.open()

        chapters = self._organize_chapters(transcriptions)

        stats = {
            "Capítulos": str(len(chapters)),
            "Palavras": str(sum(len(c["content"].split()) for c in chapters)),
            "Gerado em": self.date_str,
        }

        # Gerar páginas
        self._create_cover(title, subtitle, stats)
        self._create_toc(chapters)

        for ch in chapters:
            self._create_chapter(ch["number"], ch["title"], ch["content"])

        # Checklist baseado nos títulos dos capítulos
        checklist_items = [f"Revisar: {ch['title']}" for ch in chapters]
        checklist_items.append("Aplicar conceitos na prática")
        checklist_items.append("Compartilhar com a equipe")
        self._create_checklist(checklist_items)

        # Salvar
        output_path = os.path.join(
            self.output_dir, f"{self._slugify(title)}.pdf"
        )
        self.doc.save(output_path)
        self.doc.close()
        print(f"PDF gerado: {output_path}")
        return output_path

    def _slugify(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_]+', '-', text)
        return text[:80]


def generate_pdf_from_transcriptions(
    transcription_dir: str,
    brand: str,
    title: str,
    subtitle: str = "",
    output_dir: str = None,
) -> str:
    """
    Gera PDF a partir de um diretório com arquivos .txt de transcrição.

    Args:
        transcription_dir: Pasta com arquivos .txt
        brand: Nome da marca/instituto
        title: Título do PDF
        subtitle: Subtítulo
        output_dir: Pasta de saída (default: mesmo diretório)

    Returns:
        Caminho do PDF gerado
    """
    if output_dir is None:
        output_dir = transcription_dir

    txt_files = sorted(Path(transcription_dir).glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError(
            f"Nenhum .txt encontrado em {transcription_dir}"
        )

    transcriptions = []
    for f in txt_files:
        content = f.read_text(encoding="utf-8")
        title_from_file = f.stem
        transcriptions.append({
            "title": title_from_file,
            "content": content,
        })

    gen = PDFGenerator(brand=brand, output_dir=output_dir)
    return gen.generate(transcriptions, title, subtitle)
```
