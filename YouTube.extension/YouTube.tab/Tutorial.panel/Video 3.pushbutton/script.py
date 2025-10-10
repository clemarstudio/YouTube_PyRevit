from pyrevit import revit, DB

elements = DB.FilteredElementCollector(revit.doc).WhereElementIsNotElementType()

# Start a transaction to make changes
with revit.Transaction("Remove Paint"):

    for elem in elements:
        geometry = elem.get_Geometry(DB.Options()) # Get element geometry
        if geometry:
            for geo_obj in geometry:
                try:
                    for face in geo_obj.Faces: # Loop through element faces
                        revit.doc.RemovePaint(elem.Id, face) # Remove paint
                except:
                    pass # Ignore errors and move on
