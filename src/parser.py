import os
from pathlib import Path
from typing import List, Dict, Any
from unstructured.partition.image import partition_image


def scan_data_folder(folder_path: str) -> List[str]:
    """
    Scan the data folder for all TIFF files.
    
    Args:
        folder_path: Path to the folder containing TIFF files
        
    Returns:
        List of file paths to TIFF files
    """
    tiff_files = []
    folder = Path(folder_path)
    
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    # Find all .tiff and .tif files
    for ext in ['*.tiff', '*.tif', '*.TIFF', '*.TIF']:
        tiff_files.extend(folder.glob(ext))
    
    return [str(f) for f in sorted(tiff_files)]


def parse_single_tiff(file_path: str) -> Dict[str, Any]:
    """
    Parse a single TIFF file and extract text with coordinates.
    
    Args:
        file_path: Path to the TIFF file
        
    Returns:
        Dictionary containing:
            - filename: Name of the file
            - filepath: Full path to the file
            - elements: List of extracted elements with text and coordinates
            - full_text: All extracted text concatenated
    """
    elements = partition_image(
        filename=file_path,
        infer_table_structure=True
    )
    
    # Structure the results
    parsed_elements = []
    full_text_parts = []
    
    for element in elements:
        element_data = {
            'type': element.category,
            'text': str(element),
            'coordinates': None
        }
        
        # Extract coordinates if available
        if hasattr(element, 'metadata') and element.metadata.coordinates:
            points = element.metadata.coordinates.points
            element_data['coordinates'] = [(p[0], p[1]) for p in points]
        
        parsed_elements.append(element_data)
        full_text_parts.append(str(element))
    
    return {
        'filename': Path(file_path).name,
        'filepath': file_path,
        'elements': parsed_elements,
        'full_text': '\n\n'.join(full_text_parts)
    }


def parse_all_tiffs(folder_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse all TIFF files in the specified folder.
    
    Args:
        folder_path: Path to the folder containing TIFF files
        
    Returns:
        Dictionary mapping filenames to their parse results
    """
    tiff_files = scan_data_folder(folder_path)
    
    if not tiff_files:
        print(f"No TIFF files found in {folder_path}")
        return {}
    
    results = {}
    
    for file_path in tiff_files:
        print(f"Parsing: {Path(file_path).name}")
        try:
            parsed_data = parse_single_tiff(file_path)
            results[parsed_data['filename']] = parsed_data
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            continue
    
    return results


def parse_region(image_path: str, coordinates: List[tuple]) -> str:
    """
    Parse a specific region of an image marked by the user.
    
    Args:
        image_path: Path to the image file
        coordinates: List of (x, y) tuples defining the region boundary
        
    Returns:
        Extracted text from the specified region
    """
    from PIL import Image
    import tempfile
    
    # Load image
    img = Image.open(image_path)
    
    # Get bounding box from coordinates
    xs = [coord[0] for coord in coordinates]
    ys = [coord[1] for coord in coordinates]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    
    # Crop to the specified region
    cropped = img.crop(bbox)
    
    # Save temporarily and parse
    with tempfile.NamedTemporaryFile(suffix='.tiff', delete=False) as tmp:
        cropped.save(tmp.name)
        tmp_path = tmp.name
    
    try:
        elements = partition_image(filename=tmp_path)
        text = '\n'.join([str(el) for el in elements])
    finally:
        os.unlink(tmp_path)
    
    return text