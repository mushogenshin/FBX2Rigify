import bpy

from ..ops import assign_meta
from ..ops import prep_xforms
from .. import user_fields


class FBX2LegMeta(bpy.types.Panel):
    """Creates a Panel. This is automatically registered with the global `register` function"""

    bl_label = "Convert to Leg MetaRig"
    bl_idname = "OBJECT_PT_fbx2legmeta"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FBX2Rigify"
    bl_parent_id = "OBJECT_PT_fbx2rigify"
    # bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

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
