# Document Parser and Viewer

An interactive web application for parsing scanned documents using OCR, with visual annotation and editing capabilities.

This is just a small-scale project with many further improvements. The idea is to aid in systematic large-scale manual OCR-processing by immediate visualization of the results, and possibility of quickly adjusting errors. This is showcased using selected TIFF-files from alvin-portal.org under public domain.

Possible improvements include expanding the interactive component with drag-and-drop functionalities, utilizing an LLM for language checks, allowing for further customization depending on specific needs, e.g. file formats possible to process, what type of structure the data output should have, etc. This project could also be extended to an evaluation tool: changing the OCR technique and logging edits, then visualizing how edit frequency and type depend on OCR technique, for instance.

## Features

- **Parse Documents**: Extract text from scanned TIFF documents using the Unstructured library
- **Visual Annotation**: View documents with color-coded bounding boxes for different element types
- **Interactive Editing**: Adjust bounding boxes and re-parse specific regions
- **Export Results**: Download extracted text, structured data and annotated images

## Demo

[Live Demo on Streamlit Cloud](https://mddc-documentparserviewer.streamlit.app/)

## Installation

### Prerequisites

- Python 3.11+
- Tesseract OCR

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ParsePDFs.git
   cd ParsePDFs
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Add your TIFF files to the `data/` folder

4. Run the application:
   ```bash
   streamlit run main.py
   ```

## Usage

1. **Load Documents**: Click "Load/Reload TIFFs" in the sidebar
2. **Select a File**: Choose a TIFF from the dropdown
3. **View Results**: See annotated image and extracted text side-by-side
4. **Edit Elements**: 
   - Expand "Edit Elements" section
   - Relabel element types
   - Adjust bounding boxes and re-parse regions
5. **Download**: Export text or annotated images

## Project Structure

```
ParsePDFs/
├── main.py                 # Entry point
├── src/
│   ├── interactive_ui.py   # Streamlit UI
│   ├── parser.py           # OCR and document parsing
│   ├── visualizer.py       # Bounding box visualization
│   └── utils.py            # Helper functions
├── data/                   # TIFF files (public domain documents)
├── output/                 # Generated files
└── requirements.txt        # Python dependencies
```

## Color Legend

- 🔴 **Title**: Document titles
- 🟢 **NarrativeText**: Body paragraphs
- 🔵 **ListItem**: Bulleted/numbered lists
- 🟠 **Table**: Tabular data
- 🟣 **Image**: Embedded images
- 🟡 **Header**: Page headers
- 🔷 **Footer**: Page footers

## Technologies Used

- [Streamlit](https://streamlit.io/) - Web framework
- [Unstructured](https://unstructured.io/) - Document parsing
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR

## Data

All documents in the `data/` folder are in the public domain, retrieved from alvin-portal.org.

## Acknowledgments

Built using open-source tools.