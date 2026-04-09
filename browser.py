from __future__ import annotations

import argparse
import dataclasses
import html
import json
import re
from pathlib import Path
from typing import Any

import gradio as gr

_ROOT = Path(__file__).resolve().parent
DATA_PATH = _ROOT / "data" / "study-2-annotated-dataset.json"
CSS_PATH = _ROOT / "browser.css"

_CSS = CSS_PATH.read_text(encoding="utf-8")
TABLE_PREFIX = (
    f'<div class="browser-wrap"><style>{_CSS}</style>'
    '<table class="browser">'
    '<caption class="browser-sr-only">Product images with quality and content annotations</caption>'
    "<thead><tr>"
)
TABLE_CLOSE = "</tbody></table>"
WRAP_CLOSE = "</div>"

IMAGE_COLUMN = "__image__"
_ANNOTATION_COLUMNS = frozenset({"product", "brand", "variety"})
_NON_BOOL_COLUMNS = frozenset({IMAGE_COLUMN, "id", "file_name", "image_type"} | _ANNOTATION_COLUMNS)
TEXT_SEARCH_KEYS: tuple[str, str, str] = ("product", "brand", "variety")

HEADER_COLUMNS: list[str] = [
    IMAGE_COLUMN,
    "id",
    "file_name",
    "image_type",
    "unrecognizable",
    "blur",
    "framing",
    "rotation",
    "obstruction",
    "too dark",
    "too bright",
    "other",
    "rounded_label",
    "text_panel",
    "product",
    "brand",
    "variety",
]

HEADER_COLUMN_LABELS: dict[str, str] = {
    IMAGE_COLUMN: "Preview (click to expand)",
    "id": "VizWiz ID",
    "file_name": "VizWiz File Name",
    "image_type": "Image Type",
    "unrecognizable": "Unrecognizable",
    "blur": "Blur",
    "framing": "Framing",
    "rotation": "Rotation",
    "obstruction": "Obstruction",
    "too dark": "Too Dark",
    "too bright": "Too Bright",
    "other": "Other",
    "rounded_label": "Rounded Label",
    "text_panel": "Text Panel",
    "product": "Product",
    "brand": "Brand",
    "variety": "Variety",
}

_missing = [c for c in HEADER_COLUMNS if c not in HEADER_COLUMN_LABELS]
if _missing:
    raise ValueError(f"HEADER_COLUMN_LABELS missing keys: {_missing}")

BOOL_FILTER_COLUMNS: list[str] = [c for c in HEADER_COLUMNS if c not in _NON_BOOL_COLUMNS]
BOOL_CHECKBOX_CHOICES: list[str] = ["Yes", "No"]

# ── Data loading ──
RECORDS: list[dict] = json.loads(DATA_PATH.read_text(encoding="utf-8"))
TOTAL: int = len(RECORDS)
IMAGE_TYPE_CHOICES: list[str] = sorted({r["image_type"] for r in RECORDS if "image_type" in r})


# ── Generic helpers ──
def _safe_int(val: Any, default: int, lo: int | None = None, hi: int | None = None) -> int:
    try:
        v = int(float(val))
    except TypeError, ValueError:
        return default
    if lo is not None:
        v = max(lo, v)
    if hi is not None:
        v = min(hi, v)
    return v


def _coerce_checkbox_list(x: Any, allowed: set[str]) -> list[str]:
    if not isinstance(x, (list, tuple)):
        return []
    return [str(item).strip() for item in x if str(item).strip() in allowed]


def _norm_search(q: str | None) -> str:
    return str(q).strip().lower() if q else ""


