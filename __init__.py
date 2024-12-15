import bpy
import os
import subprocess

bl_info = {
    "name": "B2SP Linker",
    "description": "A addon for improving workflow between Blender and Substance painter. Adds exporting and importing to substance painter via blender",
    "author": "Alexander Kazakov",
    "version": (1, 0),
    "blender": (4, 2, 3),
    "location": "View3D > UI > Tools",
    "warning": "",
    "doc_url": "https://github.com/AKSB-GP/BlendertoSubstanceexporter",
    "tracker_url": "TBA",
    "support": "COMMUNITY",
    "category": "Import-Export",
}

# --------------------------------------------------------------------------------
# PROPERTIES
# --------------------------------------------------------------------------------


class texture_settings(bpy.types.PropertyGroup):
    """
    Class that handles which textures to include during the import
    from Substance Painter
    """

    use_normal_map: bpy.props.BoolProperty(
        name="use_normal_map",
        description="Enable to use Normal Map",
        default=True,
    )
    use_height_map: bpy.props.BoolProperty(
        name="use_height_map",
        description="Enable to use Height Map",
        default=False,
    )
    use_bump_map: bpy.props.BoolProperty(
        name="use_bump_map",
        description="Enable to use Bump Map",
        default=False,
    )


# --------------------------------------------------------------------------------
# EXPORT AND IMPORT OPERATORS
# --------------------------------------------------------------------------------


class EXPORT_OT_SubstancePainterExporter(bpy.types.Operator):
    """
    Class to handle the export from Blender to Substance Painter
    """

    bl_idname = "export.substance_painter"
    bl_label = "Export to Substance Painter"

    # Base paths
    export_folder = os.path.normpath("C:/Substancepainter/FBX")

    substance_painter_path = os.path.normpath(
        "C:/Program Files/Adobe/Adobe Substance 3D Painter/Adobe Substance 3D Painter.exe"
    )

    def execute(self, context):
        # Ensure export folder exists
        if not os.path.exists(self.export_folder):
            os.makedirs(self.export_folder)

        # Get selected objects
        objects = context.selected_objects
        if not objects:
            self.report({"WARNING"}, "No object selected")
            return {"CANCELLED"}

        # List to store the export paths
        export_paths = []

        # Export each object 
        try:
            for obj in objects:
                if self.export_object(obj):
                    export_paths.append(self.export_object(obj))
            # If there are export paths, open Substance Painter with the objects
            if export_paths:
                self.open_substance_painter(export_paths)
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to export objects, the error: {str(e)}")
            return {"CANCELLED"}

    def check_material(self, obj):
        """checks if object has any materials and nodes"""
        if len(obj.data.materials) == 0:
            self.report({"INFO"},f"No material on {obj.name}, creating new one",)
            new_material = bpy.data.materials.new(name=f"{obj.name}_material")
            new_material.use_nodes = True
            obj.data.materials.append(new_material)
            self.report({"INFO"},f"{obj.name} has a {obj.name}_material added to it",)
        else:
            self.report({"INFO"}, f"{obj.name} already has a material")

    def export_object(self, obj):
        """
        Return the fbx filepath and exports the mesh from blender to teh specificed folderpath
        """
        if obj.type == "MESH":
            self.check_material(obj)
            object_folder = os.path.join(self.export_folder, obj.name)
            os.makedirs(object_folder, exist_ok=True)

            texture_folder_name = f"{obj.name}_textures"
            texture_folder = os.path.join(object_folder, texture_folder_name)
            os.makedirs(texture_folder, exist_ok=True)

            export_name = f"{obj.name}.fbx"
            export_path = os.path.normpath(os.path.join(object_folder, export_name))

            bpy.ops.export_scene.fbx(
                filepath=export_path,
                global_scale=1.0,
                apply_unit_scale=True,
                use_selection=True,
            )
            self.report({"INFO"}, f"Exported {obj.name} to {export_path}")
            return export_path
        else:
            self.report({"WARNING"}, f"{obj.name} is not a mesh object, skipping mesh check.",)
            return None

    def open_substance_painter(self, export_paths):
        """
        Combine all mesh filepaths into a single list of arguments through a list comprehension
        results in [SP_exe, --mesh, mesh_path, --mesh, mesh_path, etc]
        which opens substance painter with the selected meshes
        """
        try:
            args = [self.substance_painter_path] + [
                mesh for path in export_paths for mesh in ["--mesh", path]
            ]
            subprocess.Popen(args, stdout=subprocess.PIPE, text=True)
            self.report({"INFO"},f"Trying to open Substance Painter with FBX files: {', '.join(export_paths)}",)
        except Exception as e:
            self.report({"ERROR"}, f"Could not open Substance Painter: {str(e)}")


