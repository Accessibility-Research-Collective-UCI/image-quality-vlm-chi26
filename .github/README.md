# Dataset of Product Images Taken by BLV People

[![arxiv](https://img.shields.io/badge/arXiv-2511.08917-b31b1b.svg)](https://arxiv.org/abs/2511.08917)
[![chi-2026](https://img.shields.io/badge/CHI-2026-blueviolet?logo=google-scholar&logoColor=white)](https://doi.org/10.1145/3772318.3791309)

### [Paper](https://arxiv.org/abs/2511.08917) (CHI 2026)

This is a companion repo for the paper, _"It's trained by non-disabled people": Evaluating How Image Quality Affects Product Captioning with Vision-Language Models_, which studies the impact of image quality issues on product identification accuracy with vision-language models (VLMs). We include the dataset we developed for our study and a dataset browser. The dataset browser is also hosted on [Hugging Face Spaces](https://huggingface.co/spaces/kgarg0/BLV-People-Product-Images).

**Authors:** [Kapil Garg](https://www.kgarg.com/)<sup>1</sup>, [Xinru Tang](https://xinrutang.github.io/)<sup>1</sup>, [Jimin Heo](https://hjimjim.github.io/)<sup>1</sup>, [Dwayne R. Morgan](https://1iconic1.github.io/DwayneMorgan/)<sup>1</sup>, [Darren Gergle](https://dgergle.soc.northwestern.edu/)<sup>2</sup>, [Erik B. Sudderth](https://ics.uci.edu/~sudderth/)<sup>1</sup>, [Anne Marie Piper](https://ics.uci.edu/~ampiper/)<sup>1</sup>

<sub>1: University of California, Irvine; 2: Northwestern University</sub>

## Dataset Description

We selected 1,859 product images taken by blind and low-vision (BLV) people from the [VizWiz](https://vizwiz.cs.colorado.edu/) dataset, including 729 high-quality images (without any image quality issues) and 1,130 low-quality images (with at least one image quality issue). Each image was annotated with product, brand, and variety information. For more details, please refer to our [paper](https://arxiv.org/abs/2511.08917) (see Section 4.2).

`data/` includes our annotated dataset in `.csv` and `.json`. Dataset details are available below. Original fields are derived from the [VizWiz](https://vizwiz.cs.colorado.edu/) dataset ([Gurari et al., ECCV 2020](https://vizwiz.org/tasks-and-datasets/image-captioning/), [Chiu et al., CVPR 2020](https://vizwiz.org/tasks-and-datasets/image-quality-issues/)).

<details>
<summary><strong><code>JSON</code> Data Fields & Types</strong> (click to expand)</summary>

**Original VizWiz fields:**

| Field                            | Type | Description                                                                     |
| -------------------------------- | ---- | ------------------------------------------------------------------------------- |
| <code>id</code>                  | int  | VizWiz ID                                                                       |
| <code>file_name</code>           | str  | VizWiz image file                                                               |
| <code>vizwiz_url</code>          | str  | Image URL                                                                       |
| <code>text_detected</code>       | bool | OCR detected text                                                               |
| <code>unrecognizable_orig</code> | int  | Number of crowdworkers (0-5) who found the image unrecognizable.                |
| <code>blur_orig</code>           | int  | Number of crowdworkers (0-5) who identified blur.                               |
| <code>rotation_orig</code>       | int  | Number of crowdworkers (0-5) who identified rotation.                           |
| <code>framing_orig</code>        | int  | Number of crowdworkers (0-5) who identified framing issues.                     |
| <code>obstruction_orig</code>    | int  | Number of crowdworkers (0-5) who identified an obstruction blocking the image.  |
| <code>too_dark_orig</code>       | int  | Number of crowdworkers (0-5) who found the image too dark to easily identify.   |
| <code>too_bright_orig</code>     | int  | Number of crowdworkers (0-5) who found the image too bright to easily identify. |
| <code>other_orig</code>          | int  | Number of crowdworkers (0-5) who identified other issues not included above.    |

**Our annotation fields:**

| Field                                                                                                                                                                  | Type | Description                                                                                                                                          |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| <code>image_type</code>                                                                                                                                                | str  | <code>high-quality</code> \| <code>low-quality</code>                                                                                                |
| <code>unrecognizable</code>, <code>blur</code>, <code>framing</code>,<br><code>obstruction</code>,<code>too_dark</code>,<br><code>too_bright</code>,<code>other</code> | bool | True if respective <code>\_orig</code> field ≥ 2                                                                                                     |
| <code>rotation</code>                                                                                                                                                  | bool | True if ≥ 45° off typical orientation, as coded by 2 researchers                                                                                     |
| <code>rounded_label</code>                                                                                                                                             | bool | If product has a rounded label, like canned goods. Annotated by researchers                                                                          |
| <code>text_panel</code>                                                                                                                                                | bool | If product has a text panel, like a nutrition fact label. Annotated by researchers.                                                                  |
| <code>product</code>                                                                                                                                                   | list | List of <code>{"text": str, "optional": bool}</code> entries. The generic term for the product (e.g., cereal, soup, meal, medication).               |
| <code>brand</code>                                                                                                                                                     | list | List of <code>{"text": str, "optional": bool}</code> entries. Any detectable brand information (e.g., Betty Crocker, Kraft, Great Value, Kellogg's). |
| <code>variety</code>                                                                                                                                                   | list | List of <code>{"text": str, "optional": bool}</code> entries. Details about the type, flavor, or variety (e.g., peanut, low sodium).                 |

<sub>
<b>Note:</b> For <code>product</code>, <code>brand</code>, and <code>variety</code>, entries may be <code>optional: true</code> if the remaining annotation is non-ambiguous (e.g., <code>soda</code>  for familiar brands like Coca-Cola or Pepsi).
</sub>

</details>

<details>
<summary><strong><code>CSV</code> Data Fields & Types</strong> (click to expand)</summary>

**Original VizWiz fields:**

| Field                            | Type | Description                                                                     |
| -------------------------------- | ---- | ------------------------------------------------------------------------------- |
| <code>id</code>                  | int  | VizWiz ID                                                                       |
| <code>file_name</code>           | str  | VizWiz image file                                                               |
| <code>vizwiz_url</code>          | str  | Image URL                                                                       |
| <code>text_detected</code>       | bool | OCR detected text                                                               |
| <code>unrecognizable_orig</code> | int  | Number of crowdworkers (0-5) who found the image unrecognizable.                |
| <code>blur_orig</code>           | int  | Number of crowdworkers (0-5) who identified blur.                               |
| <code>rotation_orig</code>       | int  | Number of crowdworkers (0-5) who identified rotation.                           |
| <code>framing_orig</code>        | int  | Number of crowdworkers (0-5) who identified framing issues.                     |
| <code>obstruction_orig</code>    | int  | Number of crowdworkers (0-5) who identified an obstruction blocking the image.  |
| <code>too_dark_orig</code>       | int  | Number of crowdworkers (0-5) who found the image too dark to easily identify.   |
| <code>too_bright_orig</code>     | int  | Number of crowdworkers (0-5) who found the image too bright to easily identify. |
| <code>other_orig</code>          | int  | Number of crowdworkers (0-5) who identified other issues not included above.    |

**Our annotation fields:**

| Field                                                                                                                                                                    | Type | Description                                                                            |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---- | -------------------------------------------------------------------------------------- |
| <code>image_type</code>                                                                                                                                                  | str  | <code>high-quality</code> \| <code>low-quality</code>                                  |
| <code>unrecognizable</code>, <code>blur</code>, <code>framing</code>,<br><code>obstruction</code>, <code>too_dark</code>,<br><code>too_bright</code>, <code>other</code> | bool | True if respective <code>\_orig</code> field ≥ 2                                       |
| <code>rotation</code>                                                                                                                                                    | bool | True if ≥ 45° off typical orientation, as coded by 2 researchers                       |
| <code>rounded_label</code>                                                                                                                                               | bool | If product has a rounded label, like canned goods. Annotated by researchers.           |
| <code>text_panel</code>                                                                                                                                                  | bool | If product has a text panel, like a nutrition fact label. Annotated by researchers.    |
| <code>product</code>                                                                                                                                                     | str  | The generic term for the product (e.g., cereal, soup, meal, medication).               |
| <code>brand</code>                                                                                                                                                       | str  | Any detectable brand information (e.g., Betty Crocker, Kraft, Great Value, Kellogg's). |
| <code>variety</code>                                                                                                                                                     | str  | Details about the type, flavor, or variety (e.g., peanut, low sodium).                 |

<sub>
<b>Note:</b> For <code>product</code>, <code>brand</code>, and <code>variety</code>, annotation segments are separated by semicolons
(e.g., <code>variety: diet; zero calories</code>). Segments are <i>optional</i> if the remaining annotation is non-ambiguous, indicated by parentheses (e.g., <code>(soda)</code> for familiar brands like Coca-Cola or Pepsi).
</sub>

</details>

## Dataset Browser

### Prerequisites

Install:

- [uv](https://docs.astral.sh/uv/) (package and environment manager)
- Python 3.14 (the repo pins this via `.python-version` for `uv`)

### Running the browser

The dataset browser can be run locally. Install dependencies, then start the Gradio App:

```bash
uv sync
uv run python browser.py
```

The terminal will show a local URL (e.g., `http://127.0.0.1:7860`), which you can open in your browser.

#### Creating a Public Version

For a temporary public version that persists for up to 1 week, run:

```bash
uv run python browser.py --share
```

### Development

Install dev dependencies and enable Git hooks for code formatting, which run automatically on `git commit`:

```bash
uv sync --group dev
uv run pre-commit install
```

To manually run them on all tracked files:

```bash
uv run pre-commit run --all-files
```
