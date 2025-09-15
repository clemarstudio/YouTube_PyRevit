from pyrevit import forms
from Autodesk.Revit.DB import *
from Microsoft.WindowsAPICodePack.Dialogs import CommonOpenFileDialog

def browse_Path():
    folder_Dialog = CommonOpenFileDialog()
    folder_Dialog.Title = "Select Folder"
    folder_Dialog.IsFolderPicker = True
    folder_Dialog.Multiselect = False
    folder_Dialog.ShowDialog()
    try:
        return folder_Dialog.FileName
    except:
        return None

app = __revit__.Application
uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

# Step 1: Select 3D Views
collector = FilteredElementCollector(doc).OfClass(View3D)
all_views = sorted([v.Name for v in collector])
selected_views = forms.SelectFromList.show(all_views, multiselect=True, button_name="Select 3D Views to Export")

if selected_views: 

    folder = browse_Path()

    if selected_views and folder:
        options = NavisworksExportOptions()
        options.ExportScope = NavisworksExportScope.View
        options.ExportLinks = True
        options.ExportParts = True

        for view in collector:
            if view.Name in selected_views:
                options.ViewId = view.Id
                doc.Export(folder, view.Name + ".nwc", options)
                print("Exported:", view.Name)
    else:
        print("No views or folder selected.")







