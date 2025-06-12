import bpy
import os
import subprocess
from pathlib import Path

# --------------------------------------------------------------------------------
# PROPERTIES AND FOLDER PATHS
# --------------------------------------------------------------------------------
class FolderPathPreferences(bpy.types.AddonPreferences):
    """Paths for substance painter executable and export_folder"""
    bl_idname = __package__
    spp_exe: bpy.props.StringProperty(
        name="Substance Painter executable path",
        subtype="FILE_PATH",
        default="C:/Program Files/Adobe/Adobe Substance 3D Painter/Adobe Substance 3D Painter.exe",
    )
    export_folder: bpy.props.StringProperty(
        name="Object export folder path", subtype="DIR_PATH", default=""
    )
    def draw(self, context):
        layout = self.layout
        layout.label(
            text="Paths for Substance painter executable and export path for objects. Change according to your system"
        )
        layout.prop(self, "spp_exe")
        layout.prop(self, "export_folder")

class TextureSettings(bpy.types.PropertyGroup):
    """
    Class that handles which textures to include during the import
    from Substance Painter
    """    
    use_normal_map: bpy.props.BoolProperty(
        name="use_normal_map",
        description="Enable to use Normal Map",
        default=True,
    )
    use_bump_map: bpy.props.BoolProperty(
        name="use_bump_map",
        description="Enable to use Bump Map",
        default=False,
    )
    remove_all_unused: bpy.props.BoolProperty(
        name="Remove all unused",
        description="Enable to remove all unused image nodes, otherwise only remove on seleced material",
        default=False,
    )
    clear_work_space: bpy.props.BoolProperty(
        name="Clean workspace",
        description="Enable to remove all nodes in the material before importing textures",
        default=True,
    )

# --------------------------------------------------------------------------------
# EXPORT AND IMPORT OPERATORS
# --------------------------------------------------------------------------------

class EXPORT_OT_SubstancePainterExporter(bpy.types.Operator):
    """Class to handle the export from Blender to Substance Painter"""
    bl_idname = "export.substance_painter"
    bl_label = "Export to Substance Painter"

    def execute(self, context):
        preferences = context.preferences
        export_folder = preferences.addons[__package__].preferences.export_folder
        substance_painter_path = preferences.addons[__package__].preferences.spp_exe
        objects = context.selected_objects
        # Check if export folder path exists, if not export textures in the same folder as blend file
        if not os.path.exists(export_folder):
            export_folder = Path(bpy.path.abspath("//"))
        if not objects:
            self.report({"INFO"}, "No object selected")
            return {"CANCELLED"}
        # List to store all the export paths
        export_paths = []
        # Append the paths to the export list
        folder_name = bpy.context.active_object.name
        folder_path = Path(export_folder) / folder_name
        #make subfolders for each object and export them to substancepainter
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            export_paths = []
            for obj in objects:
                obj_folder = folder_path / obj.name
                obj_folder.mkdir(parents=True, exist_ok=True)
                export_result = self.export_object(str(obj_folder), obj)
                if export_result:
                    export_paths.append(export_result)
            if export_paths:
                self.open_substance_painter(export_paths, substance_painter_path)
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Failed to export objects with error: {str(e)}")
            return {"CANCELLED"}

    def check_material(self, obj):
        """checks if object has any materials and nodes enabled"""
        if len(obj.data.materials) == 0:
            self.report({"INFO"}, f"No material on {obj.name}, adding material")
            new_material = bpy.data.materials.new(name=f"{obj.name}_material")
            new_material.use_nodes = True
            obj.data.materials.append(new_material)
            self.report({"INFO"}, f"{obj.name} has a {obj.name}_material added to it")
        else:
            for mat in obj.data.materials:
                mat.name = obj.name+"_"+mat.name

    def export_object(self, export_folder, obj):
        """Return the fbx filepath and exports the mesh from blender to the specificed folderpath"""
        if obj.type == "MESH":
            self.check_material(obj)
            os.makedirs(export_folder, exist_ok=True)
            # Export object
            export_name = f"{obj.name}.fbx"           
            export_path = os.path.normpath(os.path.join(export_folder, export_name))
            bpy.ops.export_scene.fbx(
                filepath=export_path,
                global_scale=1.0,
                apply_unit_scale=True,
                use_selection=True,
            )
            self.report({"INFO"}, f"Exported {obj.name} to {export_path}")
            # Return the path to the export list
            return export_path
        else:
            self.report(
                {"WARNING"}, f"{obj.name} is not a mesh object, skipping mesh export."
            )
            return None

    def open_substance_painter(self, export_paths, spp_exe):
        """
        Combine all mesh filepaths into a single list of arguments through a list comprehension
        results in [SPP_exe, --mesh, mesh_path, --mesh, mesh_path, etc]
        which opens substance painter with the selected meshes
        """
        try:
            args = [spp_exe] + [
                mesh for path in export_paths for mesh in ["--mesh", path]
            ]
            subprocess.Popen(args, stdout=subprocess.PIPE, text=True)
            self.report(
                {"INFO"},
                f"Exporting: {', '.join(export_paths)}",
            )
        except Exception as e:
            self.report({"ERROR"}, f"Could not open Substance Painter: {str(e)}")

