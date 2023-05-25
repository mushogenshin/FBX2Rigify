"""Assign Rigify metarig to selected bone"""

import bpy

from .shared import *


def switch_to_mode(mode):
    """Switch to the specified mode"""

    # Get the current mode
    current_mode = bpy.context.object.mode

    if current_mode == mode:
        return

    bpy.ops.object.mode_set(mode=mode)


# ------------------------------------------------------------------------
#    EDIT MODE
# ------------------------------------------------------------------------


def deselect_edit():
    """Deselect all bones in EDIT mode"""
    switch_to_mode("EDIT")

    for bone in bpy.context.object.data.edit_bones:
        bone.select = False


def select_edit_bone(bone_name):
    """Make the specified bone selected in EDIT mode"""

    obj = bpy.context.object
    if is_not_armature(obj):
        return

    deselect_edit()

    edit_bones = obj.data.edit_bones
    if bone_name in edit_bones:
        edit_bones[bone_name].select = True
    else:
        print(f"No bone named {bone_name} in armature {obj.name}")


# ------------------------------------------------------------------------
#    POSE MODE
# ------------------------------------------------------------------------


def deselect_pose():
    """Deselect all bones in POSE mode"""
    switch_to_mode("POSE")
    bpy.ops.pose.select_all(action="DESELECT")


def select_pose_bone(bone_name):
    """Make the specified bone selected and active in POSE mode"""

    obj = bpy.context.object
    if is_not_armature(obj):
        return

    deselect_pose()

    pose_bones = obj.pose.bones
    if bone_name in pose_bones:
        target_bone = pose_bones[bone_name]
        target_bone.bone.select = True
        # IMPORTANT: must include this line to make the bone active
        obj.data.bones.active = target_bone.bone
    else:
        print(f"No bone named {bone_name} in armature {obj.name}")


# ------------------------------------------------------------------------
#    ASSIGN METARIG
# ------------------------------------------------------------------------


class AssignLeg(bpy.types.Operator):
    """Assign leg metarig to selected bones"""

    bl_idname = "object.assign_metarig_leg"
    bl_label = "Assign limbs.leg Metarig"

    def execute(self, context):
        # NOTE: We're relying on the user to be in the correct mode (`POSE` mode)
        # to use this operator

        obj = bpy.context.object

        if is_not_armature(obj):
            return {"CANCELLED"}

        for bone in ls_selected_pose_bones(obj):
            print(f'Assigning "limbs.leg" metarig to {bone.name}')
            bone.rigify_type = "limbs.leg"

        return {"FINISHED"}
