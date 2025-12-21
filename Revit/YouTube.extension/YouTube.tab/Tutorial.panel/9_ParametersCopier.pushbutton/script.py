# --- [0] IMPORTS ---
from pyrevit import revit, DB, UI, script
from pyrevit import forms
import wpf
from System import Windows

doc = revit.doc

# --- [1] STATE CLASS (Data Storage) ---
class ToolState:
    def __init__(self):
        self.source_id = None
        self.target_ids = [] 
        self.mode = "auto"
        
        # Track if we are doing Instance or Type copy
        self.param_type_mode = "Instance" 
        
        self.selected_params_auto = []
        self.selected_param_src_manual = None
        self.selected_param_tgt_manual = None

# --- [2] HELPER FUNCTIONS (Logic) ---
def get_element_or_type(element, mode="Instance"):
    """Returns the Element itself OR its Type Element based on mode."""
    if mode == "Instance":
        return element
    elif mode == "Type":
        type_id = element.GetTypeId()
        if type_id and type_id != DB.ElementId.InvalidElementId:
            return doc.GetElement(type_id)
    return None

def get_param_value(element, param_name):
    if not element: return None
    param = element.LookupParameter(param_name)
    if not param or not param.HasValue:
        return None
    
    if param.StorageType == DB.StorageType.String:
        return param.AsString()
    elif param.StorageType == DB.StorageType.Integer:
        return param.AsInteger()
    elif param.StorageType == DB.StorageType.Double:
        return param.AsDouble()
    elif param.StorageType == DB.StorageType.ElementId:
        return param.AsElementId()
    return None

def set_param_value(element, param_name, value):
    if not element: return False
    param = element.LookupParameter(param_name)
    
    # SAFETY: Skip ReadOnly to prevent crashes
    if not param or param.IsReadOnly:
        return False
    
    try:
        if param.StorageType == DB.StorageType.String:
            param.Set(str(value))
        elif param.StorageType == DB.StorageType.Integer:
            param.Set(int(value))
        elif param.StorageType == DB.StorageType.Double:
            param.Set(float(value))
        elif param.StorageType == DB.StorageType.ElementId:
            param.Set(value)
        return True
    except:
        return False