class IMPORT_OT_Textures(bpy.types.Operator):
    """
    Operator to handle importing textures from Substance Painter back to Blender
    """

    bl_idname = "import.textures"
    bl_label = "import Textures"

    def execute(self, context):
        # Get active object and its texture folder
        obj = bpy.context.active_object
        textures_folder = os.path.join(
            os.path.normpath("C:/Substancepainter/FBX"),
            obj.name,
            f"{obj.name}_textures",)

        try:
            # Validate selection
            self.report({"INFO"},f"Texture folder does not exist for {str(textures_folder)}",)
            if not textures_folder:
                self.report({"INFO"},f"Texture folder does not exist for {str(obj.name)}",)
            if not obj or obj.type != "MESH":
                self.report({"INFO"}, "Object is not a mesh or no object is selected")
            if not material.use_nodes:
                material.use_nodes = True
            if not obj.data.materials:
                mat = bpy.data.materials.new(new=f"{obj.name}_Material")
                mat.use_nodes = True
                obj.data.materials.append(mat)
            material = obj.data.materials[0]

            # Assign textures to material
            self.assign_textures(material, textures_folder, context.scene.texture_settings)
            return {"FINISHED"}
        except Exception as e:
            self.report({"INFO"},f"Texture folder does not exist for {str(obj.name)}",)
            return {"CANCELLED"}

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
        #used to show what textures were assigned for the user
        textures_assigned = []
        
        # Remove previous nodes to clear the workspace
        for node in nodes:
            nodes.remove(node)

        # create BSDF and output node
        output_node = nodes.new(type="ShaderNodeOutputMaterial")
        output_node.location = (400, 0)
        principled_node = nodes.new(type="ShaderNodeBsdfPrincipled")
        principled_node.location = (0, 0)
        links.new(principled_node.outputs["BSDF"], output_node.inputs["Surface"])

        # assign textures to material:
        for index, filename in enumerate(os.listdir(textures_folder)):
            # check filetypes and join them
            if filename.lower().endswith(file_types):
                texture_type = self.get_texture_type(filename)
                filepath = os.path.join(textures_folder, filename)
                textures_assigned.append(filename)
                # Create an image node and apply texture
                image_node = nodes.new(type="ShaderNodeTexImage")
                image_node.location = (-800, -400 * index)
                image_node.image = bpy.data.images.load(filepath)
                image_node.location.y += 800
                #Check for each type of texture
                if texture_type == "Base Color":
                    links.new(
                        image_node.outputs["Color"],
                        principled_node.inputs["Base Color"],
                    )
                elif texture_type == "Roughness":
                    links.new(
                        image_node.outputs["Color"], principled_node.inputs["Roughness"]
                    )
                elif texture_type == "Metallic":
                    links.new(
                        image_node.outputs["Color"], principled_node.inputs["Metallic"]
                    )

                elif texture_type == "Normal" and texture_settings.use_normal_map:
                    normal_node = nodes.new(type="ShaderNodeNormalMap")
                    normal_node.location = (
                        image_node.location.x + node_x_displacement,
                        image_node.location.y,
                    )
                    links.new(image_node.outputs["Color"], normal_node.inputs["Color"])
                    links.new(
                        normal_node.outputs["Normal"], principled_node.inputs["Normal"]
                    )

                elif texture_type == "Height" and texture_settings.use_height_map:
                    Height_node = nodes.new(type="ShaderNodeDisplacement")
                    Height_node.location = (
                        image_node.location.x + node_x_displacement,
                        image_node.location.y,
                    )
                    links.new(image_node.outputs["Color"], Height_node.inputs["Normal"])
                    links.new(
                        Height_node.outputs["Displacement"],
                        principled_node.inputs["Normal"],
                    )

                elif texture_type == "Bump" and texture_settings.use_bump_map:
                    bump_node = nodes.new(type="ShaderNodeBump")
                    bump_node.location = (
                        image_node.location.x + node_x_displacement,
                        image_node.location.y,
                    )
                    links.new(image_node.outputs["Color"], bump_node.inputs["Normal"])
                    links.new(
                        bump_node.outputs["Normal"], principled_node.inputs["Normal"]
                    )
        self.report({"INFO"},f"{str(len(textures_assigned))} textures were imported {str(textures_assigned)}",)
        self.report({"INFO"},"If a texture is missing or wasnt assigned then check the objects texture folder or the node editor ",)

    def get_texture_type(self, filename):
        """Returns the texture type by name"""

        if "diffuse" in filename.lower() or "base_color" in filename.lower():
            return "Base Color"
        elif "roughness" in filename.lower():
            return "Roughness"
        elif "normal" in filename.lower():
            return "Normal"
        elif "height" in filename.lower():
            return "Height"
        elif "metallic" in filename.lower():
            return "Metallic"

        else:
            return None


