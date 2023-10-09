import bpy

from . import user_fields


class FBX2RigifyPanel(bpy.types.Panel):
    """Creates a Panel. This is automatically registered with the global `register` function"""

    bl_label = "FBX to Rigify"
    bl_idname = "OBJECT_PT_fbx2rigify"

    # OPTION A: a panel in the Object properties window
    # bl_context = "object"

    # bl_space_type = "PROPERTIES"
    # https://docs.blender.org/api/current/bpy_types_enum_items/space_type_items.html#rna-enum-space-type-items

    # bl_region_type = "WINDOW"
    # https://docs.blender.org/api/current/bpy_types_enum_items/region_type_items.html#rna-enum-region-type-items

    # OPTION B:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FBX2Rigify"

    def draw(self, context):
        layout = self.layout

        # header
        row = layout.row()
        row.label(text="Turn AS to Rigify!", icon="ARMATURE_DATA")

        layout.separator()

        # display all the custom properties in a column
        col = layout.column()

        for prop_name, _ in user_fields._PROPERTIES:
            row = col.row()
            row.prop(context.scene, prop_name)
