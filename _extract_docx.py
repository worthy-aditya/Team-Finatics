/"""Extract readable text from SentinelAI_30Day_Sprint.docx for review."""
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

SRC = "SentinelAI_30Day_Sprint.docx"
OUT = "SENTINELAI_30DAY_SPRINT_EXTRACTED.md"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}

def extract_text(path: str) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    lines = []
    for p in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        # Paragraph text from all w:t runs
        text = "".join(t.text or "" for t in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"))
        # Detect heading style for markdown-ish emphasis
        style = p.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pStyle")
        if style is not None:
            sid = style.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", "")
            if sid and "Heading" in sid:
                text = f"\n## {text}\n"
        lines.append(text.rstrip())
    return "\n".join(lines)

def main() -> None:
    body = extract_text(SRC)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"Wrote {OUT}: {len(body)} chars, {len(body.splitlines())} lines")

if __name__ == "__main__":
    main()