class IMPORT_OT_Textures(bpy.types.Operator):
    """Operator to handle importing textures from Substance Painter back to Blender"""
    bl_idname = "import.textures"
    bl_label = "import Textures"
    
    def execute(self, context):
        preferences = context.preferences
        export_folder_path = preferences.addons[__package__].preferences.export_folder
        objects = context.selected_objects
        parent_folder = self.folder_iteration(export_folder_path, objects)
        for obj in objects:
            if not objects:
                self.report({"INFO"}, "No object selected")
                return {"CANCELLED"}
            if obj.type != "MESH":
                continue
            if parent_folder is None:
                self.report({"INFO"}, "Folder not found for the selected object, perhaps you forgot to export the object first?")
                self.report({"INFO"}, "If you already exported the object remeber to include select the object with the same name as the folder in the export folder")
                return {"CANCELLED"}
            object_folder = os.path.join(parent_folder, obj.name)
            os.makedirs(object_folder, exist_ok=True)
            
            if not os.path.exists(object_folder) or not os.path.exists(parent_folder):
                self.report({"INFO"}, f"Folder does not exist for {obj.name}")
                continue
            try:
                if not obj.data.materials:
                    mat = bpy.data.materials.new(name=f"{obj.name}_Material")
                    mat.use_nodes = True
                    obj.data.materials.append(mat)
                for mat in obj.data.materials:
                    # Ensure the material uses nodes
                    if not mat.use_nodes:
                        mat.use_nodes = True
                    # Assign textures to the material
                    self.assign_textures(
                        mat, object_folder, context.scene.texture_settings
                    )
            except Exception as e:
                self.report({"INFO"}, f"Error assigning textures to {obj.name} with error: {str(e)}",)
                continue
        return {"FINISHED"}

    def folder_iteration(self, base_path, objects):
        '''Method to iterate through the object folder to find the parent folder containing the objects '''
        path = Path(base_path)
        # Find the parent folder containing all of the objects:
        for f in path.iterdir():
            for obj in objects:
                if obj.name == f.name:
                    return os.path.join(base_path, obj.name)
                pass

    def assign_textures(self, material, textures_folder, texture_settings):
        """
        Method to assign material and textures to the selected material,
        Takes the material, the objects texture folder and
        the users texture settings as args
        """
        node_tree = material.node_tree
        nodes = node_tree.nodes
        links = node_tree.links
        file_types = (".png", ".jpg", ".jpeg")
        node_x_displacement = 400
        # Used to reset position
        node_y_position = 400
        # Used to show what textures where assigned
        textures_assigned = []
        # Remove previous nodes to clear the workspace if the user wants it
        if texture_settings.clear_work_space:
            for node in nodes:
                nodes.remove(node)
        # check if output and bsdf_principled nodes exist
        output_node = None
        principled_node = None
        for node in nodes:
            if node.type == 'OUTPUT_MATERIAL':
                output_node = node
            elif node.type == 'BSDF_PRINCIPLED':
                principled_node = node
        # create BSDF and output node
        if not output_node:
            output_node = nodes.new(type="ShaderNodeOutputMaterial")
            output_node.location = (400, 0)
        if not principled_node:
            principled_node = nodes.new(type="ShaderNodeBsdfPrincipled")
            principled_node.location = (0, 0)
        links.new(principled_node.outputs["BSDF"], output_node.inputs["Surface"])
        # Normal and displacement rereferences
        normal_node_ref = None
        displace_node_ref = None
        # Iterates through the texture folder of an object and assigns textures to the material:
        for filename in os.listdir(textures_folder):
            if filename.lower().endswith(file_types):
                if material.name not in filename:
                    continue
                texture_type = self.get_texture_type(filename)
                filepath = os.path.join(textures_folder, filename)
                if texture_type == "Base Color":
                    image_node = self.create_image_node(nodes,node_y_position,filepath)
                    if texture_settings.clear_work_space:
                        links.new(
                            image_node.outputs["Color"],
                            principled_node.inputs["Base Color"],
                        )
                    node_y_position -= 400
                    textures_assigned.append(filename)
                elif texture_type == "Roughness":
                    image_node = self.create_image_node(nodes,node_y_position,filepath)
                    if texture_settings.clear_work_space:
                        links.new(image_node.outputs["Color"], principled_node.inputs["Roughness"])
                    image_node.image.colorspace_settings.name = "Non-Color"
                    node_y_position -= 400
                    textures_assigned.append(filename)
                elif texture_type =="Displacement" and texture_settings.use_bump_map:
                    image_node = self.create_image_node(nodes,node_y_position,filepath)
                    image_node.image.colorspace_settings.name = "Non-Color"
                    if texture_settings.use_normal_map:
                        normal_node_ref = image_node
                    else:
                        bump_node = nodes.new(type="ShaderNodeBump")
                        bump_node.location = (image_node.location.x +node_x_displacement,node_y_position)
                        
                        links.new(image_node.outputs["Color"],bump_node.inputs["Height"])
                        if texture_settings.clear_work_space:
                            links.new(bump_node.outputs["Normal"],principled_node.inputs["Normal"])   
                    node_y_position -= 400
                    textures_assigned.append(filename)
                elif texture_type =="Normal" and texture_settings.use_normal_map:
                    image_node = self.create_image_node(nodes,node_y_position,filepath)
                    image_node.image.colorspace_settings.name = "Non-Color"
                    if texture_settings.use_bump_map:
                        displace_node_ref = image_node
                    else:
                        normal_map_node = nodes.new(type="ShaderNodeNormalMap")
                        normal_map_node.location = (image_node.location.x +node_x_displacement,node_y_position)
                        links.new(image_node.outputs["Color"],normal_map_node.inputs["Color"])
                        if texture_settings.clear_work_space:
                            links.new(normal_map_node.outputs["Normal"],principled_node.inputs["Normal"])   
                    node_y_position -= 400
                    textures_assigned.append(filename)
                elif texture_type == "Metallic":
                    image_node = self.create_image_node(nodes,node_y_position,filepath)
                    image_node.image.colorspace_settings.name = "Non-Color"
                    if texture_settings.clear_work_space:
                        links.new(
                            image_node.outputs["Color"], principled_node.inputs["Metallic"]
                        )
                    node_y_position -= 400
                    textures_assigned.append(filename)                   
        if texture_settings.use_bump_map and texture_settings.use_normal_map:
            bump_normal_node = nodes.new(type="ShaderNodeBump")
            bump_normal_node.location = ( displace_node_ref.location.x + node_x_displacement,(displace_node_ref.location.y-normal_node_ref.location.y)/2.0)
            links.new(displace_node_ref.outputs["Color"], bump_normal_node.inputs["Normal"])
            links.new(normal_node_ref.outputs["Color"], bump_normal_node.inputs["Height"])
            if texture_settings.clear_work_space:
                links.new(bump_normal_node.outputs["Normal"], principled_node.inputs["Normal"])
        self.report({"INFO"},f"{str(len(textures_assigned))} textures were imported {str(textures_assigned)}",)
    
    def get_texture_type(self, filename):
        """Returns the texture by type"""
        if "diffuse" in filename.lower() or "basecolor" in filename.lower():
            return "Base Color"
        elif "roughness" in filename.lower():
            return "Roughness"
        elif "normal" in filename.lower():
            return "Normal"
        elif "displacement" in filename.lower():
            return "Displacement"
        elif "metallic" in filename.lower():
            return "Metallic"
        else:
            return None
          
    def create_image_node(self,nodes,node_y_position,filepath):
        '''Creates an image node and loads a texture to it'''
        image_node = nodes.new(type="ShaderNodeTexImage")
        image_node.location = (-800, node_y_position)
        image_node.image = bpy.data.images.load(filepath)
        return image_node
    
