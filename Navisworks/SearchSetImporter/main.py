# --- 0. IMPORT LIBRARIES ---
import xml.etree.ElementTree as ET # Library to create XML structure
from xml.dom import minidom           # Library to make XML look pretty (indentation)
import os                             # Library for file and folder operations
import sys                            # Library for system-specific parameters
import csv                            # Library to read CSV files
from tkinter import filedialog, Tk, messagebox, Button, Label # UI Components

# --- 1. MAPPING DATA ---
# This section connects our script to the 'mapping.py' file which translates 
# user-friendly names to Navisworks internal IDs.
try:
    from mapping import get_internal_category, get_internal_property, MEP_TYPE_MAP
except ImportError:
    # If the student forgot mapping.py, this fallback prevents the script from crashing.
    def get_internal_category(val): return val
    def get_internal_property(val, context=""): return val
    MEP_TYPE_MAP = {}

# --- 2. CONVERSION LOGIC ---

def convert_to_feet(value, from_unit, value_type):
    """
    Navisworks internally uses 'Decimal Feet' for its search engine.
    This function converts meters, millimeters, or inches into feet.
    """
    # We only convert numeric types (linear distances, areas, volumes, etc.)
    if value_type not in ['linear', 'area', 'volume', 'float', 'int32']:
        return value
    
    try:
        num_val = float(value)
    except (ValueError, TypeError):
        return value # If it's not a number, don't touch it
    
    # Mathematical conversion factors
    linear_factors = {
        'feet': 1.0,
        'meter': 1.0 / 0.3048,
        'millimeter': 0.001 / 0.3048,
        'inch': 1.0 / 12.0,
    }
    
    from_unit_lower = from_unit.lower().strip()
    if from_unit_lower in linear_factors:
        factor = linear_factors[from_unit_lower]
        
        # Area requires factor squared, Volume requires factor cubed
        if value_type == 'linear':
            converted = num_val * factor
        elif value_type == 'area':
            converted = num_val * (factor ** 2)
        elif value_type == 'volume':
            converted = num_val * (factor ** 3)
        else:
            converted = num_val * factor # Default to linear (float)
        
        # Round the result to 6 decimal places for cleanliness
        if value_type == 'int32':
            return str(int(round(converted)))
        else:
            return f"{converted:.6f}".rstrip('0').rstrip('.')
    
    return value

def generate_xml(rows, out_file):
    """
    This is the engine of the script. It takes the list of rules from Excel
    and translates them into a Navisworks '.xml' file.
    """
    
    # 1. Read General Settings from the first row of Excel
    navis_version = '2024'  # Default version
    data_unit = 'meter'     # Default unit
    if rows and len(rows) > 0:
        first_row = rows[0]
        # We clean the header name to find the version/unit columns regardless of spacing
        temp_dict = {str(k).lower().replace(" ", ""): v for k, v in first_row.items()}
        navis_version = str(temp_dict.get('navisworksversion', '2024')).strip() or '2024'
        data_unit = str(temp_dict.get('dataunit', 'meter')).strip() or 'meter'

    # 2. Setup the XML Root (The 'envelope' that holds everything)
    root = ET.Element("exchange", {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation": "http://download.autodesk.com/us/navisworks/schemas/nw-exchange-12.0.xsd",
        "units": "ft", # Navisworks 'Exchange' schema requires feet
        "filename": ""
    })
    selection_sets = ET.SubElement(root, "selectionsets")

    # 3. Loop through every row in the Excel spreadsheet
    for row in rows:
        folder_path = str(row.get('FolderPath', '') or '').strip()
        set_name = str(row.get('SetName', 'New Set') or 'New Set')
        cat_raw = str(row.get('Category', 'Item') or 'Item')
        prop_raw = str(row.get('Property', 'Name') or 'Name')
        cond = str(row.get('Condition', 'equals') or 'equals').lower()
        val = str(row.get('Value', '') or '')
        val_type_request = str(row.get('Value Type', 'Auto') or 'Auto').strip()

        # Place the Search Set into the correct folder structure
        parent = selection_sets
        if folder_path:
            for folder in folder_path.split('/'):
                found = False
                for child in parent:
                    if child.tag == 'viewfolder' and child.get('name') == folder:
                        parent = child
                        found = True
                        break
                if not found:
                    parent = ET.SubElement(parent, "viewfolder", name=folder)

        # Create the 'Selection Set' container
        s_set = ET.SubElement(parent, "selectionset", name=set_name)
        find_spec = ET.SubElement(s_set, "findspec", mode="all", disjoint="0")
        conds_node = ET.SubElement(find_spec, "conditions")
        
        # Determine the Data Type and if we need to convert units
        # Note: Navisworks 2025+ handles data units more strictly (feet internally)
        needs_conversion = True 
        
        # Try to find if this property is a known MEP/measurement type
        xml_type = "wstring" # Default to 'String' (Text)
        xml_flags = "10"
        
        known_type = None
        for key, mapping_val in MEP_TYPE_MAP.items():
            if key.lower() in prop_raw.lower():
                known_type, is_numeric = mapping_val
                xml_type = known_type
                xml_flags = "0" if is_numeric else "10"
                break
        
        # If not known, guess based on the 'Value Type' column in Excel
        if not known_type:
            if val_type_request == "Integer":
                xml_type, xml_flags = "int32", "0"
            elif val_type_request == "Number with Decimal":
                xml_type, xml_flags = "float", "0"
            elif val_type_request == "Text":
                xml_type, xml_flags = "wstring", "10"
            else:
                # Automatic detection if empty
                val_upper = str(val).upper()
                if val_upper in ["YES", "NO", "TRUE", "FALSE"]:
                    xml_type, xml_flags = "bool", "0"
                    val = "true" if val_upper in ["YES", "TRUE"] else "false"
                elif val.replace('.','',1).isdigit():
                    xml_type, xml_flags = "float", "0"
                else:
                    xml_type, xml_flags = "wstring", "10"

        # Apply Unit Conversion for dimensions
        dimensional_props = ['elevation', 'height', 'width', 'length', 'thickness', 'offset', 'diameter']
        is_dim = any(d in prop_raw.lower() for d in dimensional_props) or (xml_type in ['linear', 'area', 'volume'])
        
        final_val = val
        if needs_conversion and is_dim and val:
            conv_type = 'linear' if xml_type == 'float' else xml_type
            final_val = convert_to_feet(val, data_unit, conv_type)

        # Construct the 'Condition' XML node (This is what you see in the Find Items window)
        if cond in ['defined', 'undefined']:
            # "attrib" is backward compatible with 2023/2024, "prop" is for 2025+
            # We use "attrib" here as it works for both.
            xml_test = "attrib" if cond == 'defined' else "no_prop"
            c_node = ET.SubElement(conds_node, "condition", test=xml_test, flags="0")
        else:
            c_node = ET.SubElement(conds_node, "condition", test=cond, flags=xml_flags)
        
        # Add the 'Category' (Tab name)
        cat_internal = get_internal_category(cat_raw)
        cat_el = ET.SubElement(c_node, "category")
        ET.SubElement(cat_el, "name", internal=cat_internal).text = cat_raw
        
        # Add the 'Property' (Parameter name)
        prop_internal = get_internal_property(prop_raw, category_context=cat_raw)
        prop_el = ET.SubElement(c_node, "property")
        ET.SubElement(prop_el, "name", internal=prop_internal).text = prop_raw
        
        # Add the 'Value' (The search term)
        v_node = ET.SubElement(c_node, "value")
        
        if cond in ['defined', 'undefined']:
            # For existence checks, the data tag should be empty with no type
            ET.SubElement(v_node, "data") 
        elif xml_type == "wstring" and ", #" in final_val:
            # SPECIAL TREATMENT: Handle Revit object references (e.g., Phases, Levels)
            d_node = ET.SubElement(v_node, "data", type="name")
            ET.SubElement(d_node, "name", internal="LcRevitElement").text = final_val
        else:
            ET.SubElement(v_node, "data", type=xml_type).text = final_val
        
        # Navisworks requirement: Add a locator tag
        ET.SubElement(find_spec, "locator").text = "/"

    # 4. Save the XML string to a file
    xml_str = minidom.parseString(ET.tostring(root, 'utf-8')).toprettyxml(indent="  ")
    with open(out_file, "w", encoding="utf-8") as f: 
        f.write(xml_str)

