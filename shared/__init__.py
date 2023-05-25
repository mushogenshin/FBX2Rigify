import logging
import bpy


def is_not_armature(obj):
    """See if the active object is an armature, or if there is no active object"""
    is_true = (not obj) or (bpy.context.object.type != "ARMATURE")

    if is_true:
        print("No armature selected")

    return is_true


def ls_selected_edit_bones(obj=None):
    if not obj:
        obj = bpy.context.object
    return [bone for bone in obj.data.edit_bones if bone.select]


def ls_selected_pose_bones(obj=None):
    if not obj:
        obj = bpy.context.object
    return [bone for bone in obj.pose.bones if bone.bone.select]
