import bpy
import os
import subprocess
from pathlib import Path
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


#--------------------------------------------------------------------------------
# PROPERTIES AND FOLDER PATHS
#--------------------------------------------------------------------------------

#adjust so that the project usees preferences paths instead of hardcoded
#Try to find the path automatically?
#adjust so that a new export folder is created if none exists
#reorganize the file for readability and fix labels, text etc
#Fix a proper Markdown




class FolderPathPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    spp_exe: bpy.props.StringProperty(
        name="Substance Painter executable path",
        subtype='FILE_PATH',
        default="C:/Program Files/Adobe/Adobe Substance 3D Painter/Adobe Substance 3D Painter.exe"
    )
    export_folder: bpy.props.StringProperty(
        name="Object export folder path",
        subtype='DIR_PATH',
        default="C:/Substancepainter/FBX"
    )
    def draw(self, context):
        layout = self.layout
        layout.label(text="Paths for Substance painter executable and export path for objects. Change according to your system")
        layout.prop(self, "spp_exe")
        layout.prop(self, "export_folder")

class TextureSettings(bpy.types.PropertyGroup):
    '''
    Class that handles which textures to include during the import 
    from Substance Painter
    '''
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
    
   
#--------------------------------------------------------------------------------
# EXPORT AND IMPORT OPERATORS
#--------------------------------------------------------------------------------
'''
set painter paths in preference
export_folder in preferences
create object folder with subfolder of textures like before
have function which auto detects for windwos
get_preferencs --> get paths from preferences --> set paths 

if path doesnt exist for texture set as

    textures_path = Path(bpy.path.abspath('//'))


'''



class EXPORT_OT_SubstancePainterExporter(bpy.types.Operator):
    '''
    Class to handle the export from Blender to Substance Painter
    '''
    bl_idname = "export.substance_painter"
    bl_label = "Export to Substance Painter"
    
    
    # Base paths
    #export_folder = os.path.normpath("C:/Substancepainter/FBX")

    def execute(self, context):
        preferences = context.preferences
        export_folder = preferences.addons[__name__].preferences.export_folder
        substance_painter_path = preferences.addons[__name__].preferences.spp_exe
       
        # Ensure export folder exists
        if not os.path.exists(export_folder):
            export_folder = Path(bpy.path.abspath('//'))
        
                
        objects = context.selected_objects
        # Get selected  
        if not objects: 
            self.report({"WARNING"}, "No object selected")
            return {'CANCELLED'}
       
        
        if self.mutiple_meshes(objects):
            #just add a obj folder
            self.report({"INFO"}, f" Multiple objects, creating subfolder named:{str(objects[0].name)}")
            
            collection_name= "Objects_"
            for obj in objects:
                collection_name+= obj.name[0]
            object_folder = os.path.join(export_folder,collection_name )
            export_folder = os.path.join(export_folder, str(object_folder))
            
            self.report({"INFO"}, f"object_folder {str(object_folder)}")
            self.report({"INFO"}, f"export_folder {str(export_folder)}")
            
           

        # List to store the export paths
        export_paths = []

        # Export each object and track success
        try:
            for obj in objects:
                if self.export_object(export_folder,obj):
                    export_paths.append(self.export_object(export_folder,obj))
            
            # If there are export paths, open Substance Painter with the objects
            if export_paths:
                self.open_substance_painter(export_paths,substance_painter_path)
            return {'FINISHED'}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to export objects, the error: {str(e)}")
            return {'CANCELLED'}
    
    def mutiple_meshes(self,objects):
        
        if not objects: 
            self.report({"WARNING"}, "No object selected")
            return {'CANCELLED'}
        if len(objects) >1:
            return True         

    def check_material(self, obj):
        '''
        checks if object has any materials and nodes
        '''
        if len(obj.data.materials) == 0: 
            self.report({"INFO"}, f"No material on {obj.name}, creating new one")            
            new_material = bpy.data.materials.new(name=f"{obj.name}_material")
            new_material.use_nodes = True  
            obj.data.materials.append(new_material)
            self.report({"INFO"}, f"{obj.name} has a {obj.name}_material added to it")
        else:
            self.report({"INFO"}, f"{obj.name} already has a material")

    def export_object(self,export_folder,obj):
        '''
        Return the fbx filepath and exports the mesh from blender to the specificed folderpath
        '''
        if obj.type == 'MESH':
            self.check_material(obj)
            object_folder = os.path.join(export_folder, obj.name)
            
            os.makedirs(object_folder, exist_ok=True)

            
            texture_folder_name = f"{obj.name}_textures"
             
            texture_folder = os.path.join(object_folder, texture_folder_name)
            
            os.makedirs(texture_folder, exist_ok=True)
            export_name = f"{obj.name}.fbx"
            export_path = os.path.normpath(os.path.join(object_folder, export_name))

            bpy.ops.export_scene.fbx(filepath=export_path, 
                                     global_scale=1.0, 
                                     apply_unit_scale=True, 
                                     use_selection=True)
            self.report({"INFO"}, f"Exported {obj.name} to {export_path}")
            return export_path
        else:    
            self.report({"WARNING"}, f"{obj.name} is not a mesh object, skipping mesh check.")
            return None

    def open_substance_painter(self, export_paths,spp_exe):
        '''
        Combine all mesh filepaths into a single list of arguments through a list comprehension
        results in [SP_exe, --mesh, mesh_path, --mesh, mesh_path, etc] 
        which opens substance painter with the selected meshes 
        '''
        
        try:
            args = [spp_exe] + [mesh for path in export_paths for mesh in ["--mesh", path]]
            subprocess.Popen(args, stdout=subprocess.PIPE, text=True)
            self.report({"INFO"}, f"Trying to open Substance Painter with FBX files: {', '.join(export_paths)}")
        except Exception as e:
            self.report({'ERROR'}, f"Could not open Substance Painter: {str(e)}")