def read_excel_or_csv(file_path):
    """
    This function reads your Excel (.xlsx) or CSV file.
    It cleans up the data so that tiny typos (like extra spaces) don't break the code.
    """
    data = []
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == '.csv':
            # Handling comma-separated values
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                headers = [h.strip() if h else "" for h in (reader.fieldnames or [])]
                for row in reader:
                    cleaned_row = {headers[i]: str(v).strip() for i, (k, v) in enumerate(row.items()) if i < len(headers)}
                    data.append(cleaned_row)
        else:
            # Handling Excel files (requires 'openpyxl' library)
            import openpyxl
            wb = openpyxl.load_workbook(file_path, data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            if not rows: return []

            # Clean the header names (First Row)
            headers = [str(h).strip() if h is not None else f"_gap_{i}" for i, h in enumerate(rows[0])]
            
            # Read every data row (Second row onwards)
            for row_vals in rows[1:]:
                if not any(v is not None for v in row_vals): continue # Skip empty rows
                row_dict = {}
                for i, h in enumerate(headers):
                    if i < len(row_vals):
                        val = row_vals[i]
                        row_dict[h] = str(val).strip() if val is not None else ""
                data.append(row_dict)
                
    except ImportError:
        # Instruction for the viewer if they forgot to install openpyxl
        raise Exception("Missing 'openpyxl'. Run this command: pip install openpyxl")
    except Exception as e:
        raise Exception(f"File Error: {e}")
    
    return data

# --- 3. UI WINDOW LOGIC ---

def process_file():
    """Triggered when the user clicks the green button."""
    # 1. Ask the user for a file
    file_path = filedialog.askopenfilename(
        title="Select Excel/CSV File",
        filetypes=[("Excel Files", "*.xlsx"), ("CSV Files", "*.csv")]
    )
    if not file_path:
        return # User cancelled

    try:
        # 2. Read the data
        data = read_excel_or_csv(file_path)
        if not data:
            messagebox.showwarning("Empty", "No data found in file.")
            return

        # 3. Choose the output path (Same folder, new name)
        output_path = os.path.splitext(file_path)[0] + "_SearchSets.xml"
        
        # 4. Generate the XML
        generate_xml(data, output_path)
        
        # 5. Show success message
        messagebox.showinfo("Success", f"Converted!\nFile: {os.path.basename(output_path)}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")

# --- 4. START THE APPLICATION ---

if __name__ == "__main__":
    # Initialize the window
    root = Tk()
    root.title("Navisworks Search Set Importer (Beginner)")
    root.geometry("400x230") # Set the initial size
    
    # Add a nice header
    Label(root, text="Navisworks Automator", font=("Arial", 16, "bold")).pack(pady=20)
    
    # Add an instruction label
    Label(root, text="Select an Excel or CSV template to convert.").pack()
    
    # Add the big action button
    Button(root, text="Select File & Convert", command=process_file, 
           bg="#28A745", fg="white", font=("Arial", 12, "bold"), 
           padx=20, pady=10).pack(pady=20)
    
    # Keep the window running
    root.mainloop()
