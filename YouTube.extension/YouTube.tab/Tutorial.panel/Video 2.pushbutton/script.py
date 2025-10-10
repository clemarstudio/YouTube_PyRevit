from pyrevit import revit, DB

with revit.Transaction("Remove CAD Imports"):

    cad_imports = DB.FilteredElementCollector(revit.doc).OfClass(DB.ImportInstance).ToElements()

    for cad in cad_imports:
        if '.dwg' in cad.Category.Name:
            revit.doc.Delete(cad.Id)
