from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List, Tuple
from pathlib import Path
import numpy as np

COLOR_SCHEMES = {
    'Default': {
        'Title': (255, 0, 0),        # Red
        'NarrativeText': (0, 255, 0), # Green
        'ListItem': (0, 0, 255),      # Blue
        'Table': (255, 165, 0),       # Orange
        'Image': (255, 0, 255),       # Magenta
        'Header': (255, 255, 0),      # Yellow
        'Footer': (0, 255, 255),      # Cyan
        'PageBreak': (128, 128, 128), # Gray
        'UncategorizedText': (128, 0, 128) # Purple
    },
    'High Contrast': {
        'Title': (255, 0, 0),        # Bright Red
        'NarrativeText': (0, 255, 0), # Bright Green
        'ListItem': (0, 0, 255),      # Bright Blue
        'Table': (255, 255, 0),       # Yellow
        'Image': (255, 0, 255),       # Magenta
        'Header': (0, 255, 255),      # Cyan
        'Footer': (255, 128, 0),      # Orange
        'PageBreak': (255, 255, 255), # White
        'UncategorizedText': (128, 255, 128) # Light Green
    },
    'Pastel': {
        'Title': (255, 182, 193),     # Light Pink
        'NarrativeText': (173, 216, 230), # Light Blue
        'ListItem': (221, 160, 221),  # Plum
        'Table': (255, 218, 185),     # Peach
        'Image': (216, 191, 216),     # Thistle
        'Header': (255, 250, 205),    # Lemon Chiffon
        'Footer': (176, 224, 230),    # Powder Blue
        'PageBreak': (211, 211, 211), # Light Gray
        'UncategorizedText': (255, 228, 196) # Bisque
    },
    'Monochrome': {
        'Title': (255, 255, 255),     # White
        'NarrativeText': (220, 220, 220), # Very Light Gray
        'ListItem': (180, 180, 180),  # Light Gray
        'Table': (140, 140, 140),     # Gray
        'Image': (100, 100, 100),     # Dark Gray
        'Header': (255, 255, 255),    # White
        'Footer': (200, 200, 200),    # Light Gray
        'PageBreak': (160, 160, 160), # Medium Gray
        'UncategorizedText': (120, 120, 120) # Gray
    }
}

DEFAULT_COLOR = (255, 100, 100)  # Light red for unknown types


def get_color_scheme(scheme_name: str = 'Default') -> Dict[str, Tuple[int, int, int]]:
    """
    Get a color scheme by name.
    
    Args:
        scheme_name: Name of the color scheme
        
    Returns:
        Dictionary mapping element types to RGB colors
    """
    return COLOR_SCHEMES.get(scheme_name, COLOR_SCHEMES['Default']).copy()


def draw_bounding_boxes(
    image_path: str,
    elements: List[Dict[str, Any]],
    box_width: int = 7,
    transparency: float = 0.7,
    show_numbers: bool = True,
    color_scheme: str = 'Default'
) -> Image.Image:
    """
    Draw bounding boxes on an image for detected text elements.
    
    Args:
        image_path: Path to the image file
        elements: List of element dictionaries with 'type', 'text', and 'coordinates'
        box_width: Thickness of the bounding box lines
        transparency: Opacity of the boxes (0.0 = transparent, 1.0 = opaque)
        show_numbers: Whether to show element numbers on boxes
        color_scheme: Name of the color scheme to use
        
    Returns:
        PIL Image with bounding boxes drawn
    """
    # Load image
    img = Image.open(image_path)
    
    # Get color scheme
    colors = get_color_scheme(color_scheme)
    
    # Create a semi-transparent overlay
    overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Try to load a font for numbers
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=20)
    except:
        font = ImageFont.load_default()
    
    # Draw boxes for each element
    for idx, element in enumerate(elements, 1):
        if element['coordinates'] is None:
            continue
        
        coords = element['coordinates']
        element_type = element['type']
        
        # Get color for this element type
        color = colors.get(element_type, DEFAULT_COLOR)
        
        # Calculate transparency
        alpha = int(255 * transparency)
        color_with_alpha = color + (alpha,)
        
        # Draw polygon (bounding box)
        draw.polygon(coords, outline=color_with_alpha, width=box_width)
        
        # Draw element number if requested
        if show_numbers and coords:
            # Position number at top-left of bounding box
            x, y = coords[0]
            # Draw background for number
            text = str(idx)
            bbox = draw.textbbox((x, y), text, font=font)
            draw.rectangle(bbox, fill=color_with_alpha)
            draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    # Convert original image to RGBA and composite
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    result = Image.alpha_composite(img, overlay)
    
    # Convert back to RGB for display
    return result.convert('RGB')