# ── Filtering ──
@dataclasses.dataclass(frozen=True)
class FilterState:
    image_types: list[str]
    bool_filters: list[list[str]]
    text_search: tuple[str, str, str]

    @classmethod
    def default(cls) -> FilterState:
        return cls(
            image_types=list(IMAGE_TYPE_CHOICES),
            bool_filters=[list(BOOL_CHECKBOX_CHOICES) for _ in BOOL_FILTER_COLUMNS],
            text_search=("", "", ""),
        )

    @classmethod
    def from_gradio_values(cls, *vals: Any) -> FilterState:
        """Parse the flat list of Gradio component values into a FilterState.

        Expected order: [image_type_cbg, *bool_cbgs, product_txt, brand_txt, variety_txt]
        """
        n_bool = len(BOOL_FILTER_COLUMNS)
        need = 1 + n_bool + 3
        fv = list(vals[:need])
        fv.extend([None] * (need - len(fv)))

        img = _coerce_checkbox_list(fv[0], set(IMAGE_TYPE_CHOICES))
        bools = [_coerce_checkbox_list(fv[1 + i], set(BOOL_CHECKBOX_CHOICES)) for i in range(n_bool)]
        off = 1 + n_bool
        texts = (
            str(fv[off] or ""),
            str(fv[off + 1] or ""),
            str(fv[off + 2] or ""),
        )
        return cls(image_types=img, bool_filters=bools, text_search=texts)

    def default_updates(self) -> list[dict[str, Any]]:
        """Gradio update dicts to reset all filter components to defaults."""
        d = FilterState.default()
        return [
            gr.update(value=d.image_types),
            *[gr.update(value=bf) for bf in d.bool_filters],
            *[gr.update(value=t) for t in d.text_search],
        ]


def _annotation_blob_lower(row: dict, key: str) -> str:
    items = row.get(key)
    if not isinstance(items, list):
        return ""
    return " ".join(it.get("text", "") for it in items if isinstance(it, dict)).lower()


def _bool_matches(val: object, selected: list[str]) -> bool:
    n = len(selected)
    if n == 0 or n == 2:
        return True
    return (val is True) if "Yes" in selected else (val is not True)


def _image_type_constrains(selection: list[str]) -> bool:
    return bool(selection) and set(selection) != set(IMAGE_TYPE_CHOICES)


def row_passes_filters(row: dict, fs: FilterState) -> bool:
    if _image_type_constrains(fs.image_types):
        if row.get("image_type", "") not in fs.image_types:
            return False
    for key, q in zip(TEXT_SEARCH_KEYS, fs.text_search, strict=True):
        nq = _norm_search(q)
        if nq and nq not in _annotation_blob_lower(row, key):
            return False
    for key, selected in zip(BOOL_FILTER_COLUMNS, fs.bool_filters, strict=True):
        if not _bool_matches(row.get(key), selected):
            return False
    return True


def iter_filtered(fs: FilterState) -> list[dict]:
    return [r for r in RECORDS if row_passes_filters(r, fs)]


