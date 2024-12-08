import bpy
import os
import subprocess

bl_info = {
    "name": "Blender to Substance painter",
    "description": "Export a mesh to Substance painter",
    "author": "Alexander Kazakov",
    "version": (0, 1),
    "blender": (4, 2, 3),
    "location": "View3D > UI",
    "warning": "",  # used for warning icon and text in addons panel
    "doc_url": "TBA",
    "tracker_url": "TBA",
    "support": "COMMUNITY",
    "category": "Exporter",
}

#Move paths to seperate file


class EXPORT_OT_Substancepainter_exporter(bpy.types.Operator):
    bl_idname = "export.substance_painter"
    bl_label = "Export to Substance Painter"
    
    # Base paths
    export_folder = os.path.normpath("C:/Substancepainter/FBX")
    
    substance_painter_path = os.path.normpath(
        "C:/Program Files/Adobe/Adobe Substance 3D Painter/Adobe Substance 3D Painter.exe")

    def execute(self, context):
        # Ensure export folder exists
        if not os.path.exists(self.export_folder):
            os.makedirs(self.export_folder)
        # Get selected objects
        objects = context.selected_objects
        if not objects : 
            self.report({"WARNING"}, "No object selected")
        # Export each object and track success
        try:
            for obj in objects:
                if self.export_object(obj):
                    self.report({"INFO"},f"Successfully exported {obj.name}")
        except Exception as e:
            self.report({"ERROR"}, f"Failed to export {obj.name}, the error: {str(e)}")
        return {'FINISHED'}
    

    def material_check(self,obj):

        if len(obj.data.materials) == 0: 
            
            self.report({"INFO"}, f"No material on { obj.name}, creating new one")            
            new_material = bpy.data.materials.new(name=f"{obj.name}_material")
            new_material.use_nodes = True  # Enable nodes if you want shader control
            obj.data.materials.append(new_material)
            self.report({"INFO"}, f"{obj.name} has a {obj.name}_material added to it")
        else:
            self.report({"INFO"}, f"{obj.name} already has an material")



    def export_object(self, obj):
    # Set dynamic path for each object
            if obj.type == 'MESH':
        
                self.material_check(obj)
                #Create object folder
                object_folder = os.path.join(self.export_folder, obj.name)
                os.makedirs(object_folder, exist_ok=True)

                # Create a texture folder inside the object folder
                texture_folder_name = f"{obj.name}_textures" 
                texture_folder = os.path.join(object_folder, texture_folder_name)
                os.makedirs(texture_folder, exist_ok=True)
                
                #Set final exportpath and name
                export_name = f"{obj.name}.fbx"
                export_path = os.path.normpath(os.path.join(object_folder, export_name))

                # Export the selected object
                file = bpy.ops.export_scene.fbx(filepath=export_path, 
                                                global_scale=1.0, 
                                                apply_unit_scale=True, 
                                                use_selection=True)
                # Print info
                self.report({"INFO"}, f"Exported {obj.name} to {file}")
                self.report({"INFO"}, f"Opening {obj.name} in Substance Painter")


                #Normalize the path
                object_path = export_path.replace("\\", "/")
                # Attempt to open substance painter
                self.open_substancepainter(object_path)
                self.report({"INFO"}, f"object path {object_path}")
                return object_path
            else:    
                self.report({"WARNING"}, f"{obj.name} is not a mesh object, skipping mesh check.")
                return False

    def open_substancepainter(self,File):
        try:
            args = [self.substance_painter_path, "--mesh", File]
            subprocess.Popen(args, stdout=subprocess.PIPE, text=True)
            # Run Substance Painter
            self.report({"INFO"}, f"Trying to open Substance Painter at {str(self.substance_painter_path)} with FBX {File}")
        except Exception as e:
            self.report(
                {'ERROR'}, f"Could not open Substance Painter: {str(e)}, {str(self.substance_painter_path)},{str(File)}")


