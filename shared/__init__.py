import logging
import bpy


# ------------------------------------------------------------------------
#    EDIT MODE
# ------------------------------------------------------------------------

def deselect_edit():
    """Deselect all bones in EDIT mode"""
    switch_to_mode("EDIT")

    # NOTE: see if we should use bpy.context.selected_objects instead
    for bone in bpy.context.active_object.data.edit_bones:
        bone.select = False


def select_edit_bone(bone_name: str):
    """Make the specified bone selected in EDIT mode"""

    if is_not_armature():
        return

    deselect_edit()

    # NOTE: see if we should use bpy.context.selected_objects instead
    obj = bpy.context.active_object
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


def select_pose_bone(bone_name: str):
    """Make the specified bone selected and active in POSE mode"""

    if is_not_armature():
        return

    deselect_pose()

    # NOTE: see if we should use bpy.context.selected_objects instead
    obj = bpy.context.active_object
    pose_bones = obj.pose.bones
    if bone_name in pose_bones:
        target_bone = pose_bones[bone_name]
        target_bone.bone.select = True
        # IMPORTANT: must include this line to make the bone active
        obj.data.bones.active = target_bone.bone
    else:
        print(f"No bone named {bone_name} in armature {obj.name}")
