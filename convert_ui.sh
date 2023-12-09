#!/bin/bash

# Find all .ui files in the src/app/ui directory
for ui_file in $(find app/ui -name "music_player.ui"); do
    # Use pyuic5 to convert the .ui file to a .py file
    pyuic5 -x $ui_file -o ${ui_file%.*}.py
done