# --- [3] UI WINDOW (Interface) ---
class SmartCopyWindow(Windows.Window):
    def __init__(self, state):
        wpf.LoadComponent(self, script.get_bundle_file('ui.xaml'))
        self.state = state
        self.next_action = None 

        self.btn_pick_source.Click += self.on_pick_source
        self.btn_pick_target.Click += self.on_pick_target
        self.btn_copy_auto.Click += self.on_copy_auto
        self.btn_copy_manual.Click += self.on_copy_manual
        self.cmb_param_type.SelectionChanged += self.on_param_type_changed

        self.refresh_ui()

    def refresh_ui(self):
        # 1. Get Elements
        source_el = doc.GetElement(self.state.source_id) if self.state.source_id else None
        target_els = []
        for eid in self.state.target_ids:
            el = doc.GetElement(eid)
            if el: target_els.append(el)

        # 2. Update Labels
        if source_el: self.lbl_source_name.Text = "Source: " + source_el.Name
        if target_els: self.lbl_target_name.Text = "Targets: {} elements".format(len(target_els))

        # 3. Determine Context (Instance vs Type)
        if self.cmb_param_type.SelectedIndex == 1:
            current_mode = "Type"
        else:
            current_mode = "Instance"
            
        src_obj = get_element_or_type(source_el, current_mode) if source_el else None
        
        tgt_obj = None
        if target_els:
             tgt_obj = get_element_or_type(target_els[0], current_mode)

        # 4. Get Parameters (Filtering ReadOnly)
        src_params = []
        if src_obj:
            src_params = sorted([p.Definition.Name for p in src_obj.Parameters if p.Definition and not p.IsReadOnly])
        
        tgt_params = []
        if tgt_obj:
            tgt_params = sorted([p.Definition.Name for p in tgt_obj.Parameters if p.Definition and not p.IsReadOnly])

        # 5. Populate Auto Match List
        if src_params and tgt_params:
            common = sorted(list(set(src_params).intersection(tgt_params)))
            self.lst_params.ItemsSource = common
            self.lst_params.SelectAll()
        else:
            self.lst_params.ItemsSource = None

        # 6. Populate Manual Dropdowns
        if target_els:
            sample = target_els[0]
            manual_params = sorted([p.Definition.Name for p in sample.Parameters if p.Definition and not p.IsReadOnly])
            self.cmb_source_param.ItemsSource = manual_params
            self.cmb_target_param.ItemsSource = manual_params
            if manual_params:
                self.cmb_source_param.SelectedIndex = 0
                self.cmb_target_param.SelectedIndex = 0

    def on_param_type_changed(self, sender, args):
        self.refresh_ui()

    def on_pick_source(self, sender, args):
        self.next_action = "pick_src"
        self.Close()

    def on_pick_target(self, sender, args):
        self.next_action = "pick_tgt"
        self.Close()

    def on_copy_auto(self, sender, args):
        if not self.state.source_id or not self.state.target_ids:
            forms.alert("Source and Targets required.")
            return
        
        self.state.selected_params_auto = [str(item) for item in self.lst_params.SelectedItems]
        self.state.mode = "auto"
        
        if self.cmb_param_type.SelectedIndex == 1:
            self.state.param_type_mode = "Type"
        else:
            self.state.param_type_mode = "Instance"

        self.next_action = "copy"
        self.Close()

    def on_copy_manual(self, sender, args):
        if not self.state.target_ids:
            forms.alert("Targets required.")
            return
        self.state.selected_param_src_manual = self.cmb_source_param.SelectedItem
        self.state.selected_param_tgt_manual = self.cmb_target_param.SelectedItem
        self.state.mode = "manual"
        self.next_action = "copy"
        self.Close()

# --- [4] MAIN LOOP (Modal Pattern) ---

app_state = ToolState()

while True:
    window = SmartCopyWindow(app_state)
    window.ShowDialog()

    if window.next_action == "pick_src":
        try:
            ref = revit.uidoc.Selection.PickObject(UI.Selection.ObjectType.Element, "Pick Source")
            if ref: app_state.source_id = ref.ElementId
        except: pass

    elif window.next_action == "pick_tgt":
        try:
            refs = revit.uidoc.Selection.PickObjects(UI.Selection.ObjectType.Element, "Pick Targets")
            if refs: app_state.target_ids = [r.ElementId for r in refs]
        except: pass

    elif window.next_action == "copy":
        t = DB.Transaction(doc, "Copy Parameters")
        t.Start()
        
        count = 0
        
        source_base = doc.GetElement(app_state.source_id) if app_state.source_id else None
        target_bases = []
        for eid in app_state.target_ids:
            el = doc.GetElement(eid)
            if el: target_bases.append(el)
        
        # LOGIC FOR AUTO COPY
        if app_state.mode == "auto":
            if source_base:
                source_obj = get_element_or_type(source_base, app_state.param_type_mode)
                
                for target_base in target_bases:
                    target_obj = get_element_or_type(target_base, app_state.param_type_mode)
                    
                    if source_obj and target_obj:
                        updated = False
                        for p_name in app_state.selected_params_auto:
                            val = get_param_value(source_obj, p_name)
                            if val is not None:
                                if set_param_value(target_obj, p_name, val):
                                    updated = True
                        if updated: count += 1

        # LOGIC FOR MANUAL COPY
        elif app_state.mode == "manual":
            p_src = app_state.selected_param_src_manual
            p_tgt = app_state.selected_param_tgt_manual
            if p_src and p_tgt:
                for target in target_bases:
                    val = get_param_value(target, p_src)
                    if val is not None:
                        if set_param_value(target, p_tgt, val):
                            count += 1
        
        t.Commit()
        forms.alert("Done! Updated {} elements.".format(count))
        break

    else:
        break

