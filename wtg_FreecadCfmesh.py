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
domainUp=10.*span
domainDown=20*span	#40.*span
domainHeight=10*span	#20.*span

#cylinder=Part.makeCylinder(domainHeight/10,domainUp/10+domainDown/10,Base.Vector(-domainUp/10,0,0),Base.Vector(1,0,0),80)
cylinder=Part.makeCylinder(2*span,2*span,Base.Vector(-span,0,0),Base.Vector(1,0,0),80)
cylinder.rotate(Base.Vector(0,0,0),Base.Vector(1,0,0),-40)

print("Creating static domain")
static_cylinder=Part.makeCylinder(domainHeight,domainUp+domainDown,Base.Vector(-domainUp,0,0),Base.Vector(1,0,0),360)

print("Creating blade")
### Use this if the blade cuts the cyclic : can create issues
#wing=Part.makeShell(intrados.Faces+extrados.Faces+TE.Faces)
#wing=wing.common(cylinder)
### Use this if blade does not cut cyclic
wing=Part.makeShell(intrados.Faces+extrados.Faces+TE.Faces+root.Faces)

Part.show(wing)

wingSolid=Part.makeSolid(Part.makeShell(intrados.Faces+extrados.Faces+TE.Faces+tip.Faces+root.Faces))

print("Cutting domain")
idx=[x.CenterOfMass[1] for x in cylinder.Faces].index(min([x.CenterOfMass[1] for x in cylinder.Faces]))
cyclic1=cylinder.Faces[idx]
cyclic1Cut=cyclic1.cut(wingSolid)
Part.show(cyclic1Cut)

idx=[x.CenterOfMass[1] for x in cylinder.Faces].index(max([x.CenterOfMass[1] for x in cylinder.Faces]))
cyclic2=cylinder.Faces[idx]
cyclic2Cut=cyclic2.cut(wingSolid)
Part.show(cyclic2Cut)

print("Ordering rotating domain faces")
idx=[x.CenterOfMass[0] for x in cylinder.Faces].index(min([x.CenterOfMass[0] for x in cylinder.Faces]))
inlet=cylinder.Faces[idx]
Part.show(inlet)

idx=[x.CenterOfMass[0] for x in cylinder.Faces].index(max([x.CenterOfMass[0] for x in cylinder.Faces]))
outlet=cylinder.Faces[idx]
Part.show(outlet)

idx=[x.CenterOfMass[2] for x in cylinder.Faces].index(max([x.CenterOfMass[2] for x in cylinder.Faces]))
top=cylinder.Faces[idx]
Part.show(top)

print("Ordering static domain faces")
idx=[x.CenterOfMass[0] for x in static_cylinder.Faces].index(min([x.CenterOfMass[0] for x in static_cylinder.Faces]))
static_inlet=static_cylinder.Faces[idx]
Part.show(static_inlet)

idx=[x.CenterOfMass[0] for x in static_cylinder.Faces].index(max([x.CenterOfMass[0] for x in static_cylinder.Faces]))
static_outlet=static_cylinder.Faces[idx]
Part.show(static_outlet)

idx=[x.CenterOfMass[2] for x in static_cylinder.Faces].index(min([abs(x.CenterOfMass[2]) for x in static_cylinder.Faces]))
static_side=static_cylinder.Faces[idx]
Part.show(static_side)

print("Exporting")
Mesh.export([doc.getObject("Shape")],u"./LE.stl")
Mesh.export([doc.getObject("Shape002")],u"./TE.stl")

Mesh.export([doc.getObject("Shape003")],u"./foil.ast")
Mesh.export([doc.getObject("Shape001")],u"./tip.ast")
Mesh.export([doc.getObject("Shape004")],u"./cyc1.ast")
Mesh.export([doc.getObject("Shape005")],u"./cyc2.ast")
Mesh.export([doc.getObject("Shape006")],u"./inlet.ast")
Mesh.export([doc.getObject("Shape007")],u"./outlet.ast")
Mesh.export([doc.getObject("Shape008")],u"./top.ast")
Mesh.export([doc.getObject("Shape009")],u"./static_inlet.ast")
Mesh.export([doc.getObject("Shape010")],u"./static_outlet.ast")
Mesh.export([doc.getObject("Shape011")],u"./static_side.ast")

os.system('sed -i -e "s#solid Mesh#solid inlet#g" inlet.ast')
os.system('sed -i -e "s#solid Mesh#solid outlet#g" outlet.ast')
os.system('sed -i -e "s#solid Mesh#solid cyc1#g" cyc1.ast')
os.system('sed -i -e "s#solid Mesh#solid cyc2#g" cyc2.ast')
os.system('sed -i -e "s#solid Mesh#solid top#g" top.ast')
os.system('sed -i -e "s#solid Mesh#solid foil#g" foil.ast')
os.system('sed -i -e "s#solid Mesh#solid tip#g" tip.ast')
os.system('sed -i -e "s#solid Mesh#solid static_inlet#g" static_inlet.ast')
os.system('sed -i -e "s#solid Mesh#solid static_outlet#g" static_outlet.ast')
os.system('sed -i -e "s#solid Mesh#solid static_side#g" static_side.ast')


os.system('cat inlet.ast outlet.ast top.ast cyc1.ast cyc2.ast foil.ast tip.ast > domain.stl')
os.system('cat static_inlet.ast static_outlet.ast static_side.ast > static_domain.stl')

exit()
