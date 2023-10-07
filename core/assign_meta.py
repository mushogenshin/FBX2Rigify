"""Assign Rigify metarig to selected bone"""

import bpy

from ..shared import *


# ------------------------------------------------------------------------
#    ASSIGN METARIG
# ------------------------------------------------------------------------


class AssignLeg(bpy.types.Operator):
    """Assign leg metarig to selected bones"""

    bl_idname = "object.assign_metarig_leg"
    bl_label = "Assign limbs.leg Metarig"

    def execute(self, context):
        obj = bpy.context.object

        # We need to be in the `POSE` mode to use this operator
        if obj.mode != "POSE":
            switch_to_mode("POSE")
            return {"CANCELLED"}

        if is_not_armature(obj):
            return {"CANCELLED"}

        for bone in ls_selected_pose_bones(obj):
            print(f'Assigning "limbs.leg" metarig to {bone.name}')
            bone.rigify_type = "limbs.leg"

        return {"FINISHED"}
