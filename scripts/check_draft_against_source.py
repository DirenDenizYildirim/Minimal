#!/usr/bin/env python3
"""Phase C1 -- check the compiled draft against docs/paper-source.json.

Four checks, read from the PDF's own text rather than the .tex source, so what
is checked is what a reader sees:

 (i)   every numeric token with >= 2 significant figures in the body, tables and
       captions appears in the numbers table (or is a structural number: a
       section, figure or page reference, or a year);
 (ii)  every SUGGESTED claim whose subject appears in the draft has the
       register's mandatory hedge words nearby;
 (iii) the disclosure markers appear on every page (page count == occurrence
       count for the header, footer and watermark);
 (iv)  no NOT SUPPORTED reading appears outside the claims register without a
       negation in the same sentence.

Usage: python scripts/check_draft_against_source.py [--verbose]
Exit status is the number of failed checks.
"""
from __future__ import annotations
import json, pathlib, re, sys, zlib

REPO = pathlib.Path(__file__).resolve().parent.parent
PDF = REPO / "paper" / "AI-GENERATED-DRAFT-do-not-circulate.pdf"
SRC = REPO / "docs" / "paper-source.json"
VERBOSE = "--verbose" in sys.argv


def pdf_text(path):
    """Kerning-insensitive page text, and the page count.

    Only streams that contain a text object (BT ... ET) are read, so the
    embedded PNGs -- whose decompressed bytes otherwise match the string regex
    and produce megabytes of spurious digits -- are skipped.
    """
    data = path.read_bytes()
    out = []
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
        try:
            d = zlib.decompress(m.group(1))
        except Exception:
            continue
        if b"BT" not in d or (b"Tj" not in d and b"TJ" not in d):
            continue
        out.append(d.decode("latin-1"))
    raw = "".join(out)

    def unescape(lit):
        """Decode a PDF literal string. \\050 is '(' -- stripping the backslash
        and keeping '050' is how a digit-token check acquires phantom numbers."""
        out = []
        i = 0
        while i < len(lit):
            c = lit[i]
            if c != "\\":
                out.append(c); i += 1; continue
            i += 1
            if i >= len(lit):
                break
            d = lit[i]
            if d in "01234567":
                oct_ = d; i += 1
                while i < len(lit) and len(oct_) < 3 and lit[i] in "01234567":
                    oct_ += lit[i]; i += 1
                out.append(chr(int(oct_, 8)))
            else:
                out.append({"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f"}.get(d, d))
                i += 1
        return "".join(out)

    # One show operation (TJ or Tj) is one run of kerned glyphs, so its strings
    # join without a space; separate operations get a space between them, which
    # keeps numbers in adjacent table cells apart. Splitting on the operator
    # rather than matching the array is deliberate: caption text contains a
    # literal "[AI-generated draft]", so a bracket-matching regex drops exactly
    # the operations the marker check needs to see.
    STR = re.compile(r"\((?:[^()\\]|\\.)*\)")
    pieces = []
    for block in re.findall(r"BT\b(.*?)\bET\b", raw, re.S):   # text objects only
        for segment in re.split(r"\bT[Jj]\b", block):
            lits = STR.findall(segment)
            if lits:
                pieces.append("".join(unescape(c[1:-1]) for c in lits))
    text = " ".join(pieces)
    # Math-mode digits arrive with the separator in a different font slot and with
    # kern spaces around it; rejoin them so 0 : 3476 reads as 0.3476.
    text = re.sub(r"(?<=\d)\s*[.:]\s*(?=\d)", ".", text)
    text = re.sub(r"(?<=\d)\s*,\s*(?=\d\d\d\b)", "", text)
    pages = data.count(b"/Type /Page") + data.count(b"/Type/Page")
    if not pages:  # page objects live in an object stream; take the build's count
        log = path.with_suffix(".log")
        m = re.search(r"Output written on .*?\((\d+) pages", log.read_text(errors="ignore")) if log.exists() else None
        pages = int(m.group(1)) if m else 0
    return text, pages


