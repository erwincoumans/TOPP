# -*- coding: utf-8 -*-
# Copyright (C) 2013 Quang-Cuong Pham <cuong.pham@normalesup.org>
#
# This file is part of the Time-Optimal Path Parameterization (TOPP) library.
# TOPP is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
sys.path.append('..')

import TOPPbindings
import TOPPpy
import TOPPopenravepy
import time
import string
from pylab import *
from numpy import *
from openravepy import *

ion()

########################### Robot ################################
env = Environment() # create openrave environment
#------------------------------------------#
#robotfile = "../robots/hrp4r.dae"
robotfile = "../robots/arm.robot.xml"
env.Load(robotfile)
robot=env.GetRobots()[0]
#------------------------------------------#
grav=[0,0,-9.8]
n=robot.GetDOF()
dof_lim=robot.GetDOFLimits()
vel_lim=robot.GetDOFVelocityLimits()
robot.SetDOFLimits(-10*ones(n),10*ones(n))
robot.SetDOFVelocityLimits(100*vel_lim)


############################ Tunings ############################
discrtimestep = 0.01
integrationtimestep = 0.01
reparamtimestep = 0.01
passswitchpointnsteps = 5
tuningsstring = "%f %f %f %d"%(discrtimestep,integrationtimestep,reparamtimestep,passswitchpointnsteps)


############################ Trajectory ############################
#------------------------------------------#
q0=[0,0,0,0]
q1=[ 2.32883,  1.61082,  0.97706,  1.94169]
v=1
qd0=[v,v,v,v]
qd1=[v,v,v,v]
T = 1.5
trajectorystring = "%f\n%d"%(T,4)
for i in range(4):
    a,b,c,d = TOPPpy.Interpolate3rdDegree(q0[i],q1[i],qd0[i],qd1[i],T)
    trajectorystring += "\n%f %f %f %f"%(d,c,b,a)
#------------------------------------------#
traj0 = TOPPpy.PiecewisePolynomialTrajectory.FromString(trajectorystring)



############################ Constraints ############################
#------------------------------------------#
taumin = array([0,0,0,0])
taumax = array([0,0,0,0])
xmax = 1
xmin = -1
ymax = 1
ymin = -1
zmplimits = [xmin,xmax,ymin,ymax]
vmax = [5,5,5,5]
t0 = time.time()
constraintstring = string.join([str(x) for x in taumin]) + "\n" + string.join([str(a) for a in taumax]) + "\n" +  string.join([str(a) for a in zmplimits]) + "\n" + string.join([str(a) for a in vmax])
#------------------------------------------#


############################ Run TOPP ############################
t1 = time.time()
x = TOPPbindings.TOPPInstance("ZMPTorqueLimits",constraintstring,trajectorystring,tuningsstring,robot);

t2 = time.time()
ret = x.RunComputeProfiles(0,0)
t3 = time.time()

if(ret == 1):
    x.ReparameterizeTrajectory()

t4 = time.time()

################ Plotting the MVC and the profiles #################
x.WriteProfilesList()
x.WriteSwitchPointsList()
profileslist = TOPPpy.ProfilesFromString(x.resprofilesliststring)
switchpointslist = TOPPpy.SwitchPointsFromString(x.switchpointsliststring)
TOPPpy.PlotProfiles(profileslist,switchpointslist,5)


##################### Plotting the trajectories #####################
if(ret == 1):
    x.WriteResultTrajectory()
    traj1 = TOPPpy.PiecewisePolynomialTrajectory.FromString(x.restrajectorystring)
    dtplot = 0.01
    TOPPpy.PlotKinematics(traj0,traj1,dtplot,vmax)
    #TOPPopenravepy.PlotTorques(robot,traj0,traj1,dtplot,taumin,taumax,3)
    TOPPopenravepy.PlotZMP(robot,traj0,traj1,zmplimits,dtplot,4)


print "\n--------------"
print "Python preprocessing: ", t1-t0
print "Building TOPP Instance: ", t2-t1
print "Compute profiles: ", t3-t2
print "Reparameterize trajectory: ", t4-t3
print "Total: ", t4-t0
print "Trajectory duration (estimate): ", x.resduration
print "Trajectory duration: ", traj1.duration

raw_input()
