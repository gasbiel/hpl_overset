import FreeCAD, math, Draft, Part
from math import sqrt, pi, sin, cos, asin, acos
from FreeCAD import Base
import numpy
from numpy import tan, pi, sin, cos
import os
import Mesh
doc=FreeCAD.newDocument()

def profil(chord,shape,axis,side,gap):
	coordinates=numpy.loadtxt('CAO/'+shape+'_'+side+'.dat')
	coordinates=coordinates[coordinates[:,0].argsort()]
	if side == "extrados":
		coordinates[:,1]=(coordinates[:,1]+coordinates[:,0]*gap/2.)*chord
	else:
		coordinates[:,1]=(coordinates[:,1]-coordinates[:,0]*gap/2.)*chord
	coordinates[:,0]=(coordinates[:,0]-axis)*chord
	return coordinates

geom=numpy.genfromtxt('CAO/NREL_1.5MW.dat',dtype='str',skip_header=1)
TEGap=1/50.#100. gives more accurate lift...
span=float(geom[-1,1])
pitch=2.6
xDisc=200
LEidx=int(.1*xDisc)#chord point index included in LE refinement
extradosLine=[]
intradosLine=[]
LELines=[]
TELines=[]
print("Creating stations")
for i in geom:
	if i[4]=='cylinder':
		extradosPts=profil(float(i[3]),i[4],float(i[5]),"extrados",1/1000.)
		intradosPts=profil(float(i[3]),i[4],float(i[5]),"intrados",1/1000.)
	else:
		extradosPts=profil(float(i[3]),i[4],float(i[5]),"extrados",TEGap)
		intradosPts=profil(float(i[3]),i[4],float(i[5]),"intrados",TEGap)
	extradosLineOrig=Part.makePolygon([Base.Vector(x[0],x[1],float(i[1])) for x in extradosPts])
	intradosLineOrig=Part.makePolygon([Base.Vector(x[0],x[1],float(i[1])) for x in intradosPts])
	extradosLineOrig.rotate(Base.Vector(0,0,0),Base.Vector(0,0,1),float(i[2])+pitch-90)
	intradosLineOrig.rotate(Base.Vector(0,0,0),Base.Vector(0,0,1),float(i[2])+pitch-90)
	extradosPtsInterp=numpy.array(extradosLineOrig.discretize(xDisc))
	intradosPtsInterp=numpy.array(intradosLineOrig.discretize(xDisc))
	extradosInterp=Part.makePolygon([Base.Vector(x[0],x[1],x[2]) for x in extradosPtsInterp])
	intradosInterp=Part.makePolygon([Base.Vector(x[0],x[1],x[2]) for x in intradosPtsInterp])
	extradosLine.append(extradosInterp)
	intradosLine.append(intradosInterp)
	LELines.append(Part.makePolygon([Base.Vector(x[0],x[1],x[2]) for x in numpy.vstack((intradosPtsInterp[LEidx::-1],extradosPtsInterp[1:LEidx]))]))
	TELines.append(Part.makePolygon([intradosInterp.Vertexes[-1].Point,extradosInterp.Vertexes[-1].Point]))

print("Creating surfaces")
### LE SURFACE

LESurfaces=[]
for i in range(2,len(LELines[:-1])):#Start from airfoils, not cylinders
	LESurfaces.append(Part.makeRuledSurface(LELines[i],LELines[i+1]))

LE=Part.Compound(LESurfaces)
#LE=Part.makeLoft(LELines)

Part.show(LE)

##### EXTRADOS SURFACE
extradosSurfaces=[]
for i in range(len(extradosLine[:-1])):
	extradosSurfaces.append(Part.makeRuledSurface(extradosLine[i],extradosLine[i+1]))

extrados=Part.Compound(extradosSurfaces)
#extrados=Part.makeLoft(extradosLine)
#Part.show(extrados)

#### INTRADOS SURFACE
intradosSurfaces=[]
for i in range(len(intradosLine[:-1])):
	intradosSurfaces.append(Part.makeRuledSurface(intradosLine[i],intradosLine[i+1]))

intrados=Part.Compound(intradosSurfaces)
#intrados=Part.makeLoft(intradosLine)
#Part.show(intrados)

#### TIP SURFACE

tip=Part.makeRuledSurface(extradosLine[-1],intradosLine[-1])
Part.show(tip)

##### ROOT SURFACE

root=Part.makeRuledSurface(extradosLine[0],intradosLine[0])

