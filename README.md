# Blender to Substance Painter (B2SP) Linker

A Blender addon which simplifies exports and imports between Blender and Substance Painter.

## Developed on:
- **Python**: 3.12.7  
- **Blender Version**: 4.4.4
- **Windows 10**

Other Python and Blender version should work but I have not tested then myself.


## Features

- **Export meshes to Substance Painter**: Export your Blender meshes and materials to Substance Painter for texturing.
- **Import textures back into Blender**: Import textures created in Substance Painter back into Blender for use in the scene.
- **Texture import options**: Choose which textures (e.g., Normal, bump, or height) to import back into Blender.
- **Remove unused image nodes**: Clean up the material nodes by removing any unused image textures, either in the entire scene or for a selected material only.
- **Open export folder in Blender**: Quickly open the export folder from Blender's file browser for easy access.

## Installation

1. Download the addon `.zip` file.  
2. Open Blender and go to `Edit > Preferences > Add-ons`.  
3. Click on `Install`, and select the downloaded `.zip` file.  
4. Enable the addon by checking the box next to its name.

## Usage

### Set paths

1. **Set the Substance Painter executable**:  
   In the preferences tab of the addon, set the executable for Substance Painter. Example:  
   `C:\Program Files\Adobe\Adobe Substance 3D Painter\Adobe Substance 3D Painter.exe`.  
   The addon will not work otherwise.

2. **Set the export folder path**:  
   In the preferences tab of the addon, choose a location where exports of objects will occur.  
   If none is selected, it will default to the same location as the `.blend` file.

3. **Enable Node Wrangler**:  
   Make sure that the Node Wrangler addon is enabled, as this addon makes use of it.

### Exporting Meshes to Substance Painter

1. **Prepare the mesh**:  
   - Ensure your mesh has proper UVs and materials set up in Blender.  
   - Make sure that all materials have unique names, as otherwise this can cause issues.
   - If the mesh already has materials attached to it, then the name of the object will be added as a prefix to the material. 

2. **Export the mesh**:  
   - Select the objects you want to export to Substance Painter.  
   - Click "Export to Substance Painter" to send the mesh(es) to Substance Painter.  
   - The addon will automatically add materials to the objects if none exists.  
   - UV maps must be created before exporting.
   - The folder containing the exported objects will have the same name as the currently active object in the export selection  
   - Objects will be saved in the export folder.

   - The structure after exporting a mesh named "Cube":
     ```
     ├── EXPORT_FOLDER_NAME/
     │   └── Cube
     │       ├──Cube
                └── Cube.fbx
     ```
      - The structure after exporting multiple meshes with the active mesh being named "Cube":
     ```
      ├── EXPORT_FOLDER_NAME/
      │ 
      └── Cube
      	 ├──Cube
      	    └── Cube.fbx
      	 ├──Cube2
      	    └── Cube2.fbx
     ```
The textures are imported into the corresponding object and resides besides the .fbx file. 


### Exporting Textures from Substance Painter

After texturing in Substance Painter, export the textures (File → Export Textures) into the mesh's texture folder named `MESHNAME_textures`. Make sure to set the output template in export panel is set to "Blender (Principled BSDF)".

### Importing Textures Back

After saving the textures, select the object you want to add textures to and press the "Import from Substance Painter" button. Make sure that the object which has the same name as the folder containing the textures is selected. 


### Texture settings

When importing the textures there are three settings which can be checked. 

1. **Use normal maps**:
   If active, normal maps will be imported and automatically connected to the Principled BSDF for the object through the use of a image texture and a normal map.

2. **Use bump maps**:  
   If active, bump maps will be imported and automatically connected to the Principled BSDF for the object through the use of a image texture and a bump map.

If both normal maps and bump maps are used then both will be imported and then connected to the Principled BSDF for the object through the use a bump node. 

