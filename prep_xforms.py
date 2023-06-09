"""Placing the transforms needed for Rigify metarig hierarchies"""

import bpy
import mathutils

from .shared import *


class HeelPrep(bpy.types.Operator):
    """
    Create a Heel bone (for limbs.leg metarig).
    If no other bone is selected, the Heel is placed near the world origin.
    Otherwise, the Heel is placed near the selected bone.
    """

    bl_idname = "object.heel_prep"
    bl_label = "Prep Heel Bone"

    def execute(self, context):
        # NOTE: We're relying on the user to be in the correct mode (`EDIT` mode)
        # to use this operator

        obj = bpy.context.object

        if is_not_armature(obj):
            return

        print("Creating Heel bone for leg metarig")

        # Create the heel bone
        armature = obj.data
        heel_bone = armature.edit_bones.new("Heel")
        # NOTE: After creation, the bone's head and tail position MUST be set

        # In case user has selected "some" foot bone
        selection = ls_selected_edit_bones(obj)

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
