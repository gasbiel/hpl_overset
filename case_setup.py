# coding: utf-8
import os
import shutil
import math
import numpy
from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
import numpy,copy
from stl import mesh
import stl

nSlices = 10
nbLayers = [3, 3, 3, 4, 4, 4, 5, 5, 5, 6]	#number of layers wanted for each blade section

#creating sections
os.system('cat geom/foil.ast > foil.stl')
blade = stl.mesh.Mesh.from_file('foil.stl')
os.system('touch cut_foil.stl')

sections=numpy.linspace(blade.z.min(),blade.z.max(),nSlices+1)
sections[0]=0
sections[-1]*=nSlices+1
filenames = []

for ii in range(len(sections[:-1])):
    vectors1=blade.vectors[(blade.z>=sections[ii]).any(axis=1) & (blade.z<sections[ii+1]).all(axis=1)]
    blade1=mesh.Mesh(numpy.zeros(len(vectors1), dtype=mesh.Mesh.dtype))
    blade1.vectors=vectors1
    blade1.save('section'+str(ii), mode=stl.Mode.ASCII)
    filenames.append('section'+str(ii))

#concatenating sections into one .stl file
with open('cut_foil.stl', 'w') as outfile:
    for fname in filenames:
        with open(fname) as infile:
            for line in infile:
                outfile.write(line)
os.system('rm foil.stl')
os.system('rm section*')

#creating case from template and adding .stl files
os.system('cp -r template/rotor_orig .')
os.system('cp -r template/stator_orig .')
os.system('mv cut_foil.stl geom')
os.system('mv geom/LE.stl rotor_orig')
os.system('mv geom/TE.stl rotor_orig')
os.system('cat geom/rotor_inlet.ast geom/rotor_outlet.ast geom/rotor_side1.ast geom/rotor_side2.ast geom/rotor_side3.ast geom/rotor_side4.ast geom/cut_foil.stl geom/tip.ast > rotor_orig/rotor.stl')
os.system('cat geom/stator_inlet.ast geom/stator_outlet.ast geom/stator_side1.ast geom/stator_side2.ast geom/stator_side3.ast geom/stator_side4.ast > stator_orig/stator.stl')

#adapting dicts to cut blade
meshDict = ParsedParameterFile('rotor_orig/system/meshDict')
patchDict = ParsedParameterFile('rotor_orig/system/createPatchDict')

patchNames = ['tip']

for i in range (nSlices):
	meshDict['localRefinement']['section'+str(i)] = {'additionalRefinementLevels':'$foilLevel'}
	meshDict['boundaryLayers']['patchBoundaryLayers']['section'+str(i)] = {'nLayers':str(nbLayers[i]), 'thicknessRatio':'$tRatio', 'allowDiscontinuity':str(1)}
	patchNames.append('section'+str(i))
meshDict['boundaryLayers']['patchBoundaryLayers']['tip'] = {'nLayers':str(nbLayers[-1]), 'thicknessRatio':'$tRatio', 'allowDiscontinuity':str(1)}
meshDict.writeFile()

patchDict['patches'][1]['patches'] = patchNames
patchDict.writeFile()