class IMPORT_OT_Textures(bpy.types.Operator):
    '''
    Operator to handle importing textures from Substance Painter back to Blender
    '''
    bl_idname ="import.textures"
    bl_label = "import Textures"

    def execute(self,context):
        #Get active object and its texture folder
        obj = bpy.context.active_object
        preferences = context.preferences
        export_folder_path = preferences.addons[__name__].preferences.export_folder
        textures_folder = os.path.join(os.path.normpath(export_folder_path),obj.name,f"{obj.name}_textures")        
        object_folder = os.path.join(export_folder_path, obj.name)
        os.makedirs(object_folder, exist_ok=True)
        
        try:
            #Validate selection
            if not textures_folder.find(obj.name): 
                self.report({"INFO"}, f"Texture folder does not exist for {str(obj.name)}")
            if not textures_folder:
                self.report({"INFO"}, f"Texture folder {str(textures_folder)} does not exist")
            if not obj or obj.type !="MESH":
                self.report({"INFO"}, "Object is not a mesh or no object is selected")
            if not obj.data.materials:
                mat = bpy.data.materials.new(new=f"{obj.name}_Material")
                mat.use_nodes = True
                obj.data.materials.append(mat)
            material = obj.data.materials[0]
            if not material.use_nodes:
                material.use_nodes = True
            
            #Assign textures to material
            self.assign_textures(material,textures_folder,context.scene.texture_settings)
            return {"FINISHED"}
        except Exception as e:
            self.report({"INFO"}, f"Texture folder does not exist for {str(obj.name)}")
            return {"CANCELLED"}
        


    def assign_textures(self,material,textures_folder,texture_settings):
        '''
        Method to assign material and textures to the selected material,
        Takes the material, the objects texture folder and 
        the users texture settings as args
        '''
        node_tree = material.node_tree
        nodes = node_tree.nodes
        links = node_tree.links
        file_types = (".png",".jpg",".jpeg")
        node_x_displacement = 400
        textures_assigned = [] 
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
        for index, filename in enumerate(os.listdir(textures_folder)):
            #check filetypes and join them
            if filename.lower().endswith(file_types):
                texture_type = self.get_texture_type(filename)
                filepath = os.path.join(textures_folder, filename)
                textures_assigned.append(filename)
                #Create an image node and apply texture 
                image_node = nodes.new(type="ShaderNodeTexImage")
                image_node.location = (-800, -400*index )
                image_node.image = bpy.data.images.load(filepath)
                #align better to bsdf
                image_node.location.y += 800
                #connect to BSDF
                if texture_type == "Base Color":
                    links.new(image_node.outputs["Color"], principled_node.inputs["Base Color"])
                elif texture_type == "Roughness":
                    links.new(image_node.outputs["Color"], principled_node.inputs["Roughness"])
                elif texture_type == "Metallic":
                    links.new(image_node.outputs["Color"], principled_node.inputs["Metallic"])
                    
                #Check that these maps exist in the first place
                elif texture_type == "Normal" and texture_settings.use_normal_map :
                    normal_node = nodes.new(type="ShaderNodeNormalMap")
                    normal_node.location = (image_node.location.x +node_x_displacement, image_node.location.y)
                    links.new(image_node.outputs["Color"], normal_node.inputs["Color"])
                    links.new(normal_node.outputs["Normal"], principled_node.inputs["Normal"])

                elif texture_type == "Height" and texture_settings.use_height_map :
                    Height_node = nodes.new(type="ShaderNodeDisplacement")
                    Height_node.location = (image_node.location.x+node_x_displacement, image_node.location.y)
                    links.new(image_node.outputs["Color"], Height_node.inputs["Normal"])
                    links.new(Height_node.outputs["Displacement"], principled_node.inputs["Normal"])
                    
                elif texture_type == "Bump" and texture_settings.use_bump_map :
                    bump_node = nodes.new(type="ShaderNodeBump")
                    bump_node.location = (image_node.location.x+node_x_displacement, image_node.location.y)
                    links.new(image_node.outputs["Color"], bump_node.inputs["Normal"])
                    links.new(bump_node.outputs["Normal"], principled_node.inputs["Normal"])
        self.report({"INFO"}, f"{str(len(textures_assigned))} textures were imported {str(textures_assigned)}")
        self.report({"INFO"}, "If a texture is missing or wasnt assigned then check the objects texture folder or the node editor ")
      
                                        
    def get_texture_type(self, filename):
            """
            Returns the texture type by name
            """
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
            
