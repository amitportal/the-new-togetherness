"""
This script converts a Markdown file to a PDF or LaTeX document using Pandoc, with support for Mermaid diagrams and Unicode math.
"""

import argparse
import re
import subprocess
import shutil
from pathlib import Path

UNICODE_REPLACEMENTS = {
    "ψ": r"$\psi$", "ℏ": r"$\hbar$", "φ": r"$\phi$", "θ": r"$\theta$",
    "Δ": r"$\Delta$", "∑": r"$\sum$", "∫": r"$\int$", "∞": r"$\infty$",
    "μ": r"$\mu$", "λ": r"$\lambda$", "Ω": r"$\Omega$",
    "₹": r"Rs. ",
    # "₹": r"\\textrupee",   # requires rupee package
    # "→": r"$\rightarrow$",

}

def snake_case(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9]+', '_', name).strip('_').lower()

def run_mmdc(mmd_file, out_file):
    mmdc_path = shutil.which("mmdc")
    if mmdc_path:
        cmd = [mmdc_path, "-i", mmd_file, "-o", out_file]
    else:
        cmd = [r"C:\Users\kamit\AppData\Roaming\npm\mmdc.cmd", "-i", mmd_file, "-o", out_file]
    subprocess.run(cmd, check=True)

def render_mermaid_blocks(md_text: str, output_format: str = "svg") -> str:
    pattern = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
    diagrams = pattern.findall(md_text)
    new_text = md_text
    for i, diagram in enumerate(diagrams, start=1):
        mmd_file = f"diagram_{i}.mmd"
        out_file = f"diagram_{i}.{output_format}"
        with open(mmd_file, "w", encoding="utf-8") as f:
            f.write(diagram)
        run_mmdc(mmd_file, out_file)
        new_text = new_text.replace(f"```mermaid\n{diagram}```", f"![Figure]({out_file})")
    return new_text

def replace_unicode_math(md_text: str) -> str:
    for uni, latex in UNICODE_REPLACEMENTS.items():
        md_text = md_text.replace(uni, latex)
    return md_text

import re
from typing import List, Tuple, Dict

def fix_internal_links(md_text: str) -> str:
    """
    Make internal hyperlinks work in Pandoc->LaTeX PDFs by:
      - Adding explicit {#id} to every heading (preserving existing ones).
      - Attaching \\hypertarget{target} to the best-matching heading for each internal link target.
      - Handling tricky cases like numbers/punctuation (e.g., '3.2.' -> '32-' prefix).
    This guarantees that [text](#target) resolves even if Pandoc's inferred IDs differ.
    """

    # 1) Collect all internal link targets like (#32-the-peoples-internet)
    link_targets = list(set(re.findall(r'\[.*?\]\(#([^)]+)\)', md_text)))

    # Utility: normalize title to a deterministic ID
    def normalize_title_to_id(title: str) -> str:
        t = title.lower()
        t = t.replace('&', ' and ')
        t = t.replace("'", "")  # handle “people's” -> “peoples”
        # Extract leading section number like "3.2." -> "32-"
        m = re.match(r'^\s*(\d+(?:\.\d+)+\.)\s*(.*)$', t)
        prefix = ""
        if m:
            nums, rest = m.groups()
            digits = re.sub(r'\.', '', nums[:-1])  # remove trailing dot and dots inside
            prefix = digits + "-"
            t = rest
        # Remove non-alphanumeric to hyphens
        t = re.sub(r'[^a-z0-9]+', '-', t)
        t = re.sub(r'-{2,}', '-', t).strip('-')
        return prefix + t

    # Utility: score how well a target matches a heading id/title
    def match_score(target: str, heading_id: str, title: str) -> int:
        # Compare tokens to avoid punctuation pitfalls
        def tokens(s: str) -> List[str]:
            s = s.lower()
            s = re.sub(r'[^a-z0-9]+', ' ', s)
            return [w for w in s.split() if w]

        t_tokens = tokens(target)
        h_tokens = tokens(heading_id)
        title_tokens = tokens(title)

        # Score shared tokens (weighted)
        shared = len(set(t_tokens) & set(h_tokens)) + len(set(t_tokens) & set(title_tokens))

        # Bonus if numeric prefix matches
        m_t = re.match(r'^(\d+)-', target)
        m_h = re.match(r'^(\d+)-', heading_id)
        if m_t and m_h and m_t.group(1) == m_h.group(1):
            shared += 2

        # Bonus if target equals heading_id
        if target == heading_id:
            shared += 5

        return shared

    # 2) Parse headings and build a structure we can rewrite
    #    Pattern captures: leading marks (###), title, optional existing anchor {#id}
    heading_pat = re.compile(r'^(#{1,6})\s+(.+?)(?:\s*\{#([^\}]+)\})?\s*$', re.MULTILINE)
    headings: List[Tuple[int, str, str, int]] = []  # (level, title, id, start_index)
    rewritten = md_text
    offset = 0  # track index shifts while rewriting

    # First pass: add/ensure explicit {#id} for every heading
    for m in list(heading_pat.finditer(md_text)):
        marks, title, existing_id = m.groups()
        level = len(marks)
        start, end = m.span()

        if existing_id:
            final_id = existing_id
            new_line = f"{marks} {title} {{#{final_id}}}"
        else:
            # Generate deterministic ID
            final_id = normalize_title_to_id(title)
            new_line = f"{marks} {title} {{#{final_id}}}"

        # Rewrite the line in the text
        rewritten = rewritten[:start + offset] + new_line + rewritten[end + offset:]
        # Record heading metadata; start_index updated with current offset
        headings.append((level, title, final_id, start + offset))
        offset += len(new_line) - (end - start)

    # 3) For each link target, attach a raw LaTeX \hypertarget to the best matching heading
    #    This guarantees the target exists as a clickable anchor in the PDF.
    if link_targets:
        # Build quick lookup for insertion: map start_index->insertion strings
        inserts: Dict[int, List[str]] = {}

        for target in link_targets:
            # Find best heading match
            best = None
            best_score = -1
            for (level, title, hid, start_idx) in headings:
                s = match_score(target, hid, title)
                if s > best_score:
                    best_score = s
                    best = (level, title, hid, start_idx)

            if best:
                level, title, hid, start_idx = best
                # Insert hypertarget right after the heading line
                # We place it on the next line to keep Markdown clean
                latex_anchor = f"\n\\hypertarget{{{target}}}{{}}\n"
                inserts.setdefault(start_idx, []).append(latex_anchor)

        # Second pass: inject anchors after the matched headings
        # We need to find the end of each heading line to insert after it.
        # Re-scan rewritten text to get updated positions.
        final_text = rewritten
        offset = 0
        for m in list(heading_pat.finditer(rewritten)):
            start, end = m.span()
            if start in inserts:
                # Insert after the heading line
                to_insert = "".join(inserts[start])
                final_text = final_text[:end + offset] + to_insert + final_text[end + offset:]
                offset += len(to_insert)

        rewritten = final_text

    return rewritten

