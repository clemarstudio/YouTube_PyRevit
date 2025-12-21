import xml.etree.ElementTree as ET
import os
import sys
import csv
from collections import defaultdict
from tkinter import filedialog, Tk, messagebox

# --- ⬇️ DUAL MODE SUPPORT: Drag-and-Drop OR File Dialog ⬇️ ---
# Create root window (hidden) for dialogs
root = Tk()
root.withdraw()  # Hide the main window
root.attributes('-topmost', True)  # Bring dialogs to front

xml_path = None

# Mode 1: Drag-and-Drop (if file is passed as argument)
if len(sys.argv) >= 2:
    xml_path = sys.argv[1]
else:
    # Mode 2: File Dialog (if no arguments, open file picker)
    try:
        xml_path = filedialog.askopenfilename(
            title="Select Navisworks XML File",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
    except Exception as e:
        messagebox.showerror("Error", f"GUI Error: {e}")
        root.destroy()
        sys.exit(1)

# Validate selection
if not xml_path or xml_path == "":
    root.destroy()
    sys.exit(0)  # User cancelled, exit silently

# Validate that the file exists and is an XML file
if not os.path.exists(xml_path):
    messagebox.showerror("Error", f"File not found:\n{xml_path}")
    root.destroy()
    sys.exit(1)

if not xml_path.lower().endswith('.xml'):
    messagebox.showerror("Error", f"File must be an XML file:\n{xml_path}")
    root.destroy()
    sys.exit(1)

# Generate output CSV file in the same directory as the XML file
xml_dir = os.path.dirname(xml_path)
xml_basename = os.path.basename(xml_path)
xml_name_without_ext = os.path.splitext(xml_basename)[0]
output_filename = f"{xml_name_without_ext}_Final.csv"
output_path = os.path.join(xml_dir, output_filename)
# ---------------------------------------------

# Configuration
critical_threshold = 0.050
moderate_threshold = 0.010

def get_dashboard_category(revit_category, item_name):
    """
    Groups raw Revit Categories into clean Dashboard Groups.
    """
    cat = str(revit_category).upper()
    name = str(item_name).upper()
    
    # 1. Direct Revit Category Mapping (High Confidence)
    if "DUCT" in cat: return "Ducts"
    if "PIPE" in cat or "PIPING" in cat: return "Pipes"
    if "CABLE TRAY" in cat: return "Cable Trays"
    if "CONDUIT" in cat: return "Conduits"
    if "COLUMN" in cat: return "Columns"
    if "FRAMING" in cat: return "Beams"
    if "WALL" in cat: return "Walls"
    if "FLOOR" in cat: return "Slabs"
    if "SPRINKLER" in cat: return "Sprinklers"
    
    # 2. Fallback: Name-based guessing for "Equipment" or "Fittings"
    if "EQUIPMENT" in cat:
        if "MECH" in cat: return "Mech Equipment"
        if "ELEC" in cat: return "Elec Equipment"
        return "Equipment"
        
    if "FITTING" in cat:
        if "DUCT" in name: return "Duct Fittings"
        if "PIPE" in name: return "Pipe Fittings"
        return "Fittings"

    return cat.title() # Return the raw category nicely formatted (e.g. "Railings")

def get_discipline(filename, revit_category):
    """
    Determines discipline using the File Name + Revit Category.
    """
    filename = str(filename).upper()
    cat = str(revit_category).upper()
    
    # 1. Structural / Arch Files
    if "AR&ST" in filename or "_ST_" in filename:
        if any(x in cat for x in ["ARCH", "WALL", "DOOR", "WINDOW", "RAILING", "CEILING"]): return "Architectural"
        return "Structural"

    # 2. MEP System Prefixes via Category
    if "FIRE" in cat or "SPRINKLER" in cat: return "Fire Protection"
    if "ELECTRICAL" in cat or "CABLE" in cat or "CONDUIT" in cat or "LIGHTING" in cat: return "Electrical"
    if "MECHANICAL" in cat or "DUCT" in cat or "AIR" in cat: return "Mechanical"
    if "PLUMBING" in cat or "PIPE" in cat: return "Plumbing"
    
    return "General/Other"

def get_severity(distance):
    try: overlap = abs(float(distance))
    except: return "Low"
    if overlap > critical_threshold: return "Critical"
    elif overlap > moderate_threshold: return "Moderate"
    else: return "Low"

def parse_navisworks(filepath):

    if not os.path.exists(filepath):
        return []
        
    try: tree = ET.parse(filepath); root = tree.getroot()
    except Exception as e:
        # Error will be caught in main and shown via messagebox
        raise

    clash_data = []
    
    for batchtest in root.findall(".//batchtest"):
        for clashtest in batchtest.findall("./clashtests/clashtest"):
            for result in clashtest.findall("./clashresults/clashresult"):
                clash_name = result.get('name')
                status = result.get('status')
                distance_val = result.get('distance')
                
                pos_node = result.find('./clashpoint/pos3f')
                pos_x = float(pos_node.get('x')) if pos_node is not None else 0.0
                pos_y = float(pos_node.get('y')) if pos_node is not None else 0.0
                pos_z = float(pos_node.get('z')) if pos_node is not None else 0.0

                grid_raw = result.find('gridlocation')
                grid_txt = grid_raw.text if grid_raw is not None else ""
                if " : " in grid_txt: grid_line = grid_txt.split(" : ")[0]
                else: grid_line = "Unknown"

                date_node = result.find('./createddate/date')
                created_date = f"{date_node.get('year')}-{date_node.get('month').zfill(2)}-{date_node.get('day').zfill(2)}" if date_node is not None else "Unknown"

                clash_objects = result.findall('./clashobjects/clashobject')
                if len(clash_objects) < 2: continue

                # Path Helper
                def get_path_nodes(clash_obj):
                    path_link = clash_obj.find('pathlink')
                    return [node.text for node in path_link.findall('node') if node.text] if path_link is not None else []

                # Level Extraction (Index 3)
                nodes1 = get_path_nodes(clash_objects[0])
                nodes2 = get_path_nodes(clash_objects[1])
                
                level = "Unknown"
                if len(nodes1) > 3 and nodes1[3] not in ["<No level>", "File"]: level = nodes1[3]
                elif len(nodes2) > 3 and nodes2[3] not in ["<No level>", "File"]: level = nodes2[3]
                elif " : " in grid_txt: level = grid_txt.split(" : ")[1]

                # Item Info Extraction
                def process_item(clash_obj, nodes):
                    # 1. Filename (Index 2)
                    filename = nodes[2] if len(nodes) > 2 else "Unknown"
                    
                    # 2. Revit Category (Index 4)
                    revit_cat = nodes[4] if len(nodes) > 4 else "Unknown Category"
                    
                    # 3. Item Name
                    smart_tag = clash_obj.find("./smarttags/smarttag[name='Item Name']/value")
                    name = smart_tag.text if smart_tag is not None else "Unknown"
                    
                    # 4. Derived Logic
                    discipline = get_discipline(filename, revit_cat)
                    dash_cat = get_dashboard_category(revit_cat, name)
                    
                    return name, discipline, revit_cat, dash_cat

                name1, disc1, revit_cat1, dash_cat1 = process_item(clash_objects[0], nodes1)
                name2, disc2, revit_cat2, dash_cat2 = process_item(clash_objects[1], nodes2)

                try: dist_float = float(distance_val) if distance_val else 0.0
                except: dist_float = 0.0

                clash_data.append({
                    'Clash ID': clash_name,
                    'Status': status,
                    'Severity': get_severity(distance_val),
                    'Level': level,
                    'Grid': grid_line,
                    'Date Found': created_date,
                    'Discipline 1': disc1,
                    'Discipline 2': disc2,
                    'Revit Cat 1': revit_cat1,
                    'Revit Cat 2': revit_cat2,
                    'Dashboard Cat 1': dash_cat1,
                    'Dashboard Cat 2': dash_cat2,
                    'Item 1': name1,
                    'Item 2': name2,
                    'Clash Group': f"{disc1} vs {disc2}",
                    'Pos X': pos_x,
                    'Pos Y': pos_y,
                    'Pos Z': pos_z,
                    'Distance': dist_float,
                    'Clash_Weight': abs(dist_float) # Positive value for Weighted Charts
                })

    # ----------------------------------------------------
    # 🔁 POST-PROCESSING: Derived columns for Power BI
    # ----------------------------------------------------
    if not clash_data:
        return clash_data

    # 1) Normalised XY for heatmap (start from 0,0)
    pos_x_values = [row['Pos X'] for row in clash_data]
    pos_y_values = [row['Pos Y'] for row in clash_data]
    min_x = min(pos_x_values) if pos_x_values else 0
    min_y = min(pos_y_values) if pos_y_values else 0
    
    for row in clash_data:
        row['X_Normalized'] = row['Pos X'] - min_x
        row['Y_Normalized'] = row['Pos Y'] - min_y

    # 2) Critical flag
    for row in clash_data:
        row['Is_Critical'] = 1 if row['Severity'] == 'Critical' else 0

    # 3) Symmetric category pair (for category-to-category matrix)
    for row in clash_data:
        a = str(row.get('Dashboard Cat 1', '')) if row.get('Dashboard Cat 1') else ''
        b = str(row.get('Dashboard Cat 2', '')) if row.get('Dashboard Cat 2') else ''
        pair = sorted([a, b])
        row['CatPair_Row'] = pair[0]
        row['CatPair_Col'] = pair[1]

    # 4) Per-Level Top-N rank for critical clashes (by Clash_Weight descending)
    critical_clashes = [row for row in clash_data if row['Severity'] == 'Critical']
    
    if critical_clashes:
        # Group by level and rank within each level
        level_groups = defaultdict(list)
        for clash in critical_clashes:
            level_groups[clash['Level']].append(clash)
        
        # Rank within each level
        for level, clashes in level_groups.items():
            sorted_clashes = sorted(clashes, key=lambda x: x['Clash_Weight'], reverse=True)
            for rank, clash in enumerate(sorted_clashes, start=1):
                clash['Critical_Rank_Level'] = rank
    
    # Add None for non-critical clashes
    clash_id_to_rank = {clash['Clash ID']: clash.get('Critical_Rank_Level') 
                        for clash in critical_clashes}
    
    for row in clash_data:
        if row['Clash ID'] not in clash_id_to_rank:
            row['Critical_Rank_Level'] = None

    # 5) Z-Axis Sorting Logic for levels
    valid_clashes = [row for row in clash_data 
                     if row['Level'] not in ['Unknown', '<No level>']]
    
    if valid_clashes:
        # Group by level and calculate average Z
        level_z_groups = defaultdict(list)
        for clash in valid_clashes:
            level_z_groups[clash['Level']].append(clash['Pos Z'])
        
        # Calculate mean Z for each level and sort
        level_stats = {level: sum(z_vals) / len(z_vals) 
                      for level, z_vals in level_z_groups.items()}
        sorted_levels = sorted(level_stats.items(), key=lambda x: x[1])
        level_rank = {level: i for i, (level, _) in enumerate(sorted_levels)}
        
        for row in clash_data:
            row['Level_Sort'] = level_rank.get(row['Level'], 9999)
    else:
        for row in clash_data:
            row['Level_Sort'] = 0

    return clash_data

def write_to_csv(clash_data, output_path):
    """Write clash data to CSV file using Python's built-in csv module"""
    headers = [
        'Clash ID', 'Status', 'Severity', 'Level', 'Grid', 'Date Found',
        'Discipline 1', 'Discipline 2', 'Revit Cat 1', 'Revit Cat 2',
        'Dashboard Cat 1', 'Dashboard Cat 2',
        'Item 1', 'Item 2', 'Clash Group',
        'Pos X', 'Pos Y', 'Pos Z', 'Distance', 'Clash_Weight',
        'X_Normalized', 'Y_Normalized',
        'Is_Critical','CatPair_Row', 'CatPair_Col',
        'Critical_Rank_Level',
        'Level_Sort'
    ]
    
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        
        for clash in clash_data:
            # Prepare row data, handling None values
            row = {}
            for header in headers:
                value = clash.get(header, '')
                # Handle None values
                if value is None:
                    value = ''
                row[header] = value
            writer.writerow(row)

# Execution
try:
    clash_data = parse_navisworks(xml_path)

    if clash_data:
        try:
            write_to_csv(clash_data, output_path)
            # Show success message
            messagebox.showinfo(
                "Success",
                f"Conversion complete!\n\nFile created at:\n{output_path}\n\nClash records processed: {len(clash_data)}"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create CSV file:\n{e}")
            root.destroy()
            sys.exit(1)
    else:
        messagebox.showwarning("Warning", "No clash data found in the XML file.")
        root.destroy()
        sys.exit(1)
except Exception as ex:
    messagebox.showerror("Error", f"Error during conversion:\n{ex}")
    root.destroy()
    sys.exit(1)
finally:
    root.destroy()