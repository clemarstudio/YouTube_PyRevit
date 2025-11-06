from pyrevit import revit, DB, script
import wpf
from System import Windows
from System.Collections.Generic import List

# Get document handles
uidoc = revit.uidoc
doc = revit.doc

# Define allowed categories
ALLOWED_CATEGORIES = [
    DB.BuiltInCategory.OST_Walls,
    DB.BuiltInCategory.OST_Floors,
    DB.BuiltInCategory.OST_StructuralColumns,
    DB.BuiltInCategory.OST_StructuralFraming,
    DB.BuiltInCategory.OST_Doors,
    DB.BuiltInCategory.OST_Windows,
    DB.BuiltInCategory.OST_Roofs,
    DB.BuiltInCategory.OST_Ceilings
]


def get_category_name(category_type):
    """Get category name from BuiltInCategory"""
    category = DB.Category.GetCategory(doc, category_type)
    return category.Name if category else str(category_type)


def get_parameter_value_string(param):
    """Convert parameter value to string"""
    if param.StorageType == DB.StorageType.String:
        return param.AsString() or ""
    elif param.StorageType == DB.StorageType.Integer:
        return str(param.AsInteger())
    elif param.StorageType == DB.StorageType.Double:
        return str(param.AsDouble())
    else:
        return param.AsValueString() or ""


def load_parameters_for_category(category_type, sample_elements):
    """Load all parameters from elements in a category"""
    parameters_by_name = {}
    
    for element in sample_elements[:100]:  # Limit to first 100 for performance
        for param in element.Parameters:
            if param and param.StorageType != DB.StorageType.None:
                parameter_name = param.Definition.Name
                if parameter_name not in parameters_by_name:
                    parameters_by_name[parameter_name] = set()
                
                parameter_value = get_parameter_value_string(param)
                if parameter_value:
                    parameters_by_name[parameter_name].add(parameter_value)
    
    # Convert to list of tuples (parameter_name, parameter_values)
    parameter_list = []
    for parameter_name in sorted(parameters_by_name.keys()):
        parameter_values = sorted(list(parameters_by_name[parameter_name]))
        parameter_list.append((parameter_name, parameter_values))
    
    return parameter_list


def load_parameters_all_categories():
    """Load parameters from all allowed categories"""
    parameters_by_name = {}
    
    for category_type in ALLOWED_CATEGORIES:
        collector = DB.FilteredElementCollector(doc).OfCategory(category_type).WhereElementIsNotElementType()
        collected_elements = list(collector.ToElements())
        sample_elements = collected_elements[:50]  # Limit to first 50 for performance
        
        for element in sample_elements:
            for param in element.Parameters:
                if param and param.StorageType != DB.StorageType.None:
                    parameter_name = param.Definition.Name
                    if parameter_name not in parameters_by_name:
                        parameters_by_name[parameter_name] = set()
                    
                    parameter_value = get_parameter_value_string(param)
                    if parameter_value:
                        parameters_by_name[parameter_name].add(parameter_value)
    
    # Convert to list of tuples (parameter_name, parameter_values)
    parameter_list = []
    for parameter_name in sorted(parameters_by_name.keys()):
        parameter_values = sorted(list(parameters_by_name[parameter_name]))
        parameter_list.append((parameter_name, parameter_values))
    
    return parameter_list


def get_elements_for_filter(category_type, parameter_name, parameter_value):
    """Get elements matching filter criteria"""
    if category_type is None:
        # "Any category" - search all allowed categories
        collected_elements = []
        for allowed_category in ALLOWED_CATEGORIES:
            category_elements = list(DB.FilteredElementCollector(doc)
                                    .OfCategory(allowed_category)
                                    .WhereElementIsNotElementType()
                                    .ToElements())
            collected_elements.extend(category_elements)
    else:
        # Specific category
        collected_elements = list(DB.FilteredElementCollector(doc)
                                 .OfCategory(category_type)
                                 .WhereElementIsNotElementType()
                                 .ToElements())
    
    # Filter by parameter
    matching_elements = []
    for element in collected_elements:
        param = element.LookupParameter(parameter_name)
        if param:
            element_value = get_parameter_value_string(param)
            if element_value == parameter_value:
                matching_elements.append(element)
    
    return matching_elements