##### TRAILING EDGE
TESurfaces=[]
for i in range(len(TELines[:-1])):
	TESurfaces.append(Part.makeRuledSurface(TELines[i],TELines[i+1]))

TE=Part.Compound(TESurfaces)
#TE=Part.makeLoft(TELines)

TESurfacesRef=[]#Refinement surface, no refinement on cylinder
for i in range(2,len(TELines[:-1])):#Start from airfoils, not cylinders
	TESurfacesRef.append(Part.makeRuledSurface(TELines[i],TELines[i+1]))

TERefinement=Part.Compound(TESurfacesRef)
Part.show(TERefinement)

print("Creating rotating domain")
rotorLengthX = 15
rotorLengthY = 15
rotorLengthZ = 40

rotor = Part.makeBox(rotorLengthX,rotorLengthY,rotorLengthZ)
#rotor = doc.addObject("Part::Box","rotor")
#rotor.Length = rotorLengthX
#rotor.Width = rotorLengthY
#rotor.Height = rotorLengthZ
#rotor.Placement.Base = FreeCAD.Vector(-rotorLengthX/2,-rotorLengthY/2,0)
rotor.translate(Base.Vector(-rotorLengthX/2,-rotorLengthY/2,0))

print("Creating static domain")
statorLengthX = 30*span
statorLengthY = 10*span
statorLengthZ = 10*span

stator = Part.makeBox(statorLengthX,statorLengthY,statorLengthZ)
#stator = doc.addObject("Part::Box","stator")
#stator.Length = statorLengthX
#stator.Width = statorLengthY
#stator.Height = statorLengthZ
#stator.Placement.Base = FreeCAD.Vector(-10*span,-statorLengthY/2,-statorLengthZ/2)
stator.translate(Base.Vector(-10*span,-statorLengthY/2,-statorLengthZ/2))

print("Creating blade")
### Use this if the blade cuts the cyclic : can create issues
#wing=Part.makeShell(intrados.Faces+extrados.Faces+TE.Faces)
#wing=wing.common(cylinder)
### Use this if blade does not cut cyclic
wing=Part.makeShell(intrados.Faces+extrados.Faces+TE.Faces+root.Faces)

Part.show(wing)

wingSolid=Part.makeSolid(Part.makeShell(intrados.Faces+extrados.Faces+TE.Faces+tip.Faces+root.Faces))

#print("Cutting domain")
#idx=[x.CenterOfMass[1] for x in cylinder.Faces].index(min([x.CenterOfMass[1] for x in cylinder.Faces]))
#cyclic1=cylinder.Faces[idx]
#cyclic1Cut=cyclic1.cut(wingSolid)
#Part.show(cyclic1Cut)

#idx=[x.CenterOfMass[1] for x in cylinder.Faces].index(max([x.CenterOfMass[1] for x in cylinder.Faces]))
#cyclic2=cylinder.Faces[idx]
#cyclic2Cut=cyclic2.cut(wingSolid)
#Part.show(cyclic2Cut)

print("Ordering rotating domain faces")
idx=[x.CenterOfMass[0] for x in rotor.Faces].index(min([x.CenterOfMass[0] for x in rotor.Faces]))
rotor_inlet=rotor.Faces[idx]
Part.show(rotor_inlet)

idx=[x.CenterOfMass[0] for x in rotor.Faces].index(max([x.CenterOfMass[0] for x in rotor.Faces]))
rotor_outlet=rotor.Faces[idx]
Part.show(rotor_outlet)

idx=[x.CenterOfMass[1] for x in rotor.Faces].index(max([x.CenterOfMass[1] for x in rotor.Faces]))
rotor_side1=rotor.Faces[idx]
Part.show(rotor_side1)

idx=[x.CenterOfMass[1] for x in rotor.Faces].index(min([x.CenterOfMass[1] for x in rotor.Faces]))
rotor_side2=rotor.Faces[idx]
Part.show(rotor_side2)

idx=[x.CenterOfMass[2] for x in rotor.Faces].index(max([x.CenterOfMass[2] for x in rotor.Faces]))
rotor_side3=rotor.Faces[idx]
Part.show(rotor_side3)

idx=[x.CenterOfMass[2] for x in rotor.Faces].index(min([x.CenterOfMass[2] for x in rotor.Faces]))
rotor_side4=rotor.Faces[idx]
Part.show(rotor_side4)

