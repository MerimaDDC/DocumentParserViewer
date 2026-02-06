import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from PIL import Image

sys.path.append(str(Path(__file__).parent))

from parser import parse_all_tiffs, parse_region
from visualizer import create_side_by_side_view, get_color_legend, draw_box_comparison
from utils import (
    initialize_edit_tracking, 
    update_element_type, 
    replace_element_with_reparsed, 
    get_edit_summary,
    adjust_coordinates,
    get_bounding_box_size
)


@st.cache_data
def load_and_parse_tiffs(folder_path: str):
    """Load and parse all TIFFs (cached to avoid re-parsing)"""
    return parse_all_tiffs(folder_path)


def main():
    st.set_page_config(
        page_title="TIFF Document Parser",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("Document Parser & Viewer")
    st.markdown("Parse scanned TIFF documents and visualize extracted text with bounding boxes.")
    
    st.sidebar.header("Settings")
    
    data_folder = st.sidebar.text_input("Data Folder Path", value="data")
    
    if st.sidebar.button("Load/Reload TIFFs", type="primary"):
        with st.spinner("Parsing TIFF files..."):
            results = load_and_parse_tiffs(data_folder)
            st.session_state['parse_results'] = results
            # Clear edit tracking when reloading
            if 'edit_tracking' in st.session_state:
                del st.session_state['edit_tracking']
            if results:
                st.sidebar.success(f"✓ Loaded {len(results)} TIFF files")
            else:
                st.sidebar.error("No TIFF files found")
    
    # Check if we have parsed results
    if 'parse_results' not in st.session_state or not st.session_state['parse_results']:
        st.info("Click 'Load/Reload TIFFs' in the sidebar to start")
        return
    
    results = st.session_state['parse_results']
    
    # File selection
    st.sidebar.markdown("---")
    st.sidebar.header("Select File")
    selected_file = st.sidebar.selectbox(
        "Select TIFF file to view",
        options=list(results.keys()),
        index=0
    )
    
    # Color scheme selection
    st.sidebar.markdown("---")
    st.sidebar.header("Display Options")
    color_scheme = st.sidebar.selectbox(
        "Bounding Box Colors",
        options=["Default", "High Contrast", "Pastel", "Monochrome"],
        index=0
    )
    
    show_numbers = st.sidebar.checkbox("Show Element Numbers", value=True)
    
    # Color legend
    st.sidebar.markdown("---")
    st.sidebar.header("Color Legend")
    legend = get_color_legend(color_scheme)
    for element_type, color in legend.items():
        st.sidebar.markdown(
            f'<span style="color:rgb{color}">⬤</span> {element_type}',
            unsafe_allow_html=True
        )
    
    # Main content area
    if selected_file:
        file_data = results[selected_file]
        
        # Get image dimensions
        img = Image.open(file_data['filepath'])
        img_width, img_height = img.size
        
        # Initialize edit tracking for this file if not exists
        if 'edit_tracking' not in st.session_state:
            st.session_state['edit_tracking'] = {}
        if selected_file not in st.session_state['edit_tracking']:
            st.session_state['edit_tracking'][selected_file] = initialize_edit_tracking(file_data)
        
        # Get current (possibly edited) elements
        edit_tracking = st.session_state['edit_tracking'][selected_file]
        current_elements = edit_tracking['current']
        
        # Display file info
        st.header(f"📄 {selected_file}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Elements", len(current_elements))
        
        # Count element types
        element_types = {}
        for elem in current_elements:
            elem_type = elem['type']
            element_types[elem_type] = element_types.get(elem_type, 0) + 1
        
        col2.metric("Element Types", len(element_types))
        
        # Calculate total characters from current elements
        total_chars = sum(len(elem['text']) for elem in current_elements)
        col3.metric("Characters", total_chars)
        
        # Show edit status
        if edit_tracking['edited_indices']:
            st.info(f"✏️ {len(edit_tracking['edited_indices'])} element(s) edited")
        
        st.markdown("---")
        
        # Create visualization using current (edited) elements with selected color scheme
        with st.spinner("Creating visualization..."):
            annotated_img, formatted_text = create_side_by_side_view(
                file_data['filepath'],
                current_elements,
                box_width=7,
                transparency=0.7,
                show_numbers=show_numbers,
                color_scheme=color_scheme
            )
        
        # Two column layout
        col_img, col_text = st.columns([1, 1])
        
        with col_img:
            st.subheader("🖼️ Annotated Image")
            st.image(annotated_img, use_container_width=True)
        
        with col_text:
            st.subheader("📝 Extracted Text")
            st.text_area(
                "Extracted content",
                value=formatted_text,
                height=600,
                label_visibility="collapsed"
            )
        
        # Edit Elements Section
        st.markdown("---")
        with st.expander("Edit Elements", expanded=False):
            st.markdown("### Edit Element Types or Re-parse Regions")
            
            # Create dataframe for editing
            edit_data = []
            for idx, elem in enumerate(current_elements):
                edit_data.append({
                    'Number': idx + 1,
                    'Type': elem['type'],
                    'Text Preview': elem['text'][:100] + '...' if len(elem['text']) > 100 else elem['text'],
                    'Has Coordinates': elem['coordinates'] is not None,
                    'Edited': idx in edit_tracking['edited_indices']
                })
            
            df = pd.DataFrame(edit_data)
            st.dataframe(df, use_container_width=True, height=300)
            
            col_edit1, col_edit2 = st.columns(2)
            
            with col_edit1:
                st.markdown("#### 🏷️ Relabel Element Type")
                element_to_edit = st.number_input(
                    "Element Number",
                    min_value=1,
                    max_value=len(current_elements),
                    value=1,
                    key="relabel_element"
                )
                
                new_type = st.selectbox(
                    "New Element Type",
                    options=list(legend.keys()),
                    key="new_type"
                )
                
                if st.button("Update Type", key="update_type_btn"):
                    idx = element_to_edit - 1
                    edit_tracking['current'] = update_element_type(
                        edit_tracking['current'],
                        idx,
                        new_type
                    )
                    edit_tracking['edited_indices'].add(idx)
                    st.success(f"✓ Updated element {element_to_edit} type to {new_type}")
                    st.rerun()
            
            with col_edit2:
                st.markdown("#### 🔍 Re-parse Region")
                element_to_reparse = st.number_input(
                    "Element Number",
                    min_value=1,
                    max_value=len(current_elements),
                    value=1,
                    key="reparse_element"
                )
                
                idx = element_to_reparse - 1
                elem = current_elements[idx]
                
                if elem['coordinates']:
                    # Show current box info
                    width, height = get_bounding_box_size(elem['coordinates'])
                    st.info(f"Current box: {width}x{height}px\n\nText: {elem['text'][:100]}...")
                    
                    # Adjustment inputs
                    st.markdown("**Adjust Bounding Box:**")
                    st.caption("Enter pixels to expand (positive) or contract (negative)")
                    
                    col_adj1, col_adj2 = st.columns(2)
                    
                    with col_adj1:
                        left_adjust = st.number_input(
                            "Left ←",
                            min_value=-2000,
                            max_value=2000,
                            value=0,
                            step=10,
                            key="left_adj"
                        )
                        right_adjust = st.number_input(
                            "Right →",
                            min_value=-2000,
                            max_value=2000,
                            value=0,
                            step=10,
                            key="right_adj"
                        )
                    
                    with col_adj2:
                        top_adjust = st.number_input(
                            "Top ↑",
                            min_value=-2000,
                            max_value=2000,
                            value=0,
                            step=10,
                            key="top_adj"
                        )
                        bottom_adjust = st.number_input(
                            "Bottom ↓",
                            min_value=-2000,
                            max_value=2000,
                            value=0,
                            step=10,
                            key="bottom_adj"
                        )
                    
                    # Calculate adjusted coordinates
                    adjusted_coords = adjust_coordinates(
                        elem['coordinates'],
                        left_adjust,
                        right_adjust,
                        top_adjust,
                        bottom_adjust,
                        img_width,
                        img_height
                    )
                    new_width, new_height = get_bounding_box_size(adjusted_coords)
                    
                    # Show preview if adjustments are made
                    if (left_adjust != 0 or right_adjust != 0 or 
                        top_adjust != 0 or bottom_adjust != 0):
                        st.success(f"New box size: {new_width}x{new_height}px")
                        
                        st.markdown("**Preview:**")
                        st.caption("Original box in red | Adjusted box in green")
                        
                        preview_img = draw_box_comparison(
                            file_data['filepath'],
                            elem['coordinates'],
                            adjusted_coords,
                            box_width=7
                        )
                        st.image(preview_img, use_container_width=True)
                    
                    if st.button("Re-parse with Adjusted Region", key="reparse_btn"):
                        with st.spinner("Re-parsing region..."):
                            try:
                                new_text = parse_region(
                                    file_data['filepath'],
                                    adjusted_coords
                                )
                                edit_tracking['current'] = replace_element_with_reparsed(
                                    edit_tracking['current'],
                                    idx,
                                    new_text
                                )
                                # Also update coordinates to the adjusted ones
                                edit_tracking['current'][idx]['coordinates'] = adjusted_coords
                                edit_tracking['edited_indices'].add(idx)
                                st.success(f"Re-parsed element {element_to_reparse}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error re-parsing: {e}")
                else:
                    st.warning("This element has no coordinates and cannot be re-parsed")
            
            # Edit summary and reset
            st.markdown("---")
            col_summary1, col_summary2 = st.columns(2)
            
            with col_summary1:
                if edit_tracking['edited_indices']:
                    st.markdown("#### Edit Summary")
                    summary = get_edit_summary(edit_tracking)
                    st.text(summary)
            
            with col_summary2:
                if st.button("Reset All Edits", type="secondary"):
                    st.session_state['edit_tracking'][selected_file] = initialize_edit_tracking(file_data)
                    st.success("✓ All edits reset")
                    st.rerun()
        
        # Element type breakdown
        st.markdown("---")
        st.subheader("Element Type Breakdown")
        
        breakdown_cols = st.columns(min(len(element_types), 4))
        for idx, (elem_type, count) in enumerate(element_types.items()):
            col_idx = idx % len(breakdown_cols)
            breakdown_cols[col_idx].metric(elem_type, count)
        
        # Download options
        st.markdown("---")
        st.subheader("Download")
        
        col_download1, col_download2 = st.columns(2)
        
        # Regenerate full text from current elements
        current_full_text = '\n\n'.join([elem['text'] for elem in current_elements])
        
        with col_download1:
            # Download extracted text
            st.download_button(
                label="Download Text",
                data=current_full_text,
                file_name=f"{Path(selected_file).stem}_extracted.txt",
                mime="text/plain"
            )
        
        with col_download2:
            # Convert image to bytes for download
            from io import BytesIO
            buf = BytesIO()
            annotated_img.save(buf, format='PNG')
            st.download_button(
                label="Download Annotated Image",
                data=buf.getvalue(),
                file_name=f"{Path(selected_file).stem}_annotated.png",
                mime="image/png"
            )


if __name__ == "__main__":
    main()