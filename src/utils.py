from typing import Dict, Any, List, Tuple
import copy


def initialize_edit_tracking(file_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Initialize edit tracking for a file's elements.
    
    Args:
        file_data: Original parsed file data
        
    Returns:
        Dictionary with original and working copy of elements
    """
    return {
        'original': copy.deepcopy(file_data['elements']),
        'current': copy.deepcopy(file_data['elements']),
        'edited_indices': set()
    }


def update_element_type(
    elements: List[Dict[str, Any]], 
    element_index: int, 
    new_type: str
) -> List[Dict[str, Any]]:
    """
    Update the type of a specific element.
    
    Args:
        elements: List of element dictionaries
        element_index: Index of element to update (0-based)
        new_type: New element type
        
    Returns:
        Updated list of elements
    """
    if 0 <= element_index < len(elements):
        elements[element_index]['type'] = new_type
    return elements


def replace_element_with_reparsed(
    elements: List[Dict[str, Any]],
    element_index: int,
    new_text: str
) -> List[Dict[str, Any]]:
    """
    Replace an element's text with newly parsed content.
    
    Args:
        elements: List of element dictionaries
        element_index: Index of element to replace
        new_text: New text from re-parsing
        
    Returns:
        Updated list of elements
    """
    if 0 <= element_index < len(elements):
        elements[element_index]['text'] = new_text
    return elements


def adjust_coordinates(
    coordinates: List[Tuple[float, float]],
    left_adjust: int,
    right_adjust: int,
    top_adjust: int,
    bottom_adjust: int,
    image_width: int,
    image_height: int
) -> List[Tuple[float, float]]:
    """
    Adjust bounding box coordinates by expanding/contracting margins.
    
    Args:
        coordinates: Original coordinates [(x, y), ...]
        left_adjust: Pixels to expand left (negative to contract)
        right_adjust: Pixels to expand right (negative to contract)
        top_adjust: Pixels to expand top (negative to contract)
        bottom_adjust: Pixels to expand bottom (negative to contract)
        image_width: Width of the image for boundary checking
        image_height: Height of the image for boundary checking
        
    Returns:
        Adjusted coordinates
    """
    # Get bounding box from coordinates
    xs = [coord[0] for coord in coordinates]
    ys = [coord[1] for coord in coordinates]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    # Apply adjustments
    new_min_x = max(0, min_x - left_adjust)
    new_max_x = min(image_width, max_x + right_adjust)
    new_min_y = max(0, min_y - top_adjust)
    new_max_y = min(image_height, max_y + bottom_adjust)
    
    # Return new rectangular coordinates
    return [
        (new_min_x, new_min_y),  # Top-left
        (new_max_x, new_min_y),  # Top-right
        (new_max_x, new_max_y),  # Bottom-right
        (new_min_x, new_max_y)   # Bottom-left
    ]


def get_bounding_box_size(coordinates: List[Tuple[float, float]]) -> Tuple[int, int]:
    """
    Get width and height of a bounding box.
    
    Args:
        coordinates: List of (x, y) coordinate tuples
        
    Returns:
        Tuple of (width, height)
    """
    xs = [coord[0] for coord in coordinates]
    ys = [coord[1] for coord in coordinates]
    
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    
    return int(width), int(height)


def get_edit_summary(edit_tracking: Dict[str, Any]) -> str:
    """
    Generate a summary of edits made.
    
    Args:
        edit_tracking: Edit tracking dictionary
        
    Returns:
        Formatted string summary
    """
    if not edit_tracking['edited_indices']:
        return "No edits made"
    
    summary_parts = []
    for idx in sorted(edit_tracking['edited_indices']):
        original = edit_tracking['original'][idx]
        current = edit_tracking['current'][idx]
        
        changes = []
        if original['type'] != current['type']:
            changes.append(f"Type: {original['type']} → {current['type']}")
        if original['text'] != current['text']:
            changes.append(f"Text modified")
        
        if changes:
            summary_parts.append(f"Element {idx + 1}: {', '.join(changes)}")
    
    return "\n".join(summary_parts)