# ── Pagination ──
def _total_pages(n: int, ps: int) -> int:
    if n <= 0:
        return 1
    return max(1, (n + ps - 1) // ps)


# ── Annotation formatting ──
def _highlight_icase(text: str, query_norm: str) -> str:
    if not query_norm:
        return html.escape(text)
    pat = re.compile(re.escape(query_norm), re.IGNORECASE)
    chunks: list[str] = []
    pos = 0
    for m in pat.finditer(text):
        chunks.append(html.escape(text[pos : m.start()]))
        chunks.append(f"<strong>{html.escape(m.group(0))}</strong>")
        pos = m.end()
    chunks.append(html.escape(text[pos:]))
    return "".join(chunks)


def _format_annotation_html(items: Any, query_raw: str) -> str:
    if not isinstance(items, list):
        return ""
    qn = _norm_search(query_raw)
    parts: list[str] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        t = str(it.get("text", ""))
        core = _highlight_icase(t, qn) if qn else html.escape(t)
        parts.append(f"{core} (optional)" if it.get("optional") else core)
    return "; ".join(parts)


# ── Cell rendering ──
_IMAGE_TYPE_CSS = {"high-quality": "browser-cat-hq", "low-quality": "browser-cat-lq"}


def _cell_html(col: str, val: object) -> str:
    if col == "image_type":
        s = str(val) if val is not None else ""
        if not s:
            return ""
        cls = _IMAGE_TYPE_CSS.get(s, "browser-cat-unknown")
        return f'<span class="browser-cat {cls}">{html.escape(s)}</span>'
    if col in BOOL_FILTER_COLUMNS:
        if val is True:
            return '<span class="browser-val-yes">yes</span>'
        if val is False:
            return '<span class="browser-val-no">no</span>'
        return ""
    if val is None:
        return ""
    if isinstance(val, bool):
        return "yes" if val else "no"
    return html.escape(str(val))


# ── Image alt text ──
def _annotation_plain_text(row: dict, key: str) -> str:
    items = row.get(key)
    if not isinstance(items, list):
        return ""
    return ", ".join(str(it.get("text", "")) for it in items if isinstance(it, dict) and it.get("text"))


def _img_alt(row: dict) -> str:
    parts = []
    for key in TEXT_SEARCH_KEYS:
        text = _annotation_plain_text(row, key)
        if text:
            parts.append(f"{HEADER_COLUMN_LABELS[key]}: {text}")
    annotation = "; ".join(parts) if parts else "no annotations"
    return f"Product image, annotated with {annotation}"


# ── Lightbox for expanded image ──
def _lightbox_id(row: dict) -> str:
    return f"browser-full-{row['id']}"


def _lightbox_annotation(row: dict, ts: tuple[str, str, str]) -> str:
    parts: list[str] = []
    for col, q in zip(TEXT_SEARCH_KEYS, ts, strict=True):
        rendered = _format_annotation_html(row.get(col), q)
        val = rendered or '<span class="browser-lightbox-empty">None listed</span>'
        lab = html.escape(HEADER_COLUMN_LABELS[col])
        parts.append(
            f'<span class="browser-lightbox-meta-label">{lab}:</span> '
            f'<span class="browser-lightbox-meta-value">{val}</span>'
        )
    row_html = " | ".join(parts)
    return f'<div class="browser-lightbox-meta"><div class="browser-lightbox-meta-line">{row_html}</div></div>'


def _lightbox_html(row: dict, ts: tuple[str, str, str]) -> str:
    url = html.escape(row.get("vizwiz_url", ""), quote=True)
    alt = html.escape(_img_alt(row), quote=True)
    lb_id = html.escape(_lightbox_id(row), quote=True)
    meta = _lightbox_annotation(row, ts)
    return (
        f'<div id="{lb_id}" class="browser-lightbox" role="dialog" '
        f'aria-modal="true" aria-label="{alt}">'
        '<a href="#" class="browser-lightbox-backdrop" aria-label="Close"></a>'
        '<div class="browser-lightbox-body"><div class="browser-lightbox-stack">'
        f'<div class="browser-lightbox-stack-img"><div><img src="{url}" alt="{alt}"></div></div>'
        f'<div class="browser-lightbox-stack-meta"><div>{meta}</div></div>'
        "</div></div>"
        '<a href="#" class="browser-lightbox-close" aria-label="Close">&times;</a>'
        "</div>"
    )


# ── Row / table HTML ──
def _row_html(row: dict, ts: tuple[str, str, str]) -> str:
    url = html.escape(row.get("vizwiz_url", ""), quote=True)
    alt = html.escape(_img_alt(row), quote=True)
    href = html.escape(f"#{_lightbox_id(row)}", quote=True)
    thumb = f'<a href="{href}" class="browser-thumb-link"><img src="{url}" alt="{alt}" loading="lazy"></a>'
    ann_q = dict(zip(TEXT_SEARCH_KEYS, ts, strict=True))
    cells = [thumb]
    for col in HEADER_COLUMNS[1:]:
        if col in _ANNOTATION_COLUMNS:
            cells.append(_format_annotation_html(row.get(col), ann_q[col]))
        else:
            cells.append(_cell_html(col, row.get(col)))
    return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"


def _build_table(rows: list[dict], ts: tuple[str, str, str]) -> str:
    header = "".join(f'<th scope="col">{html.escape(HEADER_COLUMN_LABELS[col])}</th>' for col in HEADER_COLUMNS)
    body = "".join(_row_html(r, ts) for r in rows)
    lightboxes = "".join(_lightbox_html(r, ts) for r in rows)
    return TABLE_PREFIX + header + "</tr></thead><tbody>" + body + TABLE_CLOSE + lightboxes + WRAP_CLOSE


def render_page(page: int, page_size: Any, fs: FilterState) -> tuple[str, str, dict[str, Any]]:
    ps = _safe_int(page_size, 10, 1, 50)
    filtered = iter_filtered(fs)
    n = len(filtered)
    tp = _total_pages(n, ps)
    p = _safe_int(page, 1, 1, tp)
    start = (p - 1) * ps
    end = min(start + ps, n)
    table = _build_table(filtered[start:end], fs.text_search)
    if TOTAL == 0:
        status = "No records in dataset."
    elif n == 0:
        status = f"0 matching records (filtered from {TOTAL} total)."
    elif n == TOTAL:
        status = f"Page {p} of {tp} · Showing {start + 1}–{end} of {n} total"
    else:
        status = f"Page {p} of {tp} · Showing {start + 1}–{end} of {n} (filtered from {TOTAL} total)"
    return table, status, gr.update(value=p, maximum=tp, minimum=1)


# ── Gradio app ──
BOOL_CHUNK_SIZE = 5


def create_app() -> gr.Blocks:
    initial_ps = 10
    initial_tp = _total_pages(TOTAL, initial_ps)

    with gr.Blocks(title="Product Image Dataset Browser") as demo:
        gr.Markdown(
            '# Product Dataset and Annotation Browser for *"It\'s trained by non-disabled people":'
            " Evaluating How Image Quality Affects Product Captioning with Vision-Language Models* (CHI 2026)"
        )
        gr.Markdown(
            "[![repo](https://img.shields.io/badge/github-repo-blue?logo=github)](https://github.com/Accessibility-Research-Collective-UCI/image-quality-vlm-chi26)"
        )
        gr.Markdown(
            "Authors: [Kapil Garg](https://www.kgarg.com/), "
            "[Xinru Tang](https://xinrutang.github.io/), "
            "[Jimin Heo](https://hjimjim.github.io/), "
            "[Dwayne R. Morgan](https://1iconic1.github.io/DwayneMorgan/), "
            "[Darren Gergle](https://dgergle.soc.northwestern.edu/), "
            "[Erik B. Sudderth](https://ics.uci.edu/~sudderth/), "
            "[Anne Marie Piper](https://ics.uci.edu/~ampiper/)"
        )
        gr.Markdown(
            "This dataset browser allows for exploration of the dataset developed in our paper. "
            "We selected 1,859 product images taken by blind and low-vision (BLV) people "
            "from the [VizWiz](https://vizwiz.cs.colorado.edu/) dataset, "
            "including 729 high-quality images (without any image quality issues) "
            "and 1,130 low-quality images (with at least one image quality issue). "
            "These were annotated with product, brand, "
            "and variety information. For more details, please refer to our "
            "[paper](https://arxiv.org/abs/2511.08917) (see Section 4.2)."
        )

        # ── Filters ──
        gr.Markdown("## Filters")
        filter_inputs: list[Any] = []
        with gr.Accordion(open=True):
            gr.Markdown("### Image Type")
            filter_inputs.append(
                gr.CheckboxGroup(
                    choices=IMAGE_TYPE_CHOICES,
                    value=list(IMAGE_TYPE_CHOICES),
                    show_label=False,
                    container=False,
                )
            )

            gr.Markdown("### Image Quality Issues and Product Properties")
            gr.Markdown(
                "Image quality issues were orignally defined as the count of crowdworkers "
                "who identified the issue in the image (between 0-5). In our dataset, we "
                "convert these to binary labels, with the value as 'yes' if at least 2 "
                "crowdworkers identified the issue. Rounded Label (e.g., cans) and Text Panel "
                "(e.g., nutrition label) were annotated by the researchers. "
            )
            for i in range(0, len(BOOL_FILTER_COLUMNS), BOOL_CHUNK_SIZE):
                chunk = BOOL_FILTER_COLUMNS[i : i + BOOL_CHUNK_SIZE]
                with gr.Row():
                    for key in chunk:
                        filter_inputs.append(
                            gr.CheckboxGroup(
                                choices=BOOL_CHECKBOX_CHOICES,
                                value=list(BOOL_CHECKBOX_CHOICES),
                                label=HEADER_COLUMN_LABELS[key],
                            )
                        )

            gr.Markdown("### Product Annotation Search")
            gr.Markdown(
                "- Product: the generic term for the product (e.g., cereal, soup, meal, medication).\n"
                "- Brand: any detectable brand information (e.g., Betty Crocker, Kraft, Great Value, Kellogg's).\n"
                "- Variety: details about the type, flavor, or variety (e.g., peanut, low sodium)."
            )
            with gr.Row():
                for key in TEXT_SEARCH_KEYS:
                    filter_inputs.append(
                        gr.Textbox(
                            label=f"{HEADER_COLUMN_LABELS[key]} contains...",
                            placeholder="substring…",
                            lines=1,
                        )
                    )
            clear_btn = gr.Button("Clear filters")

        # ── Pagination ──
        gr.Markdown("## Image and Annotation Browser")
        with gr.Row():
            page_input = gr.Number(label="Page", value=1, minimum=1, maximum=initial_tp, step=1, precision=0)
            page_size = gr.Dropdown(choices=[10, 25, 50], value=initial_ps, label="Images per page")
        status_md = gr.Markdown(value="Loading…")
        table_html = gr.HTML(value="<p>Loading…</p>")
        with gr.Row():
            prev_btn = gr.Button("Previous")
            next_btn = gr.Button("Next")

        # ── Wiring ──
        out = [table_html, status_md, page_input]
        out_and_filters = out + filter_inputs

        def _navigate(page: int, ps: Any, *fv: Any):
            return render_page(page, ps, FilterState.from_gradio_values(*fv))

        prev_btn.click(
            lambda p, ps, *fv: _navigate(_safe_int(p, 1) - 1, ps, *fv),
            [page_input, page_size, *filter_inputs],
            out,
        )
        next_btn.click(
            lambda p, ps, *fv: _navigate(_safe_int(p, 1) + 1, ps, *fv),
            [page_input, page_size, *filter_inputs],
            out,
        )
        page_input.change(
            lambda p, ps, *fv: _navigate(_safe_int(p, 1), ps, *fv),
            [page_input, page_size, *filter_inputs],
            out,
        )
        page_size.change(
            lambda p, ps, *fv: _navigate(_safe_int(p, 1), ps, *fv),
            [page_input, page_size, *filter_inputs],
            out,
        )

        def on_filter_change(ps: Any, *fv: Any):
            return render_page(1, ps, FilterState.from_gradio_values(*fv))

        gr.on(
            triggers=[comp.change for comp in filter_inputs],
            fn=on_filter_change,
            inputs=[page_size, *filter_inputs],
            outputs=out,
            trigger_mode="always_last",
        )

        def clear_filters(ps: Any):
            fs = FilterState.default()
            res = render_page(1, ps, fs)
            return (*res, *fs.default_updates())

        clear_btn.click(clear_filters, [page_size], out_and_filters)
        demo.load(
            lambda ps, *fv: render_page(1, ps, FilterState.from_gradio_values(*fv)),
            [page_size, *filter_inputs],
            out,
        )

    return demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the dataset browser.")
    parser.add_argument("--share", action="store_true", help="Enable public sharing.")
    args = parser.parse_args()
    create_app().launch(share=args.share, ssr_mode=False)


if __name__ == "__main__":
    main()
