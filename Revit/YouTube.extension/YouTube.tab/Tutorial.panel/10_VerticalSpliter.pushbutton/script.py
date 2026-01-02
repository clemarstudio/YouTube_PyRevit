# -*- coding: utf-8 -*-
from pyrevit import revit, forms, script
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType
import wpf
from System import Windows

doc = revit.doc
uidoc = revit.uidoc

class LevelItem:
    """Helper to wrap Revit Levels for the UI"""
    def __init__(self, level):
        self.Element = level
        self.Name = level.Name
        self.Elevation = level.Elevation
        self.IsChecked = False

class SplitterWindow(Windows.Window):
    def __init__(self):
        wpf.LoadComponent(self, script.get_bundle_file('ui.xaml'))
        
        # 1. Load Levels sorted by Elevation
        levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
        self.all_levels = sorted([LevelItem(l) for l in levels], key=lambda x: x.Elevation)
        self.lb_levels.ItemsSource = self.all_levels
        
        # Store selected element IDs here
        self.selected_ids = []

    # --- UI Event Handlers ---

    def pick_elements_click(self, sender, args):
        """Hides window, lets user pick, then shows window again"""
        self.Hide() # Hide UI so user can see model
        try:
            # Pick multiple objects
            refs = uidoc.Selection.PickObjects(ObjectType.Element, "Select Columns or Walls")
            self.selected_ids = [r.ElementId for r in refs]
            
            # Update label
            self.lbl_status.Text = "{} elements selected".format(len(self.selected_ids))
            self.lbl_status.Foreground = Windows.Media.Brushes.Green
            
        except Exception:
            # User pressed ESC
            pass
        finally:
            self.ShowDialog() # Bring UI back

    def select_all_click(self, sender, args):
        """Toggles all checkboxes"""
        is_checked = self.chk_select_all.IsChecked
        for item in self.all_levels:
            item.IsChecked = is_checked
        
        # Refresh the list to show checkboxes updating
        self.lb_levels.ItemsSource = None
        self.lb_levels.ItemsSource = self.all_levels

    def split_click(self, sender, args):
        """Validates and runs the split"""
        # 1. Validation
        if not self.selected_ids:
            forms.alert("You haven't picked any elements yet!")
            return

        split_levels = [x.Element for x in self.lb_levels.ItemsSource if x.IsChecked]
        if not split_levels:
            forms.alert("Please check at least one level to split by.")
            return

        # 2. Get actual element objects
        elements = [doc.GetElement(id) for id in self.selected_ids]
        
        # 3. Transaction
        t = Transaction(doc, "PyRevit Split")
        t.Start()
        
        try:
            count = 0
            for el in elements:
                # Basic Category Check
                cat_id = el.Category.Id.IntegerValue
                is_col = (cat_id == int(BuiltInCategory.OST_StructuralColumns) or 
                          cat_id == int(BuiltInCategory.OST_Columns))
                # TODO: Add wall category check here
                # is_wall = (cat_id == int(BuiltInCategory.OST_Walls))

                if is_col:
                    if self.split_column(el, split_levels): count += 1
                # TODO: Add wall splitting call here
                # elif is_wall:
                #     if self.split_wall(el, split_levels): count += 1

            t.Commit()
            forms.alert("Done! Split {} elements.".format(count))
            self.Close()

        except Exception as e:
            t.RollBack()
            forms.alert("Error: {}".format(e))

    # --- Split Logic ---
    # 
    # EXERCISE: After understanding column splitting, adapt this code for walls!
    # 
    # Key differences for walls:
    # 1. Parameter names:
    #    - Column: FAMILY_BASE_LEVEL_PARAM → Wall: WALL_BASE_CONSTRAINT
    #    - Column: FAMILY_TOP_LEVEL_PARAM → Wall: WALL_HEIGHT_TYPE
    #    - Column: FAMILY_BASE_LEVEL_OFFSET_PARAM → Wall: WALL_BASE_OFFSET
    #    - Column: FAMILY_TOP_LEVEL_OFFSET_PARAM → Wall: WALL_TOP_OFFSET
    #
    # 2. Creation method:
    #    - Column: NewFamilyInstance(point, symbol, level, structural_type)
    #    - Wall: Wall.Create(doc, curve, wall_type, base_level, height, base_offset, ...)
    #
    # 3. Additional steps for walls:
    #    - Cache wall.WallType.Id BEFORE deletion (critical!)
    #    - Project curve to level elevation (walls have curves, not points)
    #    - Calculate height explicitly (walls need height parameter)
    #    - Handle Unconnected height case (top might be ElementId.InvalidElementId)
    #
    # See answer.py for the complete solution!

    def split_column(self, col, split_levels):
        """
        Split a column by selected levels.
        
        Steps:
        1. Get bounding box to find element's vertical extent
        2. Find which selected levels cross through the element
        3. Get original column parameters (base/top levels, offsets, structural type)
        4. Build complete level list: base + crossing levels + top
        5. Create new column segments between consecutive levels
        6. Set offsets correctly (preserve original for first/last segments)
        7. Delete original column
        """
        # Step 1: Get Bounding Box
        # This tells us the vertical extent (minZ to maxZ) of the column
        bbox = col.get_BoundingBox(None)
        if not bbox: return False
        
        # Step 2: Find crossing levels
        # A level "crosses" the column if its elevation is between minZ and maxZ
        crossing = [l for l in split_levels if bbox.Min.Z < l.Elevation < bbox.Max.Z]
        if not crossing: return False  # No levels cross, nothing to split
        
        # Step 3: Get original column parameters
        # We need to preserve these values for the new segments
        base_param = col.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)
        current_base = doc.GetElement(base_param.AsElementId())
        
        # Find actual top level (closest level at or above maxZ)
        # We do this instead of using the top level parameter because unconnected 
        # elements have a top level parameter that is the same as the base level!
        all_project_levels = sorted(FilteredElementCollector(doc).OfClass(Level).ToElements(), key=lambda x: x.Elevation)
        actual_top_level = next((l for l in all_project_levels if l.Elevation >= bbox.Max.Z), None)
        if not actual_top_level:
            # Fallback to the highest project level if above all levels
            actual_top_level = all_project_levels[-1]
        
        # Get original offsets (these adjust the column's start/end positions)
        original_base_offset = col.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM).AsDouble()
        
        # Get original structural type (preserve it - don't hardcode!)
        original_structural_type = col.StructuralType
        
        # Step 4: Build complete level list
        # We need: base level + all crossing levels + corrected top level
        active_levels_raw = [current_base] + sorted(crossing, key=lambda x: x.Elevation) + [actual_top_level]
        # Remove duplicates while preserving order (using element ID as key)
        seen_ids = set()
        active_levels = []
        for l in active_levels_raw:
            if l.Id.IntegerValue not in seen_ids:
                active_levels.append(l)
                seen_ids.add(l.Id.IntegerValue)
        
        active_levels = sorted(active_levels, key=lambda x: x.Elevation)
        
        # Step 5: Create segments between consecutive levels
        # For each pair of levels, create a new column segment
        for i in range(len(active_levels) - 1):
            base = active_levels[i]
            top = active_levels[i+1]
            
            # Create new column instance at the same location
            # Parameters: point, symbol, base level, structural type
            new_col = doc.Create.NewFamilyInstance(
                col.Location.Point,  # Same X,Y location as original
                col.Symbol,          # Same column type
                base,                # Base level for this segment
                original_structural_type  # Preserve structural type
            )
            
            # Set top level constraint
            new_col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM).Set(top.Id)
            
            # Set base offset
            # First segment: keep original offset (preserves column's starting position)
            # Other segments: use 0 (level-to-level)
            if i == 0:
                new_col.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM).Set(original_base_offset)
            else:
                new_col.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM).Set(0)
            
            # Set top offset
            # Last segment: recalculate from actual top Z (handles cases with large offsets)
            # Other segments: use 0 (level-to-level)
            if i == len(active_levels) - 2:  # Last segment
                actual_top_z = bbox.Max.Z
                recalculated_top_offset = actual_top_z - top.Elevation
                new_col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM).Set(recalculated_top_offset)
            else:
                new_col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM).Set(0)

        # Step 6: Delete original column (only after all segments are created)
        doc.Delete(col.Id)
        return True

    # TODO: Implement split_wall() function
    # 
    # HINTS:
    # 1. Follow the same 5-step structure as split_column()
    # 2. Change parameter names (see mapping above)
    # 3. Cache wall.WallType.Id BEFORE any operations (walls get deleted)
    # 4. Instead of NewFamilyInstance, use Wall.Create()
    # 5. Walls need curve projection to level elevation
    # 6. Walls need explicit height calculation
    # 7. Handle Unconnected height case (check if top is ElementId.InvalidElementId)
    #
    # def split_wall(self, wall, split_levels):
    #     # Your code here!
    #     pass

# Run
SplitterWindow().ShowDialog()