#one object at a time! test with multiple
class IMPORT_OT_Textures(bpy.types.Operator):
    bl_idname ="import.textures"
    bl_label = "import Textures"
    
    

    def execute(self,context):
        #Get active object
        obj = bpy.context.active_object
        
        #texture folder for object:
        textures_folder = os.path.join(os.path.normpath("C:/Substancepainter/FBX"),obj.name,f"{obj.name}_textures")        
        
        if not textures_folder:
            self.report({"INFO"}, f"Texture folder {str(textures_folder)} does not exist")
            return {'CANCELLED'}

        #Validate selection
        if not obj or obj.type !="MESH":
            self.report({"INFO"}, "Object is not a mesh or no object is selected")
        
        #Validate material, incase export function hasnt been used
        if not obj.data.materials:
            mat = bpy.data.materials.new(new=f"{obj.name}_Material")
            mat.use_nodes = True
            obj.data.materials.append(mat)
        material = obj.data.materials[0]
        #if material already exists, check if nodes are used
        if not material.use_nodes:
            material.use_nodes = True
        
        #Call assign textures method
        self.assign_textures(material,textures_folder)
        
        return {"FINISHED"}
        #obs! make sure node wrangler is enabled
    def assign_textures(self,material,textures_folder):
        #nodes and links of material
        node_tree = material.node_tree
        nodes = node_tree.nodes
        links = node_tree.links
        file_types = (".png",".jpg",".jpeg")
        # Remove previous nodes to clear the workspace
        for node in nodes:
            nodes.remove(node)

        # create BSDF and output node
        output_node = nodes.new(type="ShaderNodeOutputMaterial")
        output_node.location = (400, 0)

        principled_node = nodes.new(type="ShaderNodeBsdfPrincipled")
        principled_node.location = (0, 0)

        # Link the Principled BSDF to the Material Output
        links.new(principled_node.outputs["BSDF"], output_node.inputs["Surface"])

        # assign textures to material:
        #for filename in os.listdir(textures_folder):
        for index, filename in enumerate(os.listdir(textures_folder)):
            #check filetypes and join them
            if filename.lower().endswith(file_types):
                texture_type = self.get_texture_type(filename)
                filepath = os.path.join(textures_folder, filename)

                #Create an image node and apply texture 
                image_node = nodes.new(type="ShaderNodeTexImage")
                image_node.location = (-300, -400*index )
                image_node.image = bpy.data.images.load(filepath)
                #align better to bsdf
                image_node.location.y += 800
                                     
                                        
    def get_texture_type(self, filename):
            """
            Guess texture type based on the filename.
            """
            
            
            if "diffuse" in filename.lower() or "basecolor" in filename.lower():
                return "Base Color"
            elif "roughness" in filename.lower():
                return "Roughness"
            elif "normal" in filename.lower():
                return "Normal"
            elif "height" in filename.lower():
                return "Height"
            elif "Roughness" in filename.lower():
                return "Roughness"
            else:
                return None        
            
        

class OPEN_OT_FBXFolder(bpy.types.Operator):
    """Opens the FBX Export Folder"""
    bl_idname = "open.fbx_folder"
    bl_label = "Open FBX Folder"

    def execute(self, context):
        export_folder = os.path.normpath("C:/Substancepainter/FBX")
        try:
            os.startfile(export_folder)  
            self.report({'INFO'}, f"Opened folder: {export_folder}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open folder: {str(e)}")
        return {'FINISHED'}




class VIEW3D_PT_QuickExporter(bpy.types.Panel):
    """UI Panel for quick export to Substance Painter"""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Quick Export"
    bl_label = "Quick Exporter"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator(EXPORT_OT_Substancepainter_exporter.bl_idname,
                     text="Export to Substance Painter")
        row = layout.row()
        row.operator(OPEN_OT_FBXFolder.bl_idname,
                     text="Open the fbx folder")
        row = layout.row()
        row.operator(IMPORT_OT_Textures.bl_idname,
                     text="Import Textures from Substance Painter")
        
     


classes = (VIEW3D_PT_QuickExporter, EXPORT_OT_Substancepainter_exporter,OPEN_OT_FBXFolder,IMPORT_OT_Textures)

# Register the panel class
def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()