from Autodesk.Revit.DB import *

# --- Document / View handles ---
uiapp = __revit__  # provided by pyRevit
app   = uiapp.Application
uidoc = uiapp.ActiveUIDocument
doc   = uidoc.Document
view  = doc.ActiveView

# 1. get elements in view by category
def elements_in_view_by_category(categories):
    return list(FilteredElementCollector(doc, view.Id).OfCategory(categories).WhereElementIsNotElementType().ToElements())
	
# 2. create outline from element's bounding box
def create_outline(ele):
    try:
        bb = ele.get_BoundingBox(view)
        if bb and bb.Min and bb.Max:
            return Outline(bb.Min, bb.Max)
    except:
        pass
    return None
    
# 3. checking by bbox
def checking_by_bbox(category, outline):
    if outline is None:
        return []

    bb_filter = BoundingBoxIntersectsFilter(outline, False)
    return list(FilteredElementCollector(doc, view.Id).OfCategory(category).WherePasses(bb_filter).WhereElementIsNotElementType().ToElements())

# 4. try join
def try_join(a, b):
    try:
        JoinGeometryUtils.JoinGeometry(doc, a, b)
    except:
        pass

# 5. try switch order
def try_switch_order(keeper, cutter):
    try:
        if JoinGeometryUtils.IsCuttingElementInJoin(doc, cutter, keeper):
            JoinGeometryUtils.SwitchJoinOrder(doc, keeper, cutter)
    except:
        pass


# ========= Main Logic =========

def main():

    # 1. BuiltInCategory mapping
    priority = [
        BuiltInCategory.OST_StructuralColumns,   # 0 Columns
        BuiltInCategory.OST_StructuralFraming,   # 1 Beams
        BuiltInCategory.OST_Floors,              # 2 Floors/Slabs
        BuiltInCategory.OST_Walls,               # 3 Walls
    ]

    # 2. Collect elements per category
    buckets = [elements_in_view_by_category(bic) for bic in priority]

    # 3.1 Start one transaction for the whole pass
    t = Transaction(doc, "Auto-Join (Beginner)")
    t.Start()

    # 3.2 Walk the priority list downwards (from higher priority to lower priority)
    # For each element, we join with:
    #   1) same-category neighbors, then
    #   2) every LATER category (lower priority) to enforce dominance
    for group_number, p_cat in enumerate(priority):

        # 3.2.1 Get the current group of elements
        current_group = buckets[group_number]

        # 3.2.2 Process each element in the current group
        for ele in current_group:
            outline = create_outline(ele)
            if outline is None:
                continue

            # 1) self-join (same category neighbors)
            for other in checking_by_bbox(p_cat, outline):
                if other.Id == ele.Id:
                    continue
                # Attempt join; if join exists or invalid, it's fine
                try_join(ele, other)
                # If order is wrong (other is cutting ele), flip to make 'ele' the keeper
                try_switch_order(ele, other)

            # 2) join with every *lower-priority* category to propagate dominance
            for lower_group_number in range(group_number + 1, len(priority)):
                lower_cat = priority[lower_group_number]
                for other in checking_by_bbox(lower_cat, outline):
                    if other.Id == ele.Id:
                        continue
                    try_join(ele, other)
                    try_switch_order(ele, other)

    t.Commit()

# ========= Run =========
main()
print("Done! Processed Columns -> Beams -> Floors -> Walls in the Active View.")