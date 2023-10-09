#!/bin/bash

# the addons should be installed to:
# SYSTEM: /Applications/Blender.app/Contents/Resources/3.6/scripts/addons/
# USER (symbolic link is fine): /Users/$USER/Library/Application\ Support/Blender/3.6/scripts/addons/

# Copy the FBX2Rigify folder to Blender's addons directory
rsync -av --exclude=".git" --exclude=".vscode" /Users/mushogenshin/projects/FBX2Rigify /Applications/Blender.app/Contents/Resources/3.6/scripts/addons/
