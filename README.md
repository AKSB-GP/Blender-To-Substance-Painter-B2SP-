# Blender to Substance Painter (B2SP) Linker

A Blender addon which simplifies exports and imports between Blender and Substance Painter.

## Developed on:
- **Python**: 3.12.7  
- **Blender Version**: 4.2.3
- **Windows 10**

Other Python and Blender version should work but have not been tested on.


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
                ├── Cube.fbx
     ```
      - The structure after exporting multiple meshes with the active mesh being named "Cube":
     ```
     ├── EXPORT_FOLDER_NAME/
     │   └── Cube
     │       ├──Cube
                ├── Cube.fbx
                ├── Cube1.fbx
                ├── Cube2.fbx
     ```



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
