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
        if objects is None: 
            self.report({"WARNING"}, "No object selected")
        # Export each object and track success
        try:
            for obj in objects:
                if self.export_object(obj):
                    self.report({"INFO"},f"Successfully exported {obj.name}")
#            self.open_substancepainter()            
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
            # Fix name and path
            export_name = f"{obj.name}.fbx"
            export_path = os.path.normpath(
            os.path.join(self.export_folder, export_name))
           
            file = bpy.ops.export_scene.fbx(filepath=export_path, global_scale=1.0, apply_unit_scale=True, use_selection=True)
               
            # Export the selected object
            self.report({"INFO"}, f"Exported {obj.name} to {file}")
            self.report({"INFO"}, f"Opening {obj.name} in Substance Painter")

            #self.open_substancepainter(file)
            object_path = os.path.normpath(os.path.join(self.export_folder,export_name))
            object_path = object_path.replace("\\","/")
            self.open_substancepainter(object_path)
            self.report({"INFO"}, f"object path {object_path}")
            return object_path
        else:    
            self.report({"WARNING"}, f"{obj.name} is not a mesh object, skipping mesh check.")
            return False

    def open_substancepainter(self,File):

        try:
            # Run Substance Painter
            self.report({"INFO"}, f"Trying to open Substance Painter at {str(self.substance_painter_path)} with FBX {File}")
            #subprocess.Popen([self.substance_painter_path,File])
            #"C:\Program Files\Adobe\Adobe Substance 3D Painter\Adobe Substance 3D Painter.exe"
            #"C:\Program Files\Adobe\Adobe Substance 3D Painter"
   
            subprocess.run([self.substance_painter_path, "--mesh", File], check=True)
            #subprocess.Popen([f'"{self.substance_painter_path}"', f'"{File}"'])
            self.report({"INFO"}, f'"{self.substance_painter_path}"')
            self.report({"INFO"}, f'"{File}"')
            
        except Exception as e:
            self.report(
                {'ERROR'}, f"Could not open Substance Painter: {str(e)}, {str(self.substance_painter_path)},{str(File)}")
    


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


classes = (VIEW3D_PT_QuickExporter, EXPORT_OT_Substancepainter_exporter)

# Register the panel class


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
