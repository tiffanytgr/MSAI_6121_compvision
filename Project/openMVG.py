#!/usr/bin/python
#! -*- encoding: utf-8 -*-

# This file is part of OpenMVG (Open Multiple View Geometry) C++ library.

# Python script to launch OpenMVG SfM tools on an image dataset
#
# usage : python tutorial_demo.py
#

# TODO: 1. AFTER your CMake installation, change to your openMVG bin folder...
# TODO: ... This installation folder was set during CMake config (in CMake GUI)...
# TODO: ... The below is the default, so probably no change needed for you
# Indicate the openMVG binary directory
OPENMVG_SFM_BIN = "C:/Users/tiffa/libraries/openMVG/src/build/Windows-AMD64-/Release"

# TODO: 2. Change CAMERA_SENSOR_WIDTH_DIRECTORY to "sensor_width_database" folder...
# TODO: ... THIS folder is found directly in whatever you git cloned, and not installed via CMake...

# TODO: 3. Inside this folder, edit "sensor_width_camera_database.txt"...
# TODO: ... by adding "<Camera maker> <Camera model>;8.0"...
# TODO: ... For <Camera maker> and <Camera model>, right-click on picture > Properties...
# TODO: ... > Details Tab > Scroll down and find <Camera maker> and <Camera model>...
# TODO: ... "8.0" is the sensor-width in mm (millimeters) typical of phone cameras...
# TODO: ... I found mine -> they typically give in terms of diagonal length...
# TODO: ... Width:Height ratio, typically 4:3 -> use Pythagoras' Theorem to get width...
# TODO: ... e.g., of new line added: "samsung Galaxy S24+;8.0"
# Indicate the openMVG camera sensor width directory
CAMERA_SENSOR_WIDTH_DIRECTORY = "C:/Users/tiffa/libraries/openMVG/src/openMVG/exif/sensor_width_database"

import os
import subprocess
import sys

def get_parent_dir(directory):
    return os.path.dirname(directory)

os.chdir(os.path.dirname(os.path.abspath(__file__)))
# input_eval_dir = os.path.abspath("./ImageDataset_SceauxCastle")
# TODO: 4. Change to a folder containing images (INPUTS)
input_eval_dir = "NTU_CCDS_Signpost"
# Checkout an OpenMVG image dataset with Git
# if not os.path.exists(input_eval_dir):
#   pImageDataCheckout = subprocess.Popen([ "git", "clone", "https://github.com/openMVG/ImageDataset_SceauxCastle.git" ])
#   pImageDataCheckout.wait()

# TODO: 5. Change to a folder to contain .ply (OUTPUTS) -> Folder will be created for you, so just choose a name
output_eval_dir = "./output"
# input_eval_dir = os.path.join(input_eval_dir, "images")
if not os.path.exists(output_eval_dir):
  os.mkdir(output_eval_dir)

input_dir = input_eval_dir
output_dir = output_eval_dir
print ("Using input dir  : ", input_dir)
print ("      output_dir : ", output_dir)

matches_dir = os.path.join(output_dir, "matches")
camera_file_params = os.path.join(CAMERA_SENSOR_WIDTH_DIRECTORY, "sensor_width_camera_database.txt")

# Create the ouput/matches folder if not present
if not os.path.exists(matches_dir):
  os.mkdir(matches_dir)

print ("1. Intrinsics analysis")
pIntrisics = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_SfMInit_ImageListing"),  "-i", input_dir, "-o", matches_dir, "-d", camera_file_params, "-c", "3"] )
pIntrisics.wait()

print ("2. Compute features")
pFeatures = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeFeatures"),  "-i", matches_dir+"/sfm_data.json", "-o", matches_dir, "-m", "SIFT", "-f" , "1"] )
pFeatures.wait()


print ("2. Compute matches")
pMatches = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeMatches"),  "-i", matches_dir+"/sfm_data.json", "-o", matches_dir+"/matches.putative.bin", "-f", "1", "-n", "ANNL2"] )
pMatches.wait()

print ("2. Filter matches" )
pFiltering = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_GeometricFilter"), "-i", matches_dir+"/sfm_data.json", "-m", matches_dir+"/matches.putative.bin" , "-g" , "f" , "-o" , matches_dir+"/matches.f.bin" ] )
pFiltering.wait()

reconstruction_dir = os.path.join(output_dir,"reconstruction_sequential")
print ("3. Do Incremental/Sequential reconstruction") #set manually the initial pair to avoid the prompt question
pRecons = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_SfM"), "--sfm_engine", "INCREMENTAL", "--input_file", matches_dir+"/sfm_data.json", "--match_dir", matches_dir, "--output_dir", reconstruction_dir] )
pRecons.wait()

print ("5. Colorize Structure")
pRecons = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeSfM_DataColor"),  "-i", reconstruction_dir+"/sfm_data.bin", "-o", os.path.join(reconstruction_dir,"colorized.ply")] )
pRecons.wait()

print ("4. Structure from Known Poses (robust triangulation)")
pRecons = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeStructureFromKnownPoses"),  "-i", reconstruction_dir+"/sfm_data.bin", "-m", matches_dir, "-o", os.path.join(reconstruction_dir,"robust.ply")] )
pRecons.wait()

# Reconstruction for the global SfM pipeline
# - global SfM pipeline use matches filtered by estimating essential matrices
# - here we reuse photometric matches and perform only the essential matrix filering
print ("2. Filter matches (for the global SfM Pipeline)")
pFiltering = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_GeometricFilter"), "-i", matches_dir+"/sfm_data.json", "-m", matches_dir+"/matches.putative.bin" , "-g" , "e" , "-o" , matches_dir+"/matches.e.bin" ] )
pFiltering.wait()

reconstruction_dir = os.path.join(output_dir,"reconstruction_global")
print ("3. Do Global reconstruction")
pRecons = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_SfM"), "--sfm_engine", "GLOBAL", "--input_file", matches_dir+"/sfm_data.json", "--match_file", matches_dir+"/matches.e.bin", "--output_dir", reconstruction_dir] )
pRecons.wait()

print ("5. Colorize Structure")
pRecons = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeSfM_DataColor"),  "-i", reconstruction_dir+"/sfm_data.bin", "-o", os.path.join(reconstruction_dir,"colorized.ply")] )
pRecons.wait()

print ("4. Structure from Known Poses (robust triangulation)")
pRecons = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeStructureFromKnownPoses"),  "-i", reconstruction_dir+"/sfm_data.bin", "-m", matches_dir, "-o", os.path.join(reconstruction_dir,"robust.ply")] )
pRecons.wait()
