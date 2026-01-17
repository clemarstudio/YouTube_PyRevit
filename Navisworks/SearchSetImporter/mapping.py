# --- 1. GLOBAL SOURCE OF TRUTH ---

# A. Category Mapping (The "Tabs" in Navisworks Find Items)
# These are the items visible in the "Category" dropdown of the Find Items window.
CATEGORY_MAP = {
    "Autodesk Material": "LcOaProteinMaterialAttribute",
    "Base Constraint": "LcRevitData_Parameter",
    "Base Level": "LcRevitData_Parameter",
    "Category": "Category",
    "Custom": "LcRevitData_Custom",
    "DuctType": "DuctType",              # Updated from sample_3
    "Element": "LcRevitData_Element",
    "Element ID": "LcRevitId",
    "Entity Handle": "LcRevitData_EntityHandle",
    "Family": "lcldrevit_tab_family",
    "Geometry": "LcOaGeometry",
    "Grid": "LcRevitData_Grid",
    "Hyperlinks": "LcOaURLAttribute",
    "Identity": "LcOaSceneIdentity",
    "Item": "LcOaNode",
    "Level": "LcRevitData_Parameter",
    "Line Style": "LcRevitData_Parameter",
    "LineStyle": "LineStyle",
    "Location": "LcRevitPropertyLocation",
    "Material": "LcRevitData_Material",
    "MEPModel": "MEPModel",              # Updated from sample_3
    "MEPSystem": "MEPSystem",            # Updated from sample_3
    "Phase": "LcRevitData_Parameter",
    "Phase Created": "LcRevitData_Parameter",
    "Pipe Segment": "LcRevitData_Parameter",
    "PipeType": "PipeType",              # Updated from sample_3
    "Project": "LcRevitPropertyProject",
    "Reference Level": "LcRevitData_Parameter",
    "ReferenceLevel": "ReferenceLevel",  # Updated from sample_3
    "Revit Type": "LcRevitData_Type",
    "Schedule Level": "LcRevitData_Parameter",
    "Structural Material": "LcRevitData_Parameter",
    "System Type": "LcRevitData_Parameter",
    "TimeLiner": "LcOaTimeLiner",
    "Top Constraint": "LcRevitData_Parameter",
    "Top Level": "LcRevitData_Parameter",
    "Transform": "LcOaTransform",
    "WorksetId": "WorksetId"
}

# B. Property Mapping (Includes Common Built-in Parameters)
PROPERTY_MAP = {
    # --- Identity & Common ---
    "Name": "LcOaSceneBaseUserName",         # Item Tab Name
    "Revit Name": "LcRevitPropertyElementName", # Revit Tab Name
    "Id": "lcldrevit_parameter_Id",
    "GUID": "LcOaNodeGuid",
    "IfcGUID": "lcldrevit_parameter_IfcGUID",
    "UniqueId": "lcldrevit_parameter_UniqueId",
    "Workset": "LcRevitPropertyElementWorkset",
    "Category": "lcldrevit_parameter_Category",
    "Type": "LcRevitData_Type",
    "Family": "LcRevitData_Family",
    "FamilyName": "FamilyName",
    
    # --- MEP Specific ---
    "System Name": "lcldrevit_parameter_-1140324",
    "System Type": "SystemType",
    "System Classification": "lcldrevit_parameter_-1010110",
    "PartType": "PartType",
    "Circuit Number": "LcRevitPropertyElementCircuitNumber",
    "Service Type": "LcRevitPropertyElementServiceType",
    "Roughness": "Roughness",
    "Shape": "lcldrevit_parameter_-1140320",
    
    # --- Architectural / Structural ---
    "Building Story": "lcldrevit_parameter_-1007111",
    "Design Option": "lcldrevit_parameter_-1010106",
    "Elevation": "lcldrevit_parameter_-1007102",  # Updated for Navisworks 2023/2024 compatibility
    "Base Level": "LcRevitPropertyElementBaseConstraint",
    "Top Level": "LcRevitPropertyElementTopConstraint",
    "Structural": "lcldrevit_parameter_-1010108",
    "Category Id": "lcldrevit_parameter_CategoryId",
    "Export to IFC": "lcldrevit_parameter_ExporttoIFC",
    "IfcGUID": "lcldrevit_parameter_IfcGUID",
    "ProjectElevation": "ProjectElevation",
    
    # --- Project & Management ---
    "Document": "LcOaSceneBaseDocument",
    "Number of saves": "LcOaSceneNumberOfSaves",
    "Version": "LcOaSceneBaseVersion",
    "Project Issue Date": "lcldrevit_parameter_-1006321",
    "Project Name": "lcldrevit_parameter_-1006322",
    "Project Number": "lcldrevit_parameter_-1006323",
    "Project Status": "lcldrevit_parameter_-1006324",
    "Client Name": "lcldrevit_parameter_-1006325",
    "MC Version Saved": "lcldrevit_parameter_MCVersionSaved",
    
    # --- Graphics & Materials ---
    "Layer": "LcOaLayer",
    "Color": "LcOaMaterialColor",
    "Transparency": "LcOaMaterialTransparency",
    "Shininess": "LcOaMaterialShininess",
    "Smoothness": "LcOaMaterialSmoothness",
    "Glow": "LcOaMaterialGlow",
    "Line Style": "lcldrevit_parameter_-1010109",
    "Material Type": "lcldrevit_parameter_MaterialType",

    
    # --- Location ---
    "Latitude": "LcOaLocationLatitude",
    "Longitude": "LcOaLocationLongitude",
    "Timezone": "LcOaLocationTimezone",

    
    # --- Phasing ---
    "Phase Created": "LcRevitPropertyElementPhaseCreated", 
    "Phase Demolished": "LcRevitPropertyElementPhaseDemolished", 
    
    # --- Constraints / Location ---
    "Level": "LcRevitPropertyElementLevel", 
    "Base Constraint": "LcRevitPropertyElementBaseConstraint",
    "Top Constraint": "LcRevitPropertyElementTopConstraint",
    "Base Offset": "LcRevitPropertyElementBaseOffset",
    "Top Offset": "LcRevitPropertyElementTopOffset",
    "Unconnected Height": "LcRevitPropertyElementUnconnectedHeight",
    "Room Name": "LcRevitPropertyElementRoomName",
    "Room Number": "LcRevitPropertyElementRoomNumber",
    
    # --- Dimensions ---
    "IntegerValue": "IntegerValue",         # For WorksetId tab
    "Number of saves": "LcOaSceneNumberOfSaves", # For Identity tab
    "Value": "LcOaNat64AttributeValue",     # For Element ID tab
    "Host": "lcldrevit_parameter_-1012843", # For Family tab
    "Project Issue Date": "lcldrevit_parameter_-1006321", # For Project tab
    "Length": "lcldrevit_parameter_-1001375",  # Updated for Navisworks 2023/2024 compatibility
    "Area": "LcRevitPropertyElementArea",
    "Volume": "LcRevitPropertyElementVolume",
    "Width": "LcRevitPropertyElementWidth",
    "Height": "LcRevitPropertyElementHeight",
    "Thickness": "LcRevitPropertyElementThickness",
    
    # --- Classification ---
    "System Type": "LcRevitPropertyElementSystemType", 
    "System Name": "LcRevitPropertyElementSystemName", 
    "System Classification": "LcRevitPropertyElementSystemClassification", 
    "Assembly Code": "LcRevitPropertyElementAssemblyCode", 
    "OmniClass": "LcRevitPropertyElementOmniClass",
    "Structural Usage": "LcRevitPropertyElementStructuralUsage",
    
    # --- MEP Specific ---
    "Panel": "LcRevitPropertyElementPanel",
    "Circuit Number": "LcRevitPropertyElementCircuitNumber",
    "Service Type": "LcRevitPropertyElementServiceType",
    "Size": "LcRevitPropertyElementSize",
    
    # --- Graphics / CAD ---
    "Layer": "LcOaLayer", 
    "Color": "LcOaMaterialColor", 
    "Transparency": "LcOaMaterialTransparency"
}

