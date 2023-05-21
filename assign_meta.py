import bpy
import logging

logger = logging.getLogger(__name__)


def switch_to_mode(mode):
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
    obj = bpy.context.object
    deselect_edit()

    edit_bones = obj.data.edit_bones
    if bone_name in edit_bones:
        edit_bones[bone_name].select = True
    else:
        logger.error(f"No bone named {bone_name} in armature {obj.name}")


# ------------------------------------------------------------------------
#    POSE MODE
# ------------------------------------------------------------------------


def deselect_pose():
    """Deselect all bones in POSE mode"""
    switch_to_mode("POSE")
    bpy.ops.pose.select_all(action="DESELECT")


def select_pose_bone(bone_name):
    obj = bpy.context.object
    deselect_pose()

    pose_bones = obj.pose.bones
    if bone_name in pose_bones:
        target_bone = pose_bones[bone_name]
        target_bone.bone.select = True
        # IMPORTANT: must include this line to make the bone active
        obj.data.bones.active = target_bone.bone
    else:
        logger.error(f"No bone named {bone_name} in armature {obj.name}")


# ------------------------------------------------------------------------
#    ASSIGN METARIG
# ------------------------------------------------------------------------


class AssignMeta(bpy.types.Operator):
    """Assign Rigify metarig to selected bone"""

    bl_idname = "object.assign_metarig"
    bl_label = "Assign Metarig"

    def execute(self, context):
        logger.info("Converting to Leg Metarig")

        select_pose_bone("Hip")
        bpy.context.active_pose_bone.rigify_type = "limbs.leg"

        return {"FINISHED"}