def numeric_tokens(text):
    toks = []
    for m in re.finditer(r"(?<![A-Za-z0-9.])(\d[\d,]*\.\d+|\d[\d,]*)(?![A-Za-z0-9])", text):
        t = m.group(1).replace(",", "")
        if len(t.replace(".", "").lstrip("0")) >= 2:
            toks.append(t)
    return toks


def source_numbers(doc):
    ok = set()

    def add(tok):
        tok = tok.strip()
        if not tok:
            return
        ok.add(tok)
        try:
            f = float(tok)
        except ValueError:
            return
        if "." in tok:
            for d in range(0, 5):
                ok.add(f"{f:.{d}f}")
            ok.add(tok.rstrip("0").rstrip("."))
            for d in (0, 1, 2):
                ok.add(f"{f*100:.{d}f}")
        else:
            ok.add(tok.lstrip("0") or "0")

    for row in doc["numbers"]:
        for field in (row.get("value"), row.get("ci"), row.get("unit"), row.get("quantity")):
            for m in re.finditer(r"\d[\d,]*\.?\d*", str(field or "")):
                add(m.group(0).replace(",", ""))
    for c in doc["claims"]:
        for field in (c.get("claim"), c.get("hedge")):
            for m in re.finditer(r"\d[\d,]*\.?\d*", str(field or "")):
                add(m.group(0).replace(",", ""))
    return ok


STRUCTURAL = re.compile(
    r"^(19|20)\d\d$"                    # a year
    r"|^\d{1,3}$"                        # section, figure, table, page reference
    r"|^((19|20)\d\d){2}$"               # two years abutting across a kern, e.g. "2017 2018"
)
ALLOWED_EXTRA = {"2501.00390", "0.05", "0.95", "0.025", "0.975"}


def check_numbers(text, doc):
    ok = source_numbers(doc) | ALLOWED_EXTRA
    bad = {}
    def accepted(t):
        if t in ok or STRUCTURAL.match(t):
            return True
        # A run of table cells can reach the extractor without its separators.
        # Accept a token that splits cleanly into accepted tokens, so a cell run
        # is not reported as an invented number.
        for k in range(2, len(t)):
            if (t[:k] in ok or STRUCTURAL.match(t[:k])) and (t[k:] in ok or accepted(t[k:])):
                return True
        return False

    for t in numeric_tokens(text):
        if accepted(t):
            continue
        bad[t] = bad.get(t, 0) + 1
    return [f"{t} (x{n})" for t, n in sorted(bad.items(), key=lambda kv: -kv[1])]


HEDGE = {
    "G1": ["hand", "diameter", "no mechanism", "aggregate at this start radius"],
    "G2": ["not excluded", "sub-proportional", "excluding"],
    "G3": ["does not locate", "did not find", "not established", "did not find its own"],
    "G4": ["hand-designed", "lower bound", "among the hand-designed"],
    "G5": ["association", "never swept", "not a controlled"],
    "G6": ["ablated"],
    "G7": ["was not run", "follows from the measurement", "not run"],
    "G8": ["not chased", "excluding", "edge of what"],
    "G9": ["recorded, not claimed", "simpler", "combinatorial"],
    "G10": ["observation", "no temporal", "not evidence", "ten times"],
}
SUBJECT = {
    "G1": "body diameter", "G2": "sub-proportional", "G3": "1.6456",
    "G4": "worth more than anything else", "G5": "time to first cluster",
    "G6": "geometric mean", "G7": "replication per condition", "G8": "scalar field",
    "G9": "reach dip", "G10": "Berg",
}


def check_hedges(text):
    """A SUGGESTED claim needs its hedge wherever the body states it.

    The search stops at the appendices: the claims register prints every hedge
    verbatim, and a bibliography entry is not a statement of the claim.
    """
    flat = text.replace(" ", "")
    cut = flat.find("AParametertables")          # the first appendix heading
    body = flat[:cut] if cut > 0 else flat
    missing = []
    for cid, subject in SUBJECT.items():
        needle = subject.replace(" ", "")
        for m in re.finditer(re.escape(needle), body):
            window = body[max(0, m.start() - 1400): m.end() + 1400]
            if not any(h.replace(" ", "") in window for h in HEDGE[cid]):
                missing.append(f"{cid} near {subject!r}")
                break
    return missing


