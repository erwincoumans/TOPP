import sys
sys.path.append('..')

import string
from pylab import *
from numpy import *
from openravepy import *
import TOPPbindings
import TOPPpy
import TOPPopenravepy

# Robot
env = Environment()
env.SetViewer('qtcoin')
env.Load('data/lab1.env.xml')
robot = env.GetRobots()[0]
RaveSetDebugLevel(DebugLevel.Debug)
ndof = robot.GetDOF()

# Finding a trajectory using OpenRAVE RRT with constraintparabolicsmooting
vmax = 2 * ones(ndof)
amax = 10* ones(ndof)
robot.SetDOFVelocityLimits(vmax)
robot.SetDOFAccelerationLimits(amax)
robot.SetDOFValues(zeros(ndof))
robot.SetActiveDOFs(range(4)) # set joints the first 4 dofs
params = Planner.PlannerParameters()
params.SetRobotActiveJoints(robot)
params.SetGoalConfig([0.1,pi/2,pi/3,pi/2.1])
# forces parabolic planning with 40 iterations
#params.SetExtraParameters("""<_postprocessing planner="parabolicsmoother">
params.SetExtraParameters("""<_postprocessing planner="constraintparabolicsmoother">
    <_fStepLength>0</_fStepLength>
    <minswitchtime>0.5</minswitchtime>
    <_nmaxiterations>40</_nmaxiterations>
</_postprocessing>""")
planner=RaveCreatePlanner(env,'birrt')
planner.InitPlan(robot, params)
ravetraj0 = RaveCreateTrajectory(env,'')
planner.PlanPath(ravetraj0)
topptraj0 = TOPPopenravepy.FromRaveTraj(robot,ravetraj0)

# Constraints
discrtimestep = 0.005
taumin = zeros(ndof)
taumax = zeros(ndof)
taumin[0:4] = [-30,-50,-25,-15] # Torque limits, only for the shoulder and elbow joints
taumax[0:4] = [30,50,25,15]
constraintstring = str(discrtimestep) + "\n";
constraintstring += string.join([str(v) for v in vmax])
constraintstring += TOPPopenravepy.ComputeTorquesConstraints(robot,topptraj0,taumin,taumax,discrtimestep)

# Run TOPP
x = TOPPbindings.TOPPInstance(None,"QuadraticConstraints",constraintstring,str(topptraj0));
ret = x.RunComputeProfiles(0,0)
if(ret == 1):
    x.ReparameterizeTrajectory()

# Display results
ion()    
x.WriteProfilesList()
x.WriteSwitchPointsList()
profileslist = TOPPpy.ProfilesFromString(x.resprofilesliststring)
switchpointslist = TOPPpy.SwitchPointsFromString(x.switchpointsliststring)
TOPPpy.PlotProfiles(profileslist,switchpointslist,4)
if(ret == 1):
    x.WriteResultTrajectory()
    topptraj1 = TOPPpy.PiecewisePolynomialTrajectory.FromString(x.restrajectorystring)
    dtplot = 0.01
    TOPPpy.PlotKinematics(topptraj0,topptraj1,dtplot,vmax)
    TOPPopenravepy.PlotTorques(robot,topptraj0,topptraj1,dtplot,taumin,taumax,3)
    print "Trajectory duration before TOPP: ", topptraj0.duration
    print "Trajectory duration after TOPP: ", topptraj1.duration
else:
    print "Trajectory is not time-parameterizable"

# Execute trajectory
if(ret == 1):
    spec = ravetraj0.GetConfigurationSpecification()
    ravetraj1 = TOPPopenravepy.ToRaveTraj(robot,spec,topptraj1)
    robot.GetController().SetPath(ravetraj1)

