import logging
import bpy


def switch_to_mode(mode):
    """Switch to the specified mode"""

    # Get the current mode
    current_mode = bpy.context.object.mode

    if current_mode == mode:
        return

    bpy.ops.object.mode_set(mode=mode)


def is_not_armature(obj):
    """See if the active object is an armature, or if there is no active object"""
    is_true = (not obj) or (bpy.context.object.type != "ARMATURE")

    if is_true:
        print("No armature selected")

    return is_true


# ------------------------------------------------------------------------
#    EDIT MODE
# ------------------------------------------------------------------------

def ls_selected_edit_bones(obj=None):
    if not obj:
        obj = bpy.context.object
    return [bone for bone in obj.data.edit_bones if bone.select]


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

def ls_selected_pose_bones(obj=None):
    if not obj:
        obj = bpy.context.object
    return [bone for bone in obj.pose.bones if bone.bone.select]


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