# --------------------------------------------------------------------------------
# UTILITY OPERATORS
# --------------------------------------------------------------------------------

class REMOVE_OT_UNUSED_TEXTURES(bpy.types.Operator):
    """Removes any unused image texture nodes in the entire scene or for the selected material only"""
    bl_idname = "remove.unusedtextures"
    bl_label = "Remove Unused Textures"

    def execute(self, context):
        obj = context.active_object
        remove_all = context.scene.texture_settings.remove_all_unused
        # Remove all unused texture nodes on all materials in the scene
        if remove_all:
            for material in bpy.data.materials:
                if material.use_nodes:
                    self.remove_nodes(material)
                    self.realign_nodes(material.node_tree.nodes)
        # Remove unused texture nodes from the active object's material only
        else:
            if not obj or not obj.data.materials:
                self.report(
                    {"WARNING"}, "No object selected or object has no materials."
                )
                return {"CANCELLED"}
            material = obj.active_material
            if material and material.use_nodes:
                self.remove_nodes(material)
                self.realign_nodes(material.node_tree.nodes)

        return {"FINISHED"}

    def remove_nodes(self, material):
        """Removes unused ShaderNodeTexImage nodes in a material"""
        try:
            mat_nodes = material.node_tree.nodes
            for node in mat_nodes:
                if isinstance(node, bpy.types.ShaderNodeTexImage):
                    if len(node.outputs[0].links) == 0:
                        mat_nodes.remove(node)
        except Exception as e:
            self.report({"INFO"}, f"Failed to remove nodes with error: {e}")

    def realign_nodes(self, nodes):
        """Realigns the remaining texture nodes for better structure"""
        y_offset = 0
        node_spacing = 300
        for node in nodes:
            node.location.y = y_offset
            y_offset -= node_spacing

