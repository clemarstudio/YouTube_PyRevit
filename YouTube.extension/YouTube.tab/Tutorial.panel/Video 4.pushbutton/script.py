from pyrevit import forms
import os
from Microsoft.WindowsAPICodePack.Dialogs import CommonOpenFileDialog, CommonFileDialogFilter

app = __revit__.Application

def browse_File():

    files_Dialog = CommonOpenFileDialog()
    files_Dialog.Title = "Select Files"
    files_Dialog.IsFolderPicker = False
    files_Dialog.Multiselect = True
    files_Dialog.Filters.Add(CommonFileDialogFilter("Revit files", "*.rvt;*.rfa"))
    files_Dialog.ShowDialog()
    try:
        return list(files_Dialog.FileNames)
    except:
        return []
    
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

def get_Revit_files_from_folder(folder_path):
    
    # Check if the folder exists
    if not folder_path:
        return []

    # Scan the folder and collect all Revit files
    revit_files = [
        os.path.join(folder_path, file)
        for file in os.listdir(folder_path)
        if file.endswith((".rvt", ".rfa"))  # Only pick Revit files
    ]

    return revit_files  # Return the list of files

def open_and_save_revit_file(file_path):

    print("Processing: {file_path}".format(file_path=file_path))

    # Convert the file path into a Revit ModelPath
    model_path = ModelPathUtils.ConvertUserVisiblePathToModelPath(file_path)

    # Set open options - detach from central if it's a workshared model
    open_options = OpenOptions()
    open_options.DetachFromCentralOption = DetachFromCentralOption.DetachAndPreserveWorksets

    # Open the document
    doc = app.OpenDocumentFile(model_path, open_options)

    # Set save options
    save_options = SaveOptions()

    # Save and close the document
    doc.Save(save_options)
    doc.Close(False)

    print("Saved and closed: {file_path}".format(file_path=file_path))



## either browse path or files
## 1. browse path
selected_Path = browse_Path()
selected_Files = get_Revit_files_from_folder(selected_Path)

## 2. browse files
selected_Files = browse_File()

## upgrade
if selected_Files:

    from Autodesk.Revit.DB import *

    for file in selected_Files:
        open_and_save_revit_file(file)

else:
    print("No files selected.")

















    