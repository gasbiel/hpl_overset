import os
import shutil
import math
pi=math.pi
import numpy
from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
import subprocess
import matplotlib
matplotlib.use('Agg')###save plots through ssh
from pylab import *
######################Variables##########################""
case=10221.0
force_crit=0.2
#workingdir=""
dt=0.0001
Pdyn=60.205
c=1.0
alpha0=5.0
alphaAmpli=5.0
omega=2.0
nCor=2
nonOrtho=2
period=2*pi/omega

force=numpy.array([list(map(float,l.replace('(','').replace(')','').replace('\t',' ').split())) for l in subprocess.getoutput('tail -n +5 postProcessing/forces_foil/0/force.dat').strip('\n').split('\n')])
moment=numpy.array([list(map(float,l.replace('(','').replace(')','').replace('\t',' ').split())) for l in subprocess.getoutput('tail -n +5 postProcessing/forces_foil/0/moment.dat').strip('\n').split('\n')])

#h=numpy.array([map(float,l.split()) for l in subprocess.getoutput('tail -n +4 postProcessing/forces_foil/0/force.dat | awk \'{gsub(/[()]/,"");gsub(/,/," ");$17=(cos('+str(alpha0*pi/180)+')*($3+$6)-sin('+str(alpha0*pi/180)+')*($2+$5))/'+str(Pdyn)+';$18=(cos('+str(alpha0*pi/180)+')*($2+$5)+sin('+str(alpha0*pi/180)+')*($3+$6))/'+str(Pdyn)+';$19=($13+$16)/'+str(Pdyn*c)+';$2=$3=$4=$5=$6=$7=$8=$9=$10=$11=$12=$13=$14=$15=$16="";{print}}\' ').strip('\n').split('\n')])
t=force[:,0]
alpha=alpha0+alphaAmpli*numpy.sin(omega*t)
Cl=(numpy.cos(alpha0*pi/180)*force[:,2]-numpy.sin(alpha0*pi/180)*force[:,1])/Pdyn
Cd=(numpy.cos(alpha0*pi/180)*force[:,1]+numpy.sin(alpha0*pi/180)*force[:,2])/Pdyn
Cm=-moment[:,3]/(Pdyn*c)#negative for nose down

numpy.savetxt('tAlphaClCdCm',numpy.vstack((t,alpha,Cl,Cd,Cm)).T)

