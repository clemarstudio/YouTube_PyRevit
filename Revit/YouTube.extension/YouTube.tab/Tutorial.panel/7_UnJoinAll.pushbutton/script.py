from pyrevit import revit, DB

# 1 Define categories to process
categories = [
    DB.BuiltInCategory.OST_StructuralColumns,
    DB.BuiltInCategory.OST_StructuralFraming,
    DB.BuiltInCategory.OST_Floors,
    DB.BuiltInCategory.OST_Walls
]

# 2 Start transaction
with revit.Transaction("Unjoin Elements"):
    for cate in categories:
        elems = DB.FilteredElementCollector(revit.doc, revit.active_view.Id)\
                  .OfCategory(cate)\
                  .WhereElementIsNotElementType()\
                  .ToElements()

        for ele in elems:
            outline = DB.Outline(
                ele.get_BoundingBox(revit.active_view).Min,
                ele.get_BoundingBox(revit.active_view).Max)
            bbFilter = DB.BoundingBoxIntersectsFilter(outline, False)

            # 3 Find and unjoin intersected elements
            for other_cate in categories:
                for target in DB.FilteredElementCollector(revit.doc, revit.active_view.Id)\
                                 .OfCategory(other_cate)\
                                 .WherePasses(bbFilter)\
                                 .ToElements():
                    try:
                        DB.JoinGeometryUtils.UnjoinGeometry(revit.doc, ele, target)
                    except:
                        pass