def fix_relative_paths(md_text: str, base_dir: Path) -> str:
    """Ensure images and links resolve correctly."""
    # Fix image paths
    md_text = re.sub(r'!\[(.*?)\]\((.*?)\)', 
        lambda m: f"![{m.group(1)}]({(base_dir / m.group(2)).resolve()})", md_text)
    # Fix local markdown links (convert to absolute paths so Pandoc can find them)
    md_text = re.sub(r'\[([^\]]+)\]\((\.\/[^\)]+)\)', 
        lambda m: f"[{m.group(1)}]({(base_dir / m.group(2)).resolve()})", md_text)
    return md_text

def insert_page_breaks(md_text: str) -> str:
    """
    Insert page breaks before each new chapter heading (# or ##),
    except the very first document title '# Expanded Human Rights Framework'.
    """
    lines = md_text.splitlines()
    new_lines = []
    first_title_seen = False

    for line in lines:
        if line.startswith("# "):
            if not first_title_seen and "Expanded Human Rights Framework" in line:
                # First title: keep as-is
                first_title_seen = True
                new_lines.append(line)
            else:
                # Insert page break before subsequent top-level headings
                new_lines.append("\\newpage")
                new_lines.append(line)
        elif line.startswith("## "):
            # Insert page break before sub-chapter headings
            new_lines.append("\\newpage")
            new_lines.append(line)
        else:
            new_lines.append(line)

    return "\n".join(new_lines)

