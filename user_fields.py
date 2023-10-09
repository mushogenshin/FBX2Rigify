"""All custom properties"""

import bpy

# these will be set onto the `bpy.types.Scene`
_PROPERTIES = [
    # (
    #     "prefix",
    #     bpy.props.StringProperty(
    #         name="Prefix", default="Pref", description="A prefix"),
    # ),
    # ("add_version", bpy.props.BoolProperty(name="Add Version", default=False)),
    # ("version", bpy.props.IntProperty(name="Version", default=1)),
]

# import bpy

# class ItemId(bpy.types.PropertyGroup):
#     obj_id: bpy.props.IntProperty()

# class ScopedItems(bpy.types.PropertyGroup):
#     scope: bpy.props.StringProperty(name="Meta Type", default="Unknown")
#     members: bpy.props.CollectionProperty(type=ItemId)

#     # def init(self, obj):
#     #     item = self.members.add()
#     #     item.obj_id = obj.as_pointer()

# class HoanSettings(bpy.types.PropertyGroup):
#     items: bpy.props.CollectionProperty(type=ScopedItems)

#     def add_scoped_items(self, scope: str):
#         # only adds if not already in the list
#         if scope not in self.items:
#             item = self.items.add()
#             item.scope = scope
#         else:
#             item = self.items[scope]


# if __name__ == "__main__":
#     print("Registering Custom Properties")
#     bpy.utils.register_class(ItemId)
#     bpy.utils.register_class(ScopedItems)
#     bpy.utils.register_class(HoanSettings)
#     # bpy.types.Scene.hoan_settings = bpy.props.CollectionProperty(
#     #     type=ScopedItems)
#     bpy.types.Scene.hoan_settings = bpy.props.PointerProperty(type=HoanSettings)

# my_item = bpy.context.scene.hoan_settings.add()
# my_item.scope = "Leg"
# legs = my_item.members.add()