def draw_box_comparison(
    image_path: str,
    original_coords: List[Tuple[float, float]],
    adjusted_coords: List[Tuple[float, float]],
    box_width: int = 7
) -> Image.Image:
    """
    Draw both original and adjusted bounding boxes on the full image for comparison.
    
    Args:
        image_path: Path to the image file
        original_coords: Original bounding box coordinates
        adjusted_coords: Adjusted bounding box coordinates
        box_width: Thickness of the bounding box lines
        
    Returns:
        PIL Image showing both boxes overlaid
    """
    # Load image
    img = Image.open(image_path)
    
    # Create overlay
    overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Draw original box in red (semi-transparent)
    draw.polygon(original_coords, outline=(255, 0, 0, 180), width=box_width)
    
    # Draw adjusted box in green (semi-transparent)
    draw.polygon(adjusted_coords, outline=(0, 255, 0, 180), width=box_width + 1)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=16)
    except:
        font = ImageFont.load_default()
    
    # Label original box
    orig_x, orig_y = original_coords[0]
    draw.text((orig_x, orig_y - 20), "Original", fill=(255, 0, 0, 255), font=font)
    
    # Label adjusted box
    adj_x, adj_y = adjusted_coords[0]
    draw.text((adj_x, adj_y - 20), "Adjusted", fill=(0, 255, 0, 255), font=font)
    
    # Composite
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    result = Image.alpha_composite(img, overlay)
    
    return result.convert('RGB')


def create_side_by_side_view(
    image_path: str,
    elements: List[Dict[str, Any]],
    box_width: int = 7,
    transparency: float = 0.7,
    show_numbers: bool = True,
    color_scheme: str = 'Default'
) -> Tuple[Image.Image, str]:
    """
    Create an annotated image and formatted text for side-by-side display.
    
    Args:
        image_path: Path to the image file
        elements: List of element dictionaries
        box_width: Thickness of bounding boxes
        transparency: Opacity of boxes
        show_numbers: Whether to number the boxes
        color_scheme: Name of the color scheme to use
        
    Returns:
        Tuple of (annotated_image, formatted_text)
    """
    # Get annotated image
    annotated_img = draw_bounding_boxes(
        image_path, 
        elements, 
        box_width, 
        transparency, 
        show_numbers,
        color_scheme
    )
    
    # Format text with numbers
    text_parts = []
    for idx, element in enumerate(elements, 1):
        if show_numbers:
            text_parts.append(f"[{idx}] {element['type']}")
        else:
            text_parts.append(f"{element['type']}")
        text_parts.append(element['text'])
        text_parts.append("-" * 50)
    
    formatted_text = "\n".join(text_parts)
    
    return annotated_img, formatted_text


def save_annotated_image(
    image: Image.Image,
    original_filename: str,
    output_folder: str = "output/annotated_images"
) -> str:
    """
    Save an annotated image to the output folder.
    
    Args:
        image: PIL Image to save
        original_filename: Original filename (used to generate output name)
        output_folder: Folder to save the annotated image
        
    Returns:
        Path to the saved image
    """
    # Create output folder if it doesn't exist
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    # Generate output filename
    name = Path(original_filename).stem
    output_path = Path(output_folder) / f"{name}_annotated.png"
    
    # Save image
    image.save(output_path)
    
    return str(output_path)


def get_color_legend(color_scheme: str = 'Default') -> Dict[str, Tuple[int, int, int]]:
    """
    Get the color legend for element types based on selected scheme.
    
    Args:
        color_scheme: Name of the color scheme
        
    Returns:
        Dictionary mapping element types to RGB colors
    """
    return get_color_scheme(color_scheme)