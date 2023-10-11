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

        if obj.mode == "OBJECT":
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
        if obj.mode == "EDIT":
            # prompts for prerequisite
            row = layout.row()
            row.label(text="First select the foot as parent", icon="INFO")
            label = "Insert Heel as child"
        else:
            row = layout.row()
            row.label(text="Place Helpers:")
            label = "Insert Heel"

        row = layout.row()
        row.operator(HeelPrep.bl_idname,
                     text=label, icon="BONE_DATA")

        # only allows assigning leg metarig if the bone count suffices
        if bone_count >= __REQUIRED_BONE_NUM__:
            layout.separator()
            row = layout.row()
            row.label(text="Assign Metarig:")

            if obj.mode == "POSE":
                # prompts for prerequisite
                row = layout.row()
                row.label(text="First select the thigh", icon="INFO")
                label = "Tag as Leg"
            else:
                label = "Tag Leg"

            row = layout.row()
            row.operator(AssignLeg.bl_idname,
                         text=label, icon="OUTLINER_DATA_GP_LAYER")

        # allows discarding the working object nonetheless
        layout.separator()
        row = layout.row()
        row.operator(UninitLeg.bl_idname, text="Discard", icon="CANCEL")


class InitLeg(bpy.types.Operator):
    """Tag the selected object as a FBX working leg"""

    bl_idname = "fbx2rigify.init_leg"
    bl_label = "Tag Object as FBX Working Leg"

    def execute(self, context):
        obj = get_single_active_object()
        if not obj:
            return {"CANCELLED"}

        obj[__IS_WORKING_ITEM__] = True
        return {"FINISHED"}


class UninitLeg(bpy.types.Operator):
    """Untag the selected object as a FBX working leg"""

    bl_idname = "fbx2rigify.uninit_leg"
    bl_label = "Untag Object as FBX Working Leg"

    def execute(self, context):
        obj = get_single_active_object()
        if not obj:
            return {"CANCELLED"}

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
        """IMPORTANT: caller is responsible to make sure an armature is selected"""

        obj = bpy.context.active_object

        # We need to be in the `EDIT` mode to use this operator
        if obj.mode == "OBJECT":
            switch_to_mode("EDIT")
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
        """IMPORTANT: caller is responsible to make sure an armature is selected"""

        obj = bpy.context.active_object

        # We need to be in the `POSE` mode to use this operator
        if obj.mode != "POSE":
            switch_to_mode("POSE")
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


def get_single_active_object():
    """Returns the active object, or None if there is no active object"""
    objs = bpy.context.selected_objects
    return objs[0] if objs else None


def switch_to_mode(mode: str):
    """Switch to the specified mode"""
    obj = get_single_active_object()
    if not obj:
        return

    # compares the current mode
    if obj.mode == mode:
        return

    bpy.ops.object.mode_set(mode=mode)


def ls_selected_edit_bones():
    obj = get_single_active_object()
    if not obj:
        return []
    return [bone for bone in obj.data.edit_bones if bone.select]


def ls_selected_pose_bones():
    obj = get_single_active_object()
    if not obj:
        return []
    return [bone for bone in obj.pose.bones if bone.bone.select]


def snap_parent_tail_to_child_head(parent, child):
    """
        Args:
            parent: bpy.types.Object
            child: bpy.types.Object
    """
    parent.tail = child.head
    child.use_connect = True


def fix_disconnected_selection():
    """
        Only fixes what is selected in EDIT mode
    """
    armature = get_single_active_object()
    selected = [b for b in armature.data.edit_bones if b.select]
    for parent in selected:
        if parent.children:
            # we use the first child as the target
            child = parent.children[0]
            if not child.use_connect:
                snap_parent_tail_to_child_head(parent, child)


if __name__ == "__main__":
    register()