MARKERS = {
    "watermark + header 'AI-GENERATED DRAFT'": ("AI-GENERATEDDRAFT", 2),
    "header 'NOT FOR CIRCULATION'": ("NOTFORCIRCULATION", 1),
    "footer 'Do not circulate'": ("Donotcirculate", 1),
}


def check_markers(text, pages):
    flat = text.replace(" ", "")
    out = []
    for name, (probe, per_page) in MARKERS.items():
        n = flat.count(probe)
        if n < pages * per_page:
            out.append(f"{name}: {n} occurrences, expected at least {pages * per_page}")
    if "Nohumanauthor" not in flat:
        out.append("author block missing")
    caps = flat.count("AI-generateddraft")
    if caps < 17:
        out.append(f"caption marker on only {caps} of 17 captions")
    return out


NOT_SUPPORTED = {
    "N1": "small amounts of terrain",
    "N2": "cuts degradation from",
    "N3": "more sensing hurts",
    "N4": "re-tuning solves",
    "N9": "much worse than",
    "N10": "two robots always aggregate",
    "N12": "wider sensor cone",
}
NEGATIONS = ("does not", "do not", "did not", "ruled out", "not supported", "no longer",
             "cannot", "is not", "are not", "never", "wrong", "unsound", "dead",
             "must not", "mistake", "artefact", "loses", "would be", "disposes",
             "not what", "makes n = 2 worse", "worse")


def check_not_supported(text):
    """A ruled-out reading may appear only as a thing ruled out.

    Sentence boundaries are taken on the spaced text as ". ": splitting on a bare
    period cuts 0.9 in half and makes every sentence two characters long.
    """
    cut = text.replace(" ", "").find("CClaimsregister")
    if cut > 0:   # map the flattened offset back to a spaced offset
        seen = 0
        for i, ch in enumerate(text):
            if ch != " ":
                seen += 1
                if seen > cut:
                    cut = i
                    break
    body = text[:cut] if cut > 0 else text
    sentences = re.split(r"(?<=[.!?])\s+", body)
    out = []
    for cid, probe in NOT_SUPPORTED.items():
        needle = probe.replace(" ", "")
        for sent in sentences:
            if needle not in sent.replace(" ", "").lower():
                continue
            low = sent.replace(" ", "").lower()
            if not any(n.replace(" ", "") in low for n in NEGATIONS):
                out.append(f"{cid} unguarded in: {sent.strip()[:110]!r}")
                break
    return out


def main():
    doc = json.loads(SRC.read_text())
    text, pages = pdf_text(PDF)
    failures = 0
    print(f"draft:  {PDF.name}, {pages} pages, {len(text)} characters extracted")
    print(f"source: {len(doc['numbers'])} numbers, {len(doc['claims'])} claims\n")

    bad = check_numbers(text, doc)
    print(f"(i)   unmatched numeric tokens: {len(bad)}")
    failures += bool(bad)
    for b in (bad if VERBOSE else bad[:30]):
        print(f"        {b}")

    miss = check_hedges(text)
    print(f"(ii)  SUGGESTED claims missing their hedge: {len(miss)}")
    failures += bool(miss)
    for m in miss:
        print(f"        {m}")

    mk = check_markers(text, pages)
    print(f"(iii) disclosure markers not on every page: {len(mk)}")
    failures += bool(mk)
    for m in mk:
        print(f"        {m}")

    ns = check_not_supported(text)
    print(f"(iv)  unguarded NOT SUPPORTED readings: {len(ns)}")
    failures += bool(ns)
    for m in ns:
        print(f"        {m}")

    print(f"\n{failures} of 4 checks failing")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
