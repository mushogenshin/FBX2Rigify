#!/bin/bash

# Get the absolute path of the current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && cd .. && pwd )"

# Create the symbolic link
ln -s "$DIR" "/Users/mushogenshin/Library/Application Support/Blender/3.6/scripts/addons/FBX2Rigify"