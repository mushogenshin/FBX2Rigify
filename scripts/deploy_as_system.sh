#!/bin/bash

# Get the absolute path of the current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && cd .. && pwd )"

# Copy the FBX2Rigify folder to Blender's addons directory
rsync -av --exclude=".git" --exclude=".vscode" "$DIR" /Applications/Blender.app/Contents/Resources/3.6/scripts/addons/
