dt=$(grep -r deltaT log.solver | tail -1 | cut -d ' ' -f 3)
dt=`echo ${dt} | sed -e 's/[eE]+*/\\*10\\^/'`
if [ $(echo "$dt < 0.0000000001" | bc -l) -eq 1 ];
	then echo 'diverged' && sed -i -e 's#stopAt.*endTime#stopAt    writeNow#g' system/controlDict && echo 'Diverged\n' > convergence_status;
fi
