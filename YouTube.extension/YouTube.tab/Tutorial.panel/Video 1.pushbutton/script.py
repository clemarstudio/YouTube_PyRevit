from pyrevit import revit, DB

# Start a transaction
with revit.Transaction("Rename Sheets"):

    # Get all sheets
    sheets = DB.FilteredElementCollector(revit.doc).OfClass(DB.ViewSheet).ToElements()

    ## Rename Sheets
    for sheet in sheets:
        sheet.Name = "AED/PS1331/BS/CSD/" + sheet.Name