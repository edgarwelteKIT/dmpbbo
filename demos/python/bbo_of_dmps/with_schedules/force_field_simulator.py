import random

import numpy as np
from matplotlib import pyplot as plt


def perform_rollout(dmp_sched, integrate_time, n_time_steps, field_strength, field_max_time):
    ts = np.linspace(0.0, integrate_time, n_time_steps)
    dt = ts[1]

    r = {}  # The rollout containing all relevant  numpy ndarrays
    r['ts'] = ts
    for v in ['ys_des', 'yds_des', 'ydds_des', 'schedules', 'ys_cur', 'ydds_cur', 'yds_cur']:
        r[v] = np.zeros([n_time_steps, dmp_sched.dim_y])
    r['fields'] = np.zeros([n_time_steps, 1])

    x_des, xd_des, sch = dmp_sched.integrate_start_sched()
    des = dmp_sched.states_as_pos_vel_acc(x_des, xd_des)
    for i, v in enumerate(['ys', 'yds', 'ydds']):
        r[v + '_des'][0, :] = des[i]  # Output of integrate_start are values at t=0
        r[v + '_cur'][0, :] = r[v + '_des'][0, :]  # Current at t=0 is equal ot desired
    r['schedules'][0, :] = sch

    for tt in range(1, n_time_steps):
        x_des, xd_des, sch = dmp_sched.integrate_step_sched(dt, x_des)
        r['ys_des'][tt, :], r['yds_des'][tt, :], r['ydds_des'][tt, :] \
            = dmp_sched.states_as_pos_vel_acc(x_des, xd_des)

        # Compute error terms
        y_err = r['ys_cur'][tt - 1, :] - r['ys_des'][tt, :]
        yd_err = r['yds_cur'][tt - 1, :] - r['yds_des'][tt, :]

        # Force due to PD-controller
        r['schedules'][tt, :] = sch
        gain = sch
        r['ydds_cur'][tt, :] = -gain * y_err - np.sqrt(gain) * yd_err

        # Force due to force_field
        time = ts[tt]
        max_time = field_max_time
        w = np.sqrt(0.05*max_time)
        r['fields'][tt, 0] = field_strength * np.exp(-0.5 * np.square(time - max_time) / (w * w))
        r['ydds_cur'][tt, :] += r['fields'][tt, 0]

        # Euler integration
        r['yds_cur'][tt, :] = r['yds_cur'][tt - 1, :] + dt * r['ydds_cur'][tt, :]
        r['ys_cur'][tt, :] = r['ys_cur'][tt - 1, :] + dt * r['yds_cur'][tt, :]

    return r

def main_perform_rollout(field_strength, gains, axs):
    from dmpbbo.dmps.DmpWithSchedules import DmpWithSchedules
    from dmpbbo.dmps.Trajectory import Trajectory
    from dmpbbo.functionapproximators.FunctionApproximatorRBFN import FunctionApproximatorRBFN

    n_time_steps = 51
    tau = 1.0
    y_init = np.array([0.0])
    y_attr = np.array([1.0])
    n_dims = len(y_init)

    ts = np.linspace(0, tau, n_time_steps)
    traj = Trajectory.from_min_jerk(ts, y_init, y_attr)
    schedule = np.full((n_time_steps, n_dims), gains)
    traj.misc = schedule

    function_apps = [FunctionApproximatorRBFN(8, 0.95) for _ in range(n_dims)]
    function_apps_schedules = [FunctionApproximatorRBFN(7, 0.95) for _ in range(n_dims)]
    dmp_sched = DmpWithSchedules.from_traj_sched(traj, function_apps, function_apps_schedules,
                                                 min_schedules=100, max_schedules=2000.0)

    integrate_time = 1.3 * tau
    field_max_time = 0.5 * tau
    r = perform_rollout(dmp_sched, integrate_time, n_time_steps, field_strength, field_max_time)

    h = axs[0].plot(r['ts'], r['fields'])
    axs[0].set_ylabel('force field')
    color = h[0].get_color()

    axs[1].plot(r['ts'], r['schedules'], color=color)
    axs[1].set_ylabel('gains')

    for i, v in enumerate(['ys', 'yds', 'ydds']):
        axs[i+2].plot(r['ts'], r[v+'_des'], '-', color=color)
        axs[i+2].plot(r['ts'], r[v + '_cur'], '--', color=color)
        axs[i+2].set_ylabel(v)


def main():
    field_strengths = [10.0, 100.0]
    gains = [100.0, 1000.0]

    n_rows = 4
    n_cols = 5
    fig = plt.figure(figsize=(5*n_cols, 5*n_rows))
    row = 0
    for field_strength in field_strengths:
        for gain in gains:
            axs = [fig.add_subplot(n_rows, n_cols, 1 + row * n_cols + sp) for sp in range(n_cols)]
            main_perform_rollout(field_strength, gain, axs)
            #for i in range(n_cols):
            #    axs[i].set_xlabel('time')
            axs[0].set_ylim([0, 1.1*max(field_strengths)])
            axs[1].set_ylim([0, 1.1*max(gains)])
            row += 1

    n_rows = 1
    fig = plt.figure(figsize=(5*n_cols, 5*n_rows))
    axs = [fig.add_subplot(n_rows, n_cols, 1 + sp) for sp in range(n_cols)]
    for i in range(10):
        gain = 500.0
        field_strength = random.randrange(-200, 200)
        main_perform_rollout(field_strength, gain, axs)

    plt.show()

if __name__ == "__main__":
    main()