if t[-1]>period*1.1:
	inter=500
	tInterp=numpy.linspace(0,t[-1],inter*round(t[-1]/period))
	alphaInterp=numpy.interp(tInterp,t,alpha)
	ClInterp=numpy.interp(tInterp,t,Cl)
	CdInterp=numpy.interp(tInterp,t,Cd)
	CmInterp=numpy.interp(tInterp,t,Cm)
	ClM=numpy.array([numpy.average(ClInterp[(inter+x)::inter]) for x in range(inter)])
	CdM=numpy.array([numpy.average(CdInterp[(inter+x)::inter]) for x in range(inter)])
	CmM=numpy.array([numpy.average(CmInterp[(inter+x)::inter]) for x in range(inter)])

	for coef in [Cl,Cd,Cm]:
		plot(alpha, coef)
		xlabel('incidence')
		grid(True)
		if (coef==Cl).all():
			plot(alphaInterp[:inter],ClM)
			expUp=numpy.loadtxt('mccroskey/'+str(int(case))+'Clup.dat')
			expDown=numpy.loadtxt('mccroskey/'+str(int(case))+'Cldown.dat')
			plot(expUp[:,0],expUp[:,1])
			plot(expDown[:,0],expDown[:,1])
			ylabel('Cl')
			title('lift coefficient')
			savefig('Cl'+str(omega)+'.png')
		elif (coef==Cd).all():
			plot(alphaInterp[:inter],CdM)
			expUp=numpy.loadtxt('mccroskey/'+str(int(case))+'Cdup.dat')
			expDown=numpy.loadtxt('mccroskey/'+str(int(case))+'Cddown.dat')
			plot(expUp[:,0],expUp[:,1])
			plot(expDown[:,0],expDown[:,1])
			ylabel('Cd')
			title('drag coefficient')
			savefig('Cd'+str(omega)+'.png')
		elif (coef==Cm).all():
			plot(alphaInterp[:inter],CmM)
			ylabel('Cm')
			title('moment coefficient')
			savefig('Cm'+str(omega)+'.png')
		clf()

	for coef in [1,2,3]:
		xlabel('incidence')
		grid(True)
		if coef==1:
			plot(alphaInterp[:inter],ClM)
			expUp=numpy.loadtxt('mccroskey/'+str(int(case))+'Clup.dat')
			expDown=numpy.loadtxt('mccroskey/'+str(int(case))+'Cldown.dat')
			plot(expUp[:,0],expUp[:,1])
			plot(expDown[:,0],expDown[:,1])
			ylabel('Cl')
			title('lift coefficient')
			savefig('ClFinal'+str(omega)+'.png')
		elif coef==2:
			plot(alphaInterp[:inter],CdM)
			expUp=numpy.loadtxt('mccroskey/'+str(int(case))+'Cdup.dat')
			expDown=numpy.loadtxt('mccroskey/'+str(int(case))+'Cddown.dat')
			plot(expUp[:,0],expUp[:,1])
			plot(expDown[:,0],expDown[:,1])
			ylabel('Cd')
			title('drag coefficient')
			savefig('CdFinal'+str(omega)+'.png')
		elif coef==3:
			plot(alphaInterp[:inter],CmM)
			ylabel('Cm')
			title('moment coefficient')
			savefig('CmFinal'+str(omega)+'.png')
		clf()

	resp=subprocess.getoutput('grep "ClockTime = \|p, Initial residual = " log.solver  | cut -d "," -f 2 | cut -d " " -f 5').strip().split('\n\n')
	resp=[list(map(float,x.split())) for x in resp]
	resp_final=[x[-nCor*(nonOrtho+1)-1] for x in resp]

#resUx=subprocess.getoutput('grep "ClockTime = \|Ux, Initial residual = " log.solver  | cut -d "," -f 2 | cut -d " " -f 5').strip().split('\n\n')
#resUx=[list(map(float,x.split())) for x in resUx]
#resUx_final=[x[-2] for x in resUx]

#resUy=subprocess.getoutput('grep "ClockTime = \|Uy, Initial residual = " log.solver  | cut -d "," -f 2 | cut -d " " -f 5').strip().split('\n\n')
#resUy=[list(map(float,x.split())) for x in resUy]
#resUy_final=[x[-2] for x in resUy]

	plot(resp_final,label='residual p')
#	plot(resUx_final,label='residual Ux')
#	plot(resUy_final,label='residual Uy')
	xlabel('iteration')
	grid(True)
	ylabel('residual')
	legend()
	ax = plt.gca()
	ax.set_yscale('log')
	savefig('residual'+str(omega)+'.png')
	clf()


	if t[-1]>period*2.1:
		prevForces=numpy.loadtxt('AveragetAlphaClCdCm')
		deltaCl=ClM-prevForces[:,2]
		print(os.path.basename(os.getcwd()))
		print(max(abs(deltaCl)))
		if max(abs(deltaCl)) < force_crit:
			control = ParsedParameterFile('system/controlDict')
			control['stopAt']='noWriteNow'
			control.writeFile()
			f=open('convergence_status','w')
			f.write('forces converged\n')
			f.close()

	numpy.savetxt('AveragetAlphaClCdCm',numpy.vstack((tInterp[:inter],alphaInterp[:inter],ClM,CdM,CmM)).T)
	export=numpy.vstack((t[t>(t[-1]-period)],alpha[t>(t[-1]-period)],Cl[t>(t[-1]-period)],Cd[t>(t[-1]-period)],Cm[t>(t[-1]-period)])).T
	numpy.savetxt('lasttAlphaClCdCm',export)
