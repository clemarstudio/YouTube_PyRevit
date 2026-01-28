from pyrevit import revit, DB, forms, script

# --- PRE-REQUISITES ---
# Get the active document (the Revit file you are working on)
doc = revit.doc
uidoc = revit.uidoc

## 1. Check Active View and Get Title Block
# First, we check if the user has a sheet open
active_sheet = doc.ActiveView
if not isinstance(active_sheet, DB.ViewSheet):
    forms.alert("Please open a Sheet view first and run the code again!", exitscript=True)

# Instead of asking the user to pick a title block, we automatically 
# find the one already used on the active sheet.
title_block = DB.FilteredElementCollector(doc, active_sheet.Id)\
                .OfCategory(DB.BuiltInCategory.OST_TitleBlocks)\
                .FirstElement()

if not title_block:
    forms.alert("The active sheet does not have a Title Block! Please add one first.", exitscript=True)

# We get the Type ID to use for creating new sheets later
title_block_type_id = title_block.GetTypeId()

## 2. Define Placement Zone (Pick Area First)
# Prompt the user to click two points on the active sheet to define the "safe zone" for view placement
forms.alert("Click two points to define the placement area on this sheet.")
try:
    pt1 = uidoc.Selection.PickPoint("Pick first corner of placement zone")
    pt2 = uidoc.Selection.PickPoint("Pick second corner of placement zone")
except Exception:
    # User likely pressed Esc or canceled
    script.exit()

# Calculate the center and dimensions of the zone
min_x, max_x = min(pt1.X, pt2.X), max(pt1.X, pt2.X)
min_y, max_y = min(pt1.Y, pt2.Y), max(pt1.Y, pt2.Y)

center = DB.XYZ((min_x + max_x) / 2, (min_y + max_y) / 2, 0)

## 3. Collect and Select Unplaced Views
# Find views that are NOT already on a sheet
placed_view_ids = set(vp.ViewId for vp in DB.FilteredElementCollector(doc).OfClass(DB.Viewport))
all_views = DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements()

unplaced_views = []
for v in all_views:
    if v.IsTemplate or isinstance(v, (DB.ViewSheet, DB.ViewSchedule)):
        continue
    if not v.CanBePrinted:
        continue
    if v.Id in placed_view_ids:
        continue
    unplaced_views.append(v)

if not unplaced_views:
    forms.alert("No unplaced views found!", exitscript=True)

# Show a list for the user to select which views they want to generate sheets for
selected_view_names = forms.SelectFromList.show(
    [revit.query.get_name(v) for v in unplaced_views],
    title="Select Views to Place on Sheets",
    multiselect=True
)

if not selected_view_names:
    script.exit()

final_views = [v for v in unplaced_views if revit.query.get_name(v) in selected_view_names]

## 4. Input Prefix and Start Number
prefix = forms.ask_for_string(default="A-", title="Sheet Number Prefix")
start_number_str = forms.ask_for_string(default="101", title="Starting Sheet Number")

if not prefix or not start_number_str:
    script.exit()

try:
    start_number = int(start_number_str)
except ValueError:
    forms.alert("Invalid start number! Please enter an integer.", exitscript=True)

## 5. Process and Create Sheets
# Use a TransactionGroup to bundle all sheet creations into one "Undo" step
with revit.TransactionGroup("Batch Sheet Creation"):
    success_count = 0
    for i, view in enumerate(final_views):
        # Calculate new sheet number (e.g., A-101, A-102...)
        sheet_num = "{}{}".format(prefix, start_number + i)
        
        # Start a sub-transaction for each individual sheet
        with revit.Transaction("Create Sheet " + sheet_num):
            try:
                # 1. Create the sheet using the Title Block we found at the start
                new_sheet = DB.ViewSheet.Create(doc, title_block_type_id)
                new_sheet.Name = revit.query.get_name(view)
                new_sheet.SheetNumber = sheet_num
                
                # 2. Place the view onto the sheet at our calculated center
                DB.Viewport.Create(doc, new_sheet.Id, view.Id, center)
                success_count += 1
            except Exception as e:
                print("Failed to create sheet for {}: {}".format(revit.query.get_name(view), e))

    forms.alert("Successfully created {} sheets!".format(success_count))
