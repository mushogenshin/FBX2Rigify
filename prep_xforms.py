"""Placing the transforms needed for Rigify metarig hierarchies"""

import logging
import bpy

logger = logging.getLogger(__name__)


class HeelPrep(bpy.types.Operator):
    """Create a Heel bone for limbs.leg metarig"""

    bl_idname = "object.heel_prep"
    bl_label = "Prep Heel Bone"

    def execute(self, context):
        logger.info("Creating Heel bone for leg metarig")

        # TODO

        return {"FINISHED"}
