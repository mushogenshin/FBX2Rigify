import bpy
import logging
import mathutils

# prop name tagged to initialized object in order to display immediate-mode-style UI
__IS_WORKING_ITEM__ = "fbx2rigify_leg"
# we need: 1 thigh, 1 shin, 1 foot, 1 toe, 1 heel
__REQUIRED_BONE_NUM__ = 5


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
        selected = context.selected_objects

        # filters for armatures only
        armatures = [obj for obj in selected if obj.type == "ARMATURE"]

        # must have at least one armature selected
        if not armatures:
            layout.label(text="Select a leg armature to start")
            return

        # forbids working on multiple armatures at once
        if len(armatures) > 1:
            layout.label(text="Please work on one leg at a time")
            return

        obj = armatures[0]
        row = layout.row()
        row.prop(obj, "name", text="Target")

        # keeps track of the working object
        if __IS_WORKING_ITEM__ not in obj:
            box = layout.box()
            box.label(text="Initialize As Working Leg")
            box.operator(InitLeg.bl_idname, text="Go")
            return

        # checks the bone count in both modes
        bone_count = max(len(obj.data.bones), len(obj.data.edit_bones))

        # shows warning
        if bone_count < __REQUIRED_BONE_NUM__:
            layout.label(
                text=f"Required at least {__REQUIRED_BONE_NUM__} bones", icon="ERROR")

        # allows placing more helpers even if the bone count already meets the minimum required
        row = layout.row()
        row.label(text="Place Helpers:")

        row = layout.row()
        row.operator(HeelPrep.bl_idname,
                     text="Insert Heel", icon="BONE_DATA")

        # only allows assigning leg metarig if the bone count suffices
        if bone_count >= __REQUIRED_BONE_NUM__:
            layout.separator()
            row = layout.row()
            row.label(text="Operate On Selection:")

            row = layout.row()
            row.operator(AssignLeg.bl_idname,
                         text="Assign as Leg", icon="MOD_ARMATURE")

        # allows discarding the working object nonetheless
        layout.separator()
        row = layout.row()
        row.operator(UninitLeg.bl_idname, text="Discard", icon="CANCEL")


class InitLeg(bpy.types.Operator):
    """Tag the selected object as a FBX working leg"""

    bl_idname = "fbx2rigify.init_leg"
    bl_label = "Tag Object as FBX Working Leg"

    def execute(self, context):
        obj = bpy.context.active_object
        obj[__IS_WORKING_ITEM__] = True
        return {"FINISHED"}


class UninitLeg(bpy.types.Operator):
    """Untag the selected object as a FBX working leg"""

    bl_idname = "fbx2rigify.uninit_leg"
    bl_label = "Untag Object as FBX Working Leg"

    def execute(self, context):
        obj = bpy.context.active_object
        del obj[__IS_WORKING_ITEM__]
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

        objs = bpy.context.selected_objects
        if not objs:
            return

        # Get the current mode
        current_mode = objs[0].mode

        if current_mode == mode:
            return

        bpy.ops.object.mode_set(mode=mode)

    def is_not_armature():
        """
        See if the selected object is NOT an armature.
        Return True if there is no object selected
        """

        objs = bpy.context.selected_objects
        if not objs:
            return True

        return objs[0].type != "ARMATURE"

    def ls_selected_edit_bones():
        objs = bpy.context.selected_objects
        if not objs:
            return []
        return [bone for bone in objs[0].data.edit_bones if bone.select]

    def ls_selected_pose_bones(obj=None):
        objs = bpy.context.selected_objects
        if not objs:
            return []
        return [bone for bone in objs[0].pose.bones if bone.bone.select]

    register()