class OPEN_OT_FBXFolder(bpy.types.Operator):
    """Opens the FBX Export Folder"""
    bl_idname = "open.fbx_folder"
    bl_label = "Open FBX Folder"

    def execute(self, context):
        preferences = context.preferences
        export_folder = preferences.addons[__package__].preferences.export_folder
        try:
            os.startfile(export_folder)
            self.report({"INFO"}, f"Opened folder: {export_folder}")
        except Exception as e:
            self.report({"ERROR"}, f"Failed to open folder, the error: {str(e)}")
        return {"FINISHED"}

# --------------------------------------------------------------------------------
# UI PANELs
# --------------------------------------------------------------------------------

class VIEW3D_PT_QuickExporter_ExportImport(bpy.types.Panel):
    """Export/Import Panel for the addon"""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "B2SP Linker"
    bl_label = "Export/Import Textures"
    bl_icon = "EXPORT"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator(
            EXPORT_OT_SubstancePainterExporter.bl_idname,
            text="Export to Substance Painter",
            icon="EXPORT",
        )
        col.operator(
            IMPORT_OT_Textures.bl_idname,
            text="Import from Substance Painter",
            icon="IMPORT",
        )
        col.operator(
            OPEN_OT_FBXFolder.bl_idname, text="Open Object folder", icon="FILE_FOLDER"
        )

class VIEW3D_PT_QuickExporter_ImportSettings(bpy.types.Panel):
    """Texture Import Settings Panel for the addon"""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "B2SP Linker"
    bl_label = "Import Settings"
    bl_icon = "SETTINGS"

    def draw(self, context):
        layout = self.layout
        texture_settings = context.scene.texture_settings
        col = layout.column()
        col.prop(texture_settings, "use_normal_map", text="Normal Map")
        col.prop(texture_settings, "use_bump_map", text="Bump Map")
        col.prop(texture_settings, "clear_work_space", text="Clear Workspace")

class VIEW3D_PT_QuickExporter_Cleanup(bpy.types.Panel):
    """Cleanup Functions Panel for the addon"""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "B2SP Linker"
    bl_label = "Cleanup Functions"

    def draw(self, context):
        layout = self.layout
        texture_settings = context.scene.texture_settings
        col = layout.column()
        col.prop(texture_settings, "remove_all_unused", text="Remove all unused")
        col.operator(
            REMOVE_OT_UNUSED_TEXTURES.bl_idname,
            text="Remove unused image textures",
            icon="TRASH",
        )

# --------------------------------------------------------------------------------
# REGISTERING CLASSES
# --------------------------------------------------------------------------------
classes = (
    FolderPathPreferences,
    TextureSettings,
    VIEW3D_PT_QuickExporter_ExportImport,
    VIEW3D_PT_QuickExporter_ImportSettings,
    EXPORT_OT_SubstancePainterExporter,
    VIEW3D_PT_QuickExporter_Cleanup,
    OPEN_OT_FBXFolder,
    IMPORT_OT_Textures,
    REMOVE_OT_UNUSED_TEXTURES,
)

# Register and unregister classes
def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.texture_settings = bpy.props.PointerProperty(type=TextureSettings)

def unregister():
    del bpy.types.Scene.texture_settings
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __package__ == "__main__":
    register()

    

