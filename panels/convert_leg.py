import bpy
import mathutils

from ..shared import *


class FBX2LegMeta(bpy.types.Panel):
    """UI panel for converting FBX to Rigify Leg Meta Rig"""

    bl_label = "🦿 Convert Leg"
    bl_idname = "OBJECT_PT_fbx2legmeta"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FBX2Rigify"
    bl_parent_id = "OBJECT_PT_fbx2rigify"
    # bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        obj = context.active_object

        row = layout.row()
        row.label(text="Place Helpers:")

        # all the transform helpers
        row = layout.row()
        row.operator(HeelPrep.bl_idname,
                     text="Prep Heel", icon="BONE_DATA")

        # NOTE: `object.name` won't work with a Bone selected in Pose Mode
        # row = layout.row()
        # row.label(text="Active object is: " + obj.name)
        # row = layout.row()
        # row.prop(obj, "name")

        # row = layout.row()
        # row.operator("mesh.primitive_cube_add")

        layout.separator()
        row = layout.row()
        row.label(text="Operate On Selection:")

        row = layout.row()
        row.operator(AssignLeg.bl_idname,
                     text="Assign as Leg", icon="MOD_ARMATURE")


class HeelPrep(bpy.types.Operator):
    """
    Create a Heel bone (for limbs.leg metarig).
    If no other bone is selected, the Heel is placed near the world origin.
    Otherwise, the Heel is placed near the selected bone.
    """

    bl_idname = "object.heel_prep"
    bl_label = "Prep Heel Bone"

    def execute(self, context):
        obj = bpy.context.active_object

        # We need to be in the `EDIT` mode to use this operator
        if obj.mode == "OBJECT":
            switch_to_mode("EDIT")
            return {"CANCELLED"}

        # User now is in the right mode
        if is_not_armature():
            return {"CANCELLED"}

        print("Creating Heel bone for leg metarig")

        # Create the heel bone
        armature = obj.data
        heel_bone = armature.edit_bones.new("Heel")
        # NOTE: After creation, the bone's head and tail position MUST be set

        # In case user has selected "some" foot bone
        selection = ls_selected_edit_bones()

        if selection:
            foot_bone = selection[0]

            # Set the position of the "Heel" bone from the world position of the "Foot" bone
            heel_bone.head = foot_bone.head.copy()
            # the "Heel" bone head is level with the "Foot" bone tail in the Z axis
            heel_bone.head.z = foot_bone.tail.z

            # the "Heel" bone tail is 0.1 units offset from its head in the X axis
            heel_bone.tail = heel_bone.head.copy() + mathutils.Vector((0.1, 0, 0))

            # Parent the "Heel" bone to the "Foot" bone
            heel_bone.parent = foot_bone
        else:
            # Just set some guess values
            heel_bone.head = (0.1, 0, 0)
            heel_bone.tail = (0.2, 0, 0)

        return {"FINISHED"}


class AssignLeg(bpy.types.Operator):
    """Assign leg metarig to selected bones"""

    bl_idname = "object.assign_metarig_leg"
    bl_label = "Assign limbs.leg Metarig"

    def execute(self, context):
        obj = bpy.context.active_object

        # We need to be in the `POSE` mode to use this operator
        if obj.mode != "POSE":
            switch_to_mode("POSE")
            return {"CANCELLED"}

        # User now is in the right mode
        if is_not_armature():
            return {"CANCELLED"}

        for bone in ls_selected_pose_bones():
            print(f'Assigning "limbs.leg" metarig to {bone.name}')
            bone.rigify_type = "limbs.leg"

        return {"FINISHED"}


def register():
    bpy.utils.register_class(HeelPrep)
    bpy.utils.register_class(AssignLeg)
    bpy.utils.register_class(FBX2LegMeta)


def unregister():
    bpy.utils.unregister_class(FBX2LegMeta)
    bpy.utils.unregister_class(AssignLeg)
    bpy.utils.unregister_class(HeelPrep)
