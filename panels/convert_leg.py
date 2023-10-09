import bpy
import logging
import mathutils

# constant prop name tagged to initialized object in order to display immediate-mode-style UI
__IS_LEG__ = "fbx2rigify_leg"


class FBX2LegMeta(bpy.types.Panel):
    """UI panel for converting FBX to Rigify Leg Meta Rig"""

    bl_label = "🦿 Convert Leg"
    bl_idname = "OBJECT_PT_fbx2legmeta"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FBX2Rigify"
#    bl_parent_id = "OBJECT_PT_fbx2rigify"
    # bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        if not context.selected_objects:
            layout.label(text="Select a leg armature to start")
            return

        obj = context.active_object

        if __IS_LEG__ not in obj:
            box = layout.box()
            box.label(text="Initialize As Working Leg")
            box.operator(InitLeg.bl_idname, text="Go")
            return

        row = layout.row()
        row.label(text="Place Helpers:")

        # all the transform helpers
        row = layout.row()
        row.operator(HeelPrep.bl_idname,
                     text="Prep Heel", icon="BONE_DATA")

        # NOTE: `object.name` won't work with a Bone selected in Pose Mode
        # row = layout.row()
        # row.label(text="Active object is: " + obj.name)

        layout.separator()
        row = layout.row()
        row.label(text="Operate On Selection:")

        row = layout.row()
        row.operator(AssignLeg.bl_idname,
                     text="Assign as Leg", icon="MOD_ARMATURE")

        layout.separator()
        row = layout.row()
        row.operator(UninitLeg.bl_idname, text="Discard", icon="CANCEL")


class InitLeg(bpy.types.Operator):
    """Tag the selected object as a FBX working leg"""

    bl_idname = "fbx2rigify.init_leg"
    bl_label = "Tag Object as FBX Working Leg"

    def execute(self, context):
        obj = bpy.context.active_object
        obj[__IS_LEG__] = True
        return {"FINISHED"}


class UninitLeg(bpy.types.Operator):
    """Untag the selected object as a FBX working leg"""

    bl_idname = "fbx2rigify.uninit_leg"
    bl_label = "Untag Object as FBX Working Leg"

    def execute(self, context):
        obj = bpy.context.active_object
        del obj[__IS_LEG__]
        return {"FINISHED"}


class HeelPrep(bpy.types.Operator):
    """
    Create a Heel bone (for limbs.leg metarig).
    If no other bone is selected, the Heel is placed near the world origin.
    Otherwise, the Heel is placed near the selected bone.
    """

    bl_idname = "fbx2rigify.heel_prep"
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

    bl_idname = "fbx2rigify.assign_leg"
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
    bpy.utils.register_class(InitLeg)
    bpy.utils.register_class(UninitLeg)
    bpy.utils.register_class(HeelPrep)
    bpy.utils.register_class(AssignLeg)
    bpy.utils.register_class(FBX2LegMeta)


def unregister():
    bpy.utils.unregister_class(FBX2LegMeta)
    bpy.utils.unregister_class(AssignLeg)
    bpy.utils.unregister_class(HeelPrep)
    bpy.utils.unregister_class(UninitLeg)
    bpy.utils.unregister_class(InitLeg)

########################################################################################################################


if __name__ == "__main__":

    def switch_to_mode(mode: str):
        """Switch to the specified mode"""

        # Get the current mode
        current_mode = bpy.context.active_object.mode

        if current_mode == mode:
            return

        bpy.ops.object.mode_set(mode=mode)

    def is_not_armature():
        """See if the active object is an armature, or if there is no active object"""
        obj = bpy.context.active_object
        is_true = (not obj) or (obj.type != "ARMATURE")

        if is_true:
            print("No armature selected")

        return is_true

    def ls_selected_edit_bones():
        obj = bpy.context.active_object
        return [bone for bone in obj.data.edit_bones if bone.select]

    def ls_selected_pose_bones(obj=None):
        obj = bpy.context.active_object
        return [bone for bone in obj.pose.bones if bone.bone.select]

    register()
