import bpy

from . import user_fields


class FBX2RigifyPanel(bpy.types.Panel):
    """Creates a Panel. This is automatically registered with the global `register` function"""

    bl_label = "FBX to Rigify"
    bl_idname = "OBJECT_PT_fbx2rigify"

    # OPTION A: a panel in the Object properties window
    # bl_context = "object"

    # bl_space_type = "PROPERTIES"
    # https://docs.blender.org/api/current/bpy_types_enum_items/space_type_items.html#rna-enum-space-type-items

    # bl_region_type = "WINDOW"
    # https://docs.blender.org/api/current/bpy_types_enum_items/region_type_items.html#rna-enum-region-type-items

    # OPTION B:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FBX2Rigify"

    def draw(self, context):
        layout = self.layout
        selected = context.selected_objects

        # header
        row = layout.row()
        row.label(text="Turn FBX Skeleton to Rigify!", icon="ARMATURE_DATA")

        if user_fields._PROPERTIES:
            # display all the custom properties in a column
            col = layout.column()

            for prop_name, _ in user_fields._PROPERTIES:
                row = col.row()
                row.prop(context.scene, prop_name)

            layout.separator()

        # filters for armatures only
        armatures = [obj for obj in selected if obj.type == "ARMATURE"]

        if armatures:
            obj = armatures[0]
            # sees if some bone is already assigned some metarig
            maybe_assigned = any(bone.rigify_type for bone in obj.pose.bones)

            if maybe_assigned:
                row = layout.row()
                row.operator(ApplyAndGenerate.bl_idname,
                             text="Apply Xforms & Generate Rig", icon="HEART")


class ApplyAndGenerate(bpy.types.Operator):
    """Applies all transforms and generates Rigify"""

    bl_idname = "fbx2rigify.apply_xforms_and_generate"
    bl_label = "Apply all transforms and generate Rigify"

    def execute(self, context):
        bpy.ops.object.transform_apply(
            location=True, rotation=True, scale=True)
        bpy.ops.pose.rigify_generate()

        return {"FINISHED"}
