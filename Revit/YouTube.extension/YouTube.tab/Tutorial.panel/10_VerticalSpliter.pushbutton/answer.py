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
                is_wall = (cat_id == int(BuiltInCategory.OST_Walls))

                if is_col:
                    if self.split_column(el, split_levels): count += 1
                elif is_wall:
                    if self.split_wall(el, split_levels): count += 1

            t.Commit()
            forms.alert("Done! Split {} elements.".format(count))
            self.Close()

        except Exception as e:
            t.RollBack()
            forms.alert("Error: {}".format(e))

    # --- Split Logic ---

    def split_column(self, col, split_levels):
        # 1. Get Bounding Box
        bbox = col.get_BoundingBox(None)
        if not bbox: return False
        
        # 2. Find crossing levels (levels that the column passes through)
        crossing = [l for l in split_levels if bbox.Min.Z < l.Elevation < bbox.Max.Z]
        if not crossing: return False
        
        # 3. Get original column parameters
        base_param = col.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)
        current_base = doc.GetElement(base_param.AsElementId())
        
        # Find actual top level (closest level at or above maxZ)
        all_project_levels = sorted(FilteredElementCollector(doc).OfClass(Level).ToElements(), key=lambda x: x.Elevation)
        actual_top_level = next((l for l in all_project_levels if l.Elevation >= bbox.Max.Z), None)
        if not actual_top_level:
            # Fallback to the closest level below if wall is above all project levels
            actual_top_level = all_project_levels[-1]

        # Get original base offset and structural type
        original_base_offset = col.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM).AsDouble()
        original_structural_type = col.StructuralType
        
        # 4. Build complete level list: base + crossing levels + corrected top
        active_levels_raw = [current_base] + sorted(crossing, key=lambda x: x.Elevation) + [actual_top_level]
        # Remove duplicates while preserving order (using element ID as key)
        seen_ids = set()
        active_levels = []
        for l in active_levels_raw:
            if l.Id.IntegerValue not in seen_ids:
                active_levels.append(l)
                seen_ids.add(l.Id.IntegerValue)
        
        active_levels = sorted(active_levels, key=lambda x: x.Elevation)
        
        # 5. Create segments between consecutive levels
        for i in range(len(active_levels) - 1):
            base = active_levels[i]
            top = active_levels[i+1]
            
            # Create new column instance
            new_col = doc.Create.NewFamilyInstance(
                col.Location.Point, 
                col.Symbol, 
                base, 
                original_structural_type
            )
            
            # Set top level and offsets
            new_col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM).Set(top.Id)
            
            # Base offset: first segment keeps original, others use 0
            new_col.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM).Set(original_base_offset if i == 0 else 0)
            
            # Top offset: last segment recalculates from actual top Z, others use 0
            if i == len(active_levels) - 2:
                recalculated_top_offset = bbox.Max.Z - top.Elevation
                new_col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM).Set(recalculated_top_offset)
            else:
                new_col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM).Set(0)

        doc.Delete(col.Id)
        return True

    def split_wall(self, wall, split_levels):
        # 1. Get Bounding Box
        bbox = wall.get_BoundingBox(None)
        if not bbox: return False
        
        # 2. Find crossing levels (levels that the wall passes through)
        crossing = [l for l in split_levels if bbox.Min.Z < l.Elevation < bbox.Max.Z]
        if not crossing: return False
        
        # 3. Cache wall properties BEFORE deletion
        wall_type_id = wall.WallType.Id
        base_param = wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)
        current_base = doc.GetElement(base_param.AsElementId())
        original_base_offset = wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).AsDouble()
        
        # Find actual top level (closest level at or above maxZ)
        all_project_levels = sorted(FilteredElementCollector(doc).OfClass(Level).ToElements(), key=lambda x: x.Elevation)
        actual_top_level = next((l for l in all_project_levels if l.Elevation >= bbox.Max.Z), None)
        if not actual_top_level:
            actual_top_level = all_project_levels[-1]
            
        # 4. Build complete level list: base + crossing levels + corrected top
        active_levels_raw = [current_base] + sorted(crossing, key=lambda x: x.Elevation) + [actual_top_level]
        # Remove duplicates while preserving order (using element ID as key)
        seen_ids = set()
        active_levels = []
        for l in active_levels_raw:
            if l.Id.IntegerValue not in seen_ids:
                active_levels.append(l)
                seen_ids.add(l.Id.IntegerValue)
        
        active_levels = sorted(active_levels, key=lambda x: x.Elevation)
        
        # 5. Create segments between consecutive levels
        for i in range(len(active_levels) - 1):
            base = active_levels[i]
            top = active_levels[i+1]
            
            # Project curve to level elevation
            original_curve = wall.Location.Curve
            new_start = XYZ(original_curve.GetEndPoint(0).X, original_curve.GetEndPoint(0).Y, base.Elevation)
            new_end = XYZ(original_curve.GetEndPoint(1).X, original_curve.GetEndPoint(1).Y, base.Elevation)
            curve_at_level = Line.CreateBound(new_start, new_end) if isinstance(original_curve, Line) else original_curve
            
            # Calculate height for segment creation
            is_last_segment = (i == len(active_levels) - 2)
            height = (bbox.Max.Z - base.Elevation) if is_last_segment else (top.Elevation - base.Elevation)
            base_offset = original_base_offset if i == 0 else 0
            
            # Create new wall
            new_wall = Wall.Create(doc, curve_at_level, wall_type_id, base.Id, height, base_offset, False, False)
            
            # Set top constraint and top offset
            if is_last_segment:
                new_wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE).Set(top.Id)
                recalculated_top_offset = bbox.Max.Z - top.Elevation
                new_wall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET).Set(recalculated_top_offset)
            else:
                new_wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE).Set(top.Id)
                new_wall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET).Set(0)

        doc.Delete(wall.Id)
        return True

# Run
SplitterWindow().ShowDialog()