#--------------------------------------------------------------------------------
# UTILITY OPERATORS 
#--------------------------------------------------------------------------------
  
class REMOVE_OT_UNUSED_TEXTURES(bpy.types.Operator):
    '''
    Removes any unused image texture nodes
    '''
    bl_idname = "remove.unusedtextures"
    bl_label = "Remove unused textures in material"
    def execute(self, context):
        obj = bpy.context.active_object
        if not obj.data.materials or obj is None:
            bpy.context.report({"WARNING"}, text="Object has no material or no object has been selected")
        nodes = obj.data.materials[0].node_tree.nodes
        for node in nodes: 
            try:
                if isinstance(node,bpy.types.ShaderNodeTexImage):
                    
                    if len(node.outputs[0].links) ==0:
                        nodes.remove(node)

            except Exception as e:
                self.report({"INFO"}, f"An Error has occured: {e}")  
        self.realign_nodes(nodes)
        
        return {'FINISHED'}
    def realign_nodes(self, nodes):
        """
        Realigns the remaining texture nodes for better structure
        """
        y_offset = 0
        node_spacing = 300  
        
        #Arranges nodes, searches for textureimage nodes only
        for node in nodes:
            if isinstance(node,bpy.types.ShaderNodeTexImage):
                node.location.y = y_offset
                y_offset -= node_spacing
                            

    

class OPEN_OT_FBXFolder(bpy.types.Operator):
    """
    Opens the FBX Export Folder
    """
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


#--------------------------------------------------------------------------------
# UI PANELs
#--------------------------------------------------------------------------------

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
        col.operator(EXPORT_OT_SubstancePainterExporter.bl_idname,
                     text="Export to Substance Painter", icon="EXPORT")
        col.operator(IMPORT_OT_Textures.bl_idname,
                     text="Import from Substance Painter", icon='IMPORT')
        col.operator(OPEN_OT_FBXFolder.bl_idname,
                     text="Open Object folder", icon="FILE_FOLDER")


class VIEW3D_PT_QuickExporter_ImportSettings(bpy.types.Panel):
    """Texture Import Settings Panel for the addon"""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "B2SP Linker"
    bl_label = "Import Settings"
    bl_icon="SETTINGS"
    
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
        col.operator(REMOVE_OT_UNUSED_TEXTURES.bl_idname,
                     text="Remove unused image textures",icon="TRASH")        



classes = (FolderPathPreferences,TextureSettings,VIEW3D_PT_QuickExporter_ExportImport,VIEW3D_PT_QuickExporter_ImportSettings, EXPORT_OT_SubstancePainterExporter,VIEW3D_PT_QuickExporter_Cleanup,OPEN_OT_FBXFolder,IMPORT_OT_Textures,REMOVE_OT_UNUSED_TEXTURES)




#Register and unregister classes
def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.texture_settings = bpy.props.PointerProperty(type=TextureSettings)
def unregister():
    for c in (classes):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.texture_settings
    
if __name__ == "__init__":
    register()