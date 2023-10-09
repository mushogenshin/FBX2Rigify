"""Assign Rigify metarig to selected bone"""

import bpy

from ..shared import *


# ------------------------------------------------------------------------
#    ASSIGN METARIG TO SELECTED BONE(S)
# ------------------------------------------------------------------------


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