# --------------------------------------------------------------------------------
# UTILITY OPERATORS
# --------------------------------------------------------------------------------


class REMOVE_OT_UNUSED_TEXTURES(bpy.types.Operator):
    """Removes any unused image texture nodes"""

    bl_idname = "remove.unusedtextures"
    bl_label = "Remove unused textures in material"

    def execute(self, context):
        obj = bpy.context.active_object
        if not obj.data.materials or obj is None:
            bpy.context.report({"WARNING"},text="Object has no material or no object has been selected")
        nodes = obj.data.materials[0].node_tree.nodes
        for node in nodes:
            try:
                if isinstance(node, bpy.types.ShaderNodeTexImage):

                    if len(node.outputs[0].links) == 0:
                        nodes.remove(node)

            except Exception as e:
                self.report({"INFO"}, f"An Error has occured: {e}")
        self.realign_nodes(nodes)

        return {"FINISHED"}

    def realign_nodes(self, nodes):
        """Realigns the remaining texture nodes for better structure"""

        y_offset = 0
        node_spacing = 300

        # Arranges nodes, searches for textureimage nodes only
        for node in nodes:
            if isinstance(node, bpy.types.ShaderNodeTexImage):
                node.location.y = y_offset
                y_offset -= node_spacing


class OPEN_OT_FBXFolder(bpy.types.Operator):
    """Opens the FBX Export Folder"""

    bl_idname = "open.fbx_folder"
    bl_label = "Open FBX Folder"

    def execute(self, context):
        export_folder = os.path.normpath("C:/Substancepainter/FBX")
        try:
            os.startfile(export_folder)
            self.report({"INFO"}, f"Opened folder: {export_folder}")
        except Exception as e:
            self.report({"ERROR"}, f"Failed to open folder: {str(e)}")
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
        col.prop(texture_settings, "use_height_map", text="Height Map")
        col.prop(texture_settings, "use_bump_map", text="Bump Map")


class VIEW3D_PT_QuickExporter_Cleanup(bpy.types.Panel):
    """Cleanup Functions Panel for the addon"""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "B2SP Linker"
    bl_label = "Cleanup Functions"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.operator(
            REMOVE_OT_UNUSED_TEXTURES.bl_idname,
            text="Remove unused image textures",
            icon="TRASH",
        )


classes = (
    texture_settings,
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
    bpy.types.Scene.texture_settings = bpy.props.PointerProperty(type=texture_settings)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.texture_settings


if __name__ == "__main__":
    register()