# C. MEP Type Mapping (Includes Common Built-in Parameters)
MEP_TYPE_MAP = {
            # Electrical
            "Voltage": ("float", True),
            "Apparent Load": ("float", True),
            "Current": ("float", True),
            "Wattage": ("float", True),
            "Panel": ("wstring", False), # Panels are names (strings)
            "Circuit Number": ("wstring", False), # "1,3,5" is a string
            "Number of Poles": ("int32", True),
            
            # Mechanical / Piping
            "Flow": ("float", True),
            "Velocity": ("float", True),
            "Pressure Drop": ("float", True),
            "Friction": ("float", True),
            "Size": ("wstring", False), # "200x300" is a string!
            "Diameter": ("linear", True), # Usually linear if pure number
            "Roughness": ("float", True),
            
            # Common Dimensions
            "Area": ("area", True),
            "Volume": ("volume", True),
            "Length": ("linear", True),
            "Width": ("linear", True),
            "Height": ("linear", True),
            "Thickness": ("linear", True),
            "Offset": ("linear", True),
            "Base Offset": ("linear", True),
            "Top Offset": ("linear", True),
            "Unconnected Height": ("linear", True),
            "Elevation": ("float", True),
            "ProjectElevation": ("float", True),
            "Computation Height": ("float", True),
            
            # Graphics / Materials
            "Transparency": ("float", True),
            "Shininess": ("float", True),
            "Smoothness": ("float", True),
            "Glow": ("float", True),
 
            # Location
            "Latitude": ("float", True),
            "Longitude": ("float", True),
            
            # Identification
            "Element ID": ("int32", True), # ID is effectively an integer
            "IntegerValue": ("int32", True),
            "Id": ("int32", True),
        }

# C. Logic Options
VALID_CONDITIONS = ["equals", "contains", "not_equals", "wildcard", "defined", "undefined", "less_than", "greater_than"]

# --- D. ROBUST TRANSLATORS ---
def get_internal_category(user_input):
    """Specifically for mapping the Navisworks Tab (Category)"""
    if not user_input: return "LcOaNode"
    clean = str(user_input).strip()
    # Handle "All Element" UX rename back to "Item" internal display
    if clean == "All Element": return "LcOaNode"
    return CATEGORY_MAP.get(clean, clean)

def get_internal_property(user_input, category_context=""):
    """Specifically for mapping the Parameter name (Property)"""
    if not user_input: return "LcOaSceneBaseUserName"
    clean = str(user_input).strip()
    
    # Context-Aware Logic for the "Name" property
    if clean == "Name":
        if category_context == "Category":
            return "Name" # Internal ID for Name inside the Category tab
        if category_context in ["Item", "All Element"]:
            return "LcOaSceneBaseUserName" # Internal ID for Name inside Item tab
        return "LcRevitPropertyElementName" # Default for Revit Parameter tabs
    
    # Context-Aware Logic for the "Type" property
    if clean == "Type":
        if category_context in ["Element", "All Element"]:
            return "LcRevitPropertyElementType" # Specific ID from export.xml
        return "LcRevitData_Type" # Default Revit Type tab
        
    return PROPERTY_MAP.get(clean, clean)

def get_internal_name(user_input):
    """Legacy support - attempts to find in either map"""
    clean = str(user_input).strip()
    if clean in CATEGORY_MAP: return CATEGORY_MAP[clean]
    return PROPERTY_MAP.get(clean, clean)