print("Ordering static domain faces")
idx=[x.CenterOfMass[0] for x in stator.Faces].index(min([x.CenterOfMass[0] for x in stator.Faces]))
stator_inlet=stator.Faces[idx]
Part.show(stator_inlet)

idx=[x.CenterOfMass[0] for x in stator.Faces].index(max([x.CenterOfMass[0] for x in stator.Faces]))
stator_outlet=stator.Faces[idx]
Part.show(stator_outlet)

idx=[x.CenterOfMass[1] for x in stator.Faces].index(max([x.CenterOfMass[1] for x in stator.Faces]))
stator_side1=stator.Faces[idx]
Part.show(stator_side1)

idx=[x.CenterOfMass[1] for x in stator.Faces].index(min([x.CenterOfMass[1] for x in stator.Faces]))
stator_side2=stator.Faces[idx]
Part.show(stator_side2)

idx=[x.CenterOfMass[2] for x in stator.Faces].index(max([x.CenterOfMass[2] for x in stator.Faces]))
stator_side3=stator.Faces[idx]
Part.show(stator_side3)

idx=[x.CenterOfMass[2] for x in stator.Faces].index(min([x.CenterOfMass[2] for x in stator.Faces]))
stator_side4=stator.Faces[idx]
Part.show(stator_side4)

print("Exporting")
Mesh.export([doc.getObject("Shape")],u"./LE.stl")
Mesh.export([doc.getObject("Shape002")],u"./TE.stl")

Mesh.export([doc.getObject("Shape003")],u"./foil.ast")
Mesh.export([doc.getObject("Shape001")],u"./tip.ast")
Mesh.export([doc.getObject("Shape004")],u"./rotor_inlet.ast")
Mesh.export([doc.getObject("Shape005")],u"./rotor_outlet.ast")
Mesh.export([doc.getObject("Shape006")],u"./rotor_side1.ast")
Mesh.export([doc.getObject("Shape007")],u"./rotor_side2.ast")
Mesh.export([doc.getObject("Shape008")],u"./rotor_side3.ast")
Mesh.export([doc.getObject("Shape009")],u"./rotor_side4.ast")
Mesh.export([doc.getObject("Shape010")],u"./stator_inlet.ast")
Mesh.export([doc.getObject("Shape011")],u"./stator_outlet.ast")
Mesh.export([doc.getObject("Shape012")],u"./stator_side1.ast")
Mesh.export([doc.getObject("Shape013")],u"./stator_side2.ast")
Mesh.export([doc.getObject("Shape014")],u"./stator_side3.ast")
Mesh.export([doc.getObject("Shape015")],u"./stator_side4.ast")

os.system('sed -i -e "s#solid Mesh#solid foil#g" foil.ast')
os.system('sed -i -e "s#solid Mesh#solid tip#g" tip.ast')

os.system('sed -i -e "s#solid Mesh#solid rotor_inlet#g" rotor_inlet.ast')
os.system('sed -i -e "s#solid Mesh#solid rotor_outlet#g" rotor_outlet.ast')
os.system('sed -i -e "s#solid Mesh#solid rotor_side1#g" rotor_side1.ast')
os.system('sed -i -e "s#solid Mesh#solid rotor_side2#g" rotor_side2.ast')
os.system('sed -i -e "s#solid Mesh#solid rotor_side3#g" rotor_side3.ast')
os.system('sed -i -e "s#solid Mesh#solid rotor_side4#g" rotor_side4.ast')

os.system('sed -i -e "s#solid Mesh#solid stator_inlet#g" stator_inlet.ast')
os.system('sed -i -e "s#solid Mesh#solid stator_outlet#g" stator_outlet.ast')
os.system('sed -i -e "s#solid Mesh#solid stator_side1#g" stator_side1.ast')
os.system('sed -i -e "s#solid Mesh#solid stator_side2#g" stator_side2.ast')
os.system('sed -i -e "s#solid Mesh#solid stator_side3#g" stator_side3.ast')
os.system('sed -i -e "s#solid Mesh#solid stator_side4#g" stator_side4.ast')




os.system('cat rotor_inlet.ast rotor_outlet.ast rotor_side1.ast rotor_side2.ast rotor_side3.ast rotor_side4.ast foil.ast tip.ast > rotor.stl')
os.system('cat stator_inlet.ast stator_outlet.ast stator_side1.ast stator_side2.ast stator_side3.ast stator_side4.ast > stator.stl')

exit()
