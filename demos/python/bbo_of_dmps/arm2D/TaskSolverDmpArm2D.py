# This file is part of DmpBbo, a set of libraries and programs for the
# black-box optimization of dynamical movement primitives.
# Copyright (C) 2018 Freek Stulp
#
# DmpBbo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# DmpBbo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with DmpBbo.  If not, see <http://www.gnu.org/licenses/>.
""" Module for the TaskSolverDmp class. """

import copy

import numpy as np
from matplotlib import pyplot as plt

from demos.python.bbo_of_dmps.arm2D.TaskViapointArm2D import TaskViapointArm2D
from dmpbbo.bbo_of_dmps.TaskSolverDmp import TaskSolverDmp

class TaskSolverDmpArm2D(TaskSolverDmp):
    """ TaskSolver that integrates a DMP for a 2D arm.

    """

    def __init__(self, dmp, dt, integrate_dmp_beyond_tau_factor, link_lengths=None):
        super().__init__(dmp, dt, integrate_dmp_beyond_tau_factor)
        if not link_lengths:
            n_dofs = dmp.dim_dmp()
            # Every link has same length, and they sum to 1.0
            link_lengths = np.full(n_dofs, 1.0/n_dofs)

        # N link lengths => N joints
        assert(len(link_lengths) == dmp.dim_dmp())
        self.link_lengths = link_lengths

    def perform_rollout_dmp(self, dmp):
        """ Perform one rollout for a DMP.

        @param dmp: The DMP to integrate.
        @return: The trajectory generated by the DMP as a matrix.
        """
        ts = np.linspace(0.0, self._integrate_time, self._n_time_steps)
        xs, xds, _, _ = dmp.analytical_solution(ts)
        joint_trajs = dmp.states_as_trajectory(ts, xs, xds)
        # We have the joint trajectories as a Trajectory. Convert them to end-eff.
        y_links = self.angles_to_link_positions(joint_trajs.ys, self.link_lengths)

        # Cost-vars now contains: ts, joint pos/vel/acc, endeff pos
        cost_vars = np.column_stack((joint_trajs.as_matrix(), y_links))
        return cost_vars

    def perform_rollout(self, sample, **kwargs):
        """ Perform rollouts, that is, given a set of samples, determine all the variables that
        are relevant to evaluating the cost function.

        @param sample: The sample to perform the rollout for
        @return: The variables relevant to computing the cost.
        """
        self._dmp.set_param_vector(sample)
        return self.perform_rollout_dmp(self._dmp)

    @staticmethod
    def angles_to_link_positions(angles, link_lengths):
        n_time_steps = angles.shape[0]
        n_dofs = angles.shape[1]
        links_x = np.zeros((n_time_steps, n_dofs+1))
        links_y = np.zeros((n_time_steps, n_dofs+1))
        for tt in range(n_time_steps):
            sum_angles = 0.0
            for i_dof in range(n_dofs):
                sum_angles += angles[tt, i_dof]
                l = link_lengths[i_dof]
                links_x[tt, i_dof + 1] = links_x[tt, i_dof] + np.cos(sum_angles) * l
                links_y[tt, i_dof + 1] = links_y[tt, i_dof] + np.sin(sum_angles) * l

        # Format for each row: x_0, y_0, x_1, y_1 ... x_endeff,  y_endeff
        links_xyxyxy = np.zeros((n_time_steps, 2*(n_dofs+1)))
        for i_link in range(n_dofs+1):
            links_xyxyxy[:, 2 * i_link + 0]  = links_x[:,i_link]
            links_xyxyxy[:, 2 * i_link + 1] =  links_y[:, i_link]
        return links_xyxyxy

def main():
    """ Main function of the script. """
    from dmpbbo.dmps.Trajectory import Trajectory # Only needed when main is called

    n_dofs = 7
    duration = 0.8
    angles_init = np.full(n_dofs, 0.0)
    angles_goal = np.full(n_dofs, np.pi/n_dofs)
    angles_goal[0] *= 0.5
    ts = np.linspace(0, duration, 51)
    angles_min_jerk = Trajectory.from_min_jerk(ts, angles_init, angles_goal)
    link_lengths = np.full(n_dofs, 1.0 / n_dofs)

    from dmpbbo.functionapproximators.FunctionApproximatorRBFN import FunctionApproximatorRBFN
    from dmpbbo.dmps.Dmp import Dmp

    intersection_height = 0.9
    n_basis = 5
    function_apps = [FunctionApproximatorRBFN(n_basis, intersection_height) for _ in range(n_dofs)]
    dmp = Dmp.from_traj(angles_min_jerk, function_apps)
    dmp.set_selected_param_names("weights")
    sample = dmp.get_param_vector()
    solver = TaskSolverDmpArm2D(dmp, 0.01, 1.5*duration)

    cost_vars = solver.perform_rollout(sample)
    task = TaskViapointArm2D(n_dofs, np.full(2,0.5))
    h, ax = task.plot_rollout(cost_vars)
    plt.setp(h,color='blue')

    perturbed_sample =  np.random.normal(sample, np.abs(0.3*sample))
    cost_vars = solver.perform_rollout(perturbed_sample)
    task = TaskViapointArm2D(n_dofs, np.full(2,0.5))
    h, ax = task.plot_rollout(cost_vars, ax)

    plt.show()


if __name__ == "__main__":
    main()