class MyWindow(Windows.Window):
    
    def __init__(self):
        wpf.LoadComponent(self, script.get_bundle_file('ui.xaml'))
        # Initialize parameter data dictionaries for filter 1 and filter 2
        self.filter1_parameters = {}
        self.filter2_parameters = {}
        self.load_categories()
        self.setup_events()
    
    def load_categories(self):
        """Load allowed categories into ComboBoxes"""
        category_names = []
        for category_type in ALLOWED_CATEGORIES:
            category = DB.Category.GetCategory(doc, category_type)
            if category:
                # Check if category has elements
                collector = DB.FilteredElementCollector(doc).OfCategory(category_type).WhereElementIsNotElementType()
                if collector.GetElementCount() > 0:
                    category_names.append(category.Name)
        
        self.CbCat1.ItemsSource = category_names
        self.CbCat2.ItemsSource = category_names
    
    def setup_events(self):
        """Setup event handlers"""
        self.ChkAny1.Checked += self.on_any1_checked
        self.ChkAny1.Unchecked += self.on_any1_unchecked
        self.CbCat1.SelectionChanged += self.on_cat1_changed
        self.CbParam1.SelectionChanged += self.on_param1_changed
        
        self.ChkAny2.Checked += self.on_any2_checked
        self.ChkAny2.Unchecked += self.on_any2_unchecked
        self.CbCat2.SelectionChanged += self.on_cat2_changed
        self.CbParam2.SelectionChanged += self.on_param2_changed
        
        self.BtnClear.Click += self.on_clear
        self.BtnSelect.Click += self.on_select
    
    def get_category_type_from_name(self, category_name):
        """Get BuiltInCategory from category name"""
        for category_type in ALLOWED_CATEGORIES:
            category = DB.Category.GetCategory(doc, category_type)
            if category and category.Name == category_name:
                return category_type
        return None
    
    def on_any1_checked(self, sender, args):
        """Handle Any category checkbox 1 checked"""
        self.CbCat1.IsEnabled = False
        self.CbCat1.SelectedItem = None
        self.load_all_parameters1()
    
    def on_any1_unchecked(self, sender, args):
        """Handle Any category checkbox 1 unchecked"""
        self.CbCat1.IsEnabled = True
        if self.CbCat1.SelectedItem:
            self.on_cat1_changed(None, None)
    
    def on_any2_checked(self, sender, args):
        """Handle Any category checkbox 2 checked"""
        self.CbCat2.IsEnabled = False
        self.CbCat2.SelectedItem = None
        self.load_all_parameters2()
    
    def on_any2_unchecked(self, sender, args):
        """Handle Any category checkbox 2 unchecked"""
        self.CbCat2.IsEnabled = True
        if self.CbCat2.SelectedItem:
            self.on_cat2_changed(None, None)
    
    def load_all_parameters1(self):
        """Load parameters from all allowed categories for filter 1"""
        parameter_list = load_parameters_all_categories()
        parameter_names = [param_name for param_name, param_values in parameter_list]
        self.CbParam1.ItemsSource = parameter_names
        self.CbParam1.IsEnabled = True
        self.filter1_parameters = {param_name: param_values for param_name, param_values in parameter_list}
        self.CbValue1.ItemsSource = None
        self.CbValue1.IsEnabled = False
    
    def load_all_parameters2(self):
        """Load parameters from all allowed categories for filter 2"""
        parameter_list = load_parameters_all_categories()
        parameter_names = [param_name for param_name, param_values in parameter_list]
        self.CbParam2.ItemsSource = parameter_names
        self.CbParam2.IsEnabled = True
        self.filter2_parameters = {param_name: param_values for param_name, param_values in parameter_list}
        self.CbValue2.ItemsSource = None
        self.CbValue2.IsEnabled = False
    
    def on_cat1_changed(self, sender, args):
        """Handle category 1 selection changed"""
        if self.ChkAny1.IsChecked:
            return
        
        category_name = self.CbCat1.SelectedItem
        if not category_name:
            self.CbParam1.ItemsSource = None
            self.CbParam1.IsEnabled = False
            self.CbValue1.ItemsSource = None
            self.CbValue1.IsEnabled = False
            return
        
        category_type = self.get_category_type_from_name(category_name)
        if category_type:
            collector = DB.FilteredElementCollector(doc).OfCategory(category_type).WhereElementIsNotElementType()
            collected_elements = list(collector.ToElements())
            sample_elements = collected_elements[:100]  # Limit to first 100 for performance
            parameter_list = load_parameters_for_category(category_type, sample_elements)
            parameter_names = [param_name for param_name, param_values in parameter_list]
            self.CbParam1.ItemsSource = parameter_names
            self.CbParam1.IsEnabled = True
            self.filter1_parameters = {param_name: param_values for param_name, param_values in parameter_list}
            self.CbValue1.ItemsSource = None
            self.CbValue1.IsEnabled = False
    
    def on_cat2_changed(self, sender, args):
        """Handle category 2 selection changed"""
        if self.ChkAny2.IsChecked:
            return
        
        category_name = self.CbCat2.SelectedItem
        if not category_name:
            self.CbParam2.ItemsSource = None
            self.CbParam2.IsEnabled = False
            self.CbValue2.ItemsSource = None
            self.CbValue2.IsEnabled = False
            return
        
        category_type = self.get_category_type_from_name(category_name)
        if category_type:
            collector = DB.FilteredElementCollector(doc).OfCategory(category_type).WhereElementIsNotElementType()
            collected_elements = list(collector.ToElements())
            sample_elements = collected_elements[:100]  # Limit to first 100 for performance
            parameter_list = load_parameters_for_category(category_type, sample_elements)
            parameter_names = [param_name for param_name, param_values in parameter_list]
            self.CbParam2.ItemsSource = parameter_names
            self.CbParam2.IsEnabled = True
            self.filter2_parameters = {param_name: param_values for param_name, param_values in parameter_list}
            self.CbValue2.ItemsSource = None
            self.CbValue2.IsEnabled = False
    
    def on_param1_changed(self, sender, args):
        """Handle parameter 1 selection changed"""
        parameter_name = self.CbParam1.SelectedItem
        if parameter_name and hasattr(self, 'filter1_parameters'):
            parameter_values = self.filter1_parameters.get(parameter_name, [])
            self.CbValue1.ItemsSource = parameter_values
            self.CbValue1.IsEnabled = True
        else:
            self.CbValue1.ItemsSource = None
            self.CbValue1.IsEnabled = False
    
    def on_param2_changed(self, sender, args):
        """Handle parameter 2 selection changed"""
        parameter_name = self.CbParam2.SelectedItem
        if parameter_name and hasattr(self, 'filter2_parameters'):
            parameter_values = self.filter2_parameters.get(parameter_name, [])
            self.CbValue2.ItemsSource = parameter_values
            self.CbValue2.IsEnabled = True
        else:
            self.CbValue2.ItemsSource = None
            self.CbValue2.IsEnabled = False
    
    def on_clear(self, sender, args):
        """Clear all filters"""
        self.ChkAny1.IsChecked = False
        self.CbCat1.SelectedItem = None
        self.CbParam1.SelectedItem = None
        self.CbValue1.Text = ""
        self.CbCat1.IsEnabled = True
        
        self.ChkAny2.IsChecked = False
        self.CbCat2.SelectedItem = None
        self.CbParam2.SelectedItem = None
        self.CbValue2.Text = ""
        self.CbCat2.IsEnabled = True
        
        self.ChkUseOr.IsChecked = False
    
    def on_select(self, sender, args):
        """Select elements based on filters"""
        # Get filter 1 settings
        if not self.CbParam1.SelectedItem:
            return
        
        parameter1_name = self.CbParam1.SelectedItem
        parameter1_value = self.CbValue1.SelectedItem or self.CbValue1.Text
        
        if not parameter1_value:
            return
        
        # Get category for filter 1
        selected_category1 = None
        if not self.ChkAny1.IsChecked:
            category1_name = self.CbCat1.SelectedItem
            if category1_name:
                selected_category1 = self.get_category_type_from_name(category1_name)
        
        # Get elements matching filter 1
        matching_elements_filter1 = get_elements_for_filter(selected_category1, parameter1_name, parameter1_value)
        matching_ids_filter1 = {element.Id for element in matching_elements_filter1}
        
        # Get filter 2 if configured
        has_second_filter = False
        matching_elements_filter2 = []
        matching_ids_filter2 = set()
        
        if self.CbParam2.SelectedItem:
            parameter2_name = self.CbParam2.SelectedItem
            parameter2_value = self.CbValue2.SelectedItem or self.CbValue2.Text
            
            if parameter2_value:
                has_second_filter = True
                selected_category2 = None
                if not self.ChkAny2.IsChecked:
                    category2_name = self.CbCat2.SelectedItem
                    if category2_name:
                        selected_category2 = self.get_category_type_from_name(category2_name)
                
                matching_elements_filter2 = get_elements_for_filter(selected_category2, parameter2_name, parameter2_value)
                matching_ids_filter2 = {element.Id for element in matching_elements_filter2}
        
        # Combine filters
        if has_second_filter:
            combine_with_or = self.ChkUseOr.IsChecked
            if combine_with_or:
                # OR: union of both filters (elements that match filter 1 OR filter 2)
                selected_element_ids = matching_ids_filter1.union(matching_ids_filter2)
            else:
                # AND: intersection of both filters (elements that match filter 1 AND filter 2)
                selected_element_ids = matching_ids_filter1.intersection(matching_ids_filter2)
        else:
            selected_element_ids = matching_ids_filter1
        
        # Select elements in Revit
        if selected_element_ids:
            element_id_collection = List[DB.ElementId](selected_element_ids)
            uidoc.Selection.SetElementIds(element_id_collection)
            print("Selected {} element(s)".format(len(selected_element_ids)))
        else:
            print("No elements found matching the criteria")


# Show the window
MyWindow().ShowDialog()