3. **Clear workspace**:  
- Depending on whether the "Clear workspace" option is enabled:
  - If enabled, the addon will remove all nodes in for the selected material and then create a new Principled BSDF with the imported textures connected
  - If disabled, the addon will import the textures without removing any previous node in the material. 
## Removing Unused Image Nodes

- Depending on whether the "Remove all unused" option is enabled:
  - If enabled, the addon will remove any texture node that is not connected.
  - If disabled, the addon will only remove the texture nodes that are not connected **on the selected material** only.

- Click the "Remove unused image textures" button to perform the cleanup.

### Opening the Export Folder

1. **Access the export folder**:  
   Open the export folder for faster access to objects and textures.



### Notes about Substance Painter

Exporting each material into the correct folder can be tedious and thus I have created a small plugin within Substance Painter which allows automatic exports the texture to each folder: 
``` python 
import os
from PySide2 import QtWidgets, QtCore
import substance_painter.ui
import substance_painter.export
import substance_painter.project
import substance_painter.textureset
import substance_painter.resource
plugin_widgets = []
export_helper = None

#Split into two classes: one for logic and one for UI
class B2SPHelper:
    def __init__(self):
        self.export_path = ""
    def set_export_path(self, label_widget):
        path = QtWidgets.QFileDialog.getExistingDirectory(None, "Select Export Folder")
        if path:
            self.export_path = path
            label_widget.setText(f"Export Path: {path}")
        else:
            label_widget.setText("Export Path: Not set")
            print("No folder path selected.")

    def get_export_path(self):
        return self.export_path
        
    def export_textures(self):
        if not substance_painter.project.is_open():
            print("No project open.")
            return

        if not self.export_path:
            print("Export path is not set.")
            return

        export_preset = substance_painter.resource.ResourceID(
            context="starter_assets", name="Blender (Principled BSDF)"
        )

        for stack in substance_painter.textureset.all_texture_sets():
            #get the object suffix so that the correct folder is used
            object_name = stack.name().split('_')[0]
            print(f" new name {object_name}")
            
            object_path = os.path.join(self.export_path, object_name)
            if not os.path.exists(object_path):
               object_path = self.export_path                 
            print(f"Exporting: {stack.name()} to {object_path}")

            config = {
                "exportShaderParams": False,
                "exportPath": object_path,
                "exportList": [{"rootPath": str(stack.name())}],
                "exportPresets": [{"name": "default", "maps": []}],
                "defaultExportPreset": export_preset.url(),
                "exportParameters": [{"parameters": {"paddingAlgorithm": "infinite"}}]
            }

            substance_painter.export.export_project_textures(config)


class B2SPUI(QtWidgets.QWidget):
    '''UI for helper, inherits from logic class'''
    def __init__(self, export_helper_instance):
        super().__init__()
        self.helper = export_helper_instance
        self.setWindowTitle("B2SP Exporter")
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()
        self.path_label = QtWidgets.QLabel("Export Path: Not set")
        #Buttons
        set_path_btn = QtWidgets.QPushButton("Set Export Path")
        export_btn = QtWidgets.QPushButton("Export Textures")
        #actions for buttons
        set_path_btn.clicked.connect(lambda: self.helper.set_export_path(self.path_label))
        export_btn.clicked.connect(self.helper.export_textures)
        #add widgets
        layout.addWidget(self.path_label)
        layout.addWidget(set_path_btn)
        layout.addWidget(export_btn)
        self.setLayout(layout)

'''Start and close functions for the plugin'''
def start_plugin():
    global export_helper
    #create instance and activate UI_widget
    export_helper = B2SPHelper()

    ui_widget = B2SPUI(export_helper)
    substance_painter.ui.add_dock_widget(ui_widget)

    plugin_widgets.append(ui_widget)


def close_plugin():
    for widget in plugin_widgets:
        substance_painter.ui.delete_ui_element(widget)
    plugin_widgets.clear()


if __name__ == "__main__":
    start_plugin()
```

   