def add_yaml_header(
    md_text: str,
    use_fonts: bool = False,
    add_macros: bool = False,
    unicode_math: bool = True,
    style_links: bool = True,
    header_footer: bool = True,
    author: str = "Amit Kumar",
    title: str = "Expanded Human Rights Framework",
) -> str:
    """
    YAML header for Pandoc + XeLaTeX on Windows (MiKTeX-safe).
    Adds font setup, macros, unicode math, hyperlink styling,
    dynamic headers/footers, and author/title metadata.
    """
    header_lines = ["---"]

    # Metadata
    if title:
        header_lines.append(f'title: "{title}"')
    if author:
        header_lines.append(f'author: "{author}"')

    # Fonts
    if use_fonts:
        header_lines.extend([
            'mainfont: "Noto Sans"',
            'sansfont: "Noto Sans"',
            'monofont: "Noto Sans Mono"',
            'mathfont: "Latin Modern Math"',
            "header-includes:",
            "  - \\usepackage{fontspec}",
            "  - \\defaultfontfeatures{Ligatures=TeX}",
            "  - \\setmainfont{Noto Sans}",
            "  - \\setsansfont{Noto Sans}",
            "  - \\setmonofont{Noto Sans Mono}",
        ])

    # Unicode math
    if unicode_math:
        if "header-includes:" not in header_lines:
            header_lines.append("header-includes:")
        header_lines.extend([
            "  - \\usepackage{unicode-math}",
            "  - \\setmathfont{Latin Modern Math}",
        ])

    # Custom macros
    if add_macros:
        if "header-includes:" not in header_lines:
            header_lines.append("header-includes:")
        header_lines.extend([
            "  - \\newcommand{\\R}{\\mathbb{R}}",
            "  - \\newcommand{\\vect}[1]{\\mathbf{#1}}",
        ])

    # Hyperlink styling
    if style_links:
        # Pandoc metadata variables for link colors
        header_lines.extend([
            "linkcolor: blue",
            "urlcolor: blue",
            "citecolor: blue",
            "colorlinks: true",
        ])
        if "header-includes:" not in header_lines:
            header_lines.append("header-includes:")
        header_lines.extend([
            "  - \\usepackage{soul}",  # underline
            "  - \\AtBeginDocument{%",
            "      \\let\\oldhref\\href",
            "      \\renewcommand{\\href}[2]{\\oldhref{#1}{\\ul{#2}}}%",
            "    }",
        ])

    # Header/Footer with chapter names
    if header_footer:
        if "header-includes:" not in header_lines:
            header_lines.append("header-includes:")
        header_lines.extend([
            "  - \\usepackage{fancyhdr}",
            "  - \\pagestyle{fancy}",
            "  - \\fancyhf{}",
            "  - \\fancyhead[LO]{\\rightmark}",    # subsection name on odd pages
            "  - \\fancyhead[RE]{\\leftmark}",     # section name on even pages
            "  - \\fancyfoot[RO]{\\thepage}",      # page number bottom right
            "  - \\fancyfoot[CO]{Draft}",          # footer center text
        ])

    header_lines.append("---\n")
    return "\n".join(header_lines) + md_text

def main():
    parser = argparse.ArgumentParser(
        description="Convert Markdown to PDF or LaTeX with Mermaid + Unicode replacement + path fixes"
    )
    parser.add_argument("-i", "--input", required=True, help="Input Markdown file")
    parser.add_argument("-o", "--output", help="Output file (default: snake_case of input)")
    parser.add_argument("--mermaid-format", choices=["svg", "png", "pdf"], default="svg")
    parser.add_argument("--use-fonts", action="store_true", help="Add YAML font header")
    parser.add_argument("--add-macros", action="store_true", help="Inject LaTeX macros into preamble")
    parser.add_argument("--latex", action="store_true", help="Output LaTeX instead of PDF")
    args = parser.parse_args()

    input_file = Path(args.input)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file {input_file} not found")

    # Default output filename
    if args.output:
        output_file = Path(args.output)
    else:
        ext = ".tex" if args.latex else ".pdf"
        output_file = Path(snake_case(input_file.stem) + ext)

    processed_md = input_file.with_suffix(".processed.md")

    # Read original Markdown
    text = input_file.read_text(encoding="utf-8")

    # Process Mermaid diagrams
    text = render_mermaid_blocks(text, output_format=args.mermaid_format)

    # Replace Unicode math
    text = replace_unicode_math(text)

    # Fix relative paths
    text = fix_relative_paths(text, input_file.parent)
    # Fix internal links
    text = fix_internal_links(text)

    # Enforce heading IDs to match links
    # text = enforce_heading_ids(text)

    # Insert page breaks before chapters
    text = insert_page_breaks(text)

    # Add YAML header (fonts + macros)
    text = add_yaml_header(text, use_fonts=args.use_fonts, add_macros=args.add_macros)

    # Save processed Markdown
    processed_md.write_text(text, encoding="utf-8")

    # Run Pandoc → PDF or LaTeX
    if args.latex:
        pandoc_cmd = ["pandoc", str(processed_md), "-o", str(output_file)]
    else:
        pandoc_cmd = [
            "pandoc", str(processed_md),
            "-o", str(output_file),
            "--pdf-engine=xelatex",
            "--resource-path", str(input_file.parent),
            "--top-level-division=chapter"
        ]

    subprocess.run(pandoc_cmd, check=True)

    print(f"✅ File generated: {output_file}")

if __name__ == "__main__":
    main()