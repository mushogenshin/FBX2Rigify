import bpy

from .core import assign_meta
from .core import prep_xforms
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

        obj = context.object

        row = layout.row()
        row.label(text="PLACE HELPERS:", icon="BONE_DATA")

        # all the transform helpers
        row = layout.row()
        row.operator(prep_xforms.HeelPrep.bl_idname, text="Prep Heel")

        # NOTE: `object.name` won't work with a Bone selected in Pose Mode
        # row = layout.row()
        # row.label(text="Active object is: " + obj.name)
        # row = layout.row()
        # row.prop(obj, "name")

        # row = layout.row()
        # row.operator("mesh.primitive_cube_add")

        layout.separator()
        row = layout.row()
        row.label(text="OPERATE ON SELECTION:", icon="MOD_ARMATURE")

        row = layout.row()
        row.operator(assign_meta.AssignLeg.bl_idname, text="Assign as Leg")


# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------
