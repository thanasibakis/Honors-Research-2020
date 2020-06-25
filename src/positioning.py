import pandas as pd
import numpy as np
import sklearn.decomposition
from scipy import signal

# Projects vector of 3D points onto a plane perpendicular to vec (returning 2D points)
def project_3D_to_2D(data, vec):
    P = np.array([vec[1], -vec[0], 0])
    Q = np.array([vec[0] * vec[2], vec[1] * vec[2], -(vec[0] ** 2 + vec[1] ** 2)])

    P /= np.sqrt(np.sum(P ** 2))
    Q /= np.sqrt(np.sum(Q ** 2))

    proj_mat = np.vstack((P, Q)).T
    pts_on_plane = np.matmul(data, proj_mat)

    return pts_on_plane

# Processes acceleration data to obtain position data
def prepare_data(data):
    R = rot_mat(data.qw, data.qx, data.qy, data.qz)
    accel = rotate(data[["ax", "ay", "az"]], R)

    data = data.assign(
        lax=accel.ax,
        lay=accel.ay,
        laz=accel.az,
        time_sec=data.Timestamp
    )
    data = data.assign(
        vx=integ(data.lax, data.time_sec),
        vy=integ(data.lay, data.time_sec),
        vz=integ(data.laz, data.time_sec)
    )
    data = data.assign(
        x=integ(data.vx, data.time_sec),
        y=integ(data.vy, data.time_sec),
        z=integ(data.vz, data.time_sec)
    )
    data = data.assign(
        d=np.sqrt(data.x**2 + data.y**2 + data.z**2)
    )

    return data

# Filter and integrate a column (high pass filter removes low freq noise,
#   aka the constant drift that the sensor reports... keeping just the interesting motion we do)
# https://forums.adafruit.com/viewtopic.php?f=8&t=81842&hilit=bno055+position&start=0#p414708
def integ(col, time):
    samp_rate = col.shape[0] / (time.max() - time.min())
    b, a = signal.butter(5, 0.36 * 2 / samp_rate, "high")
    col_filtered = signal.filtfilt(b, a, col)

    return np.cumsum(col_filtered / samp_rate)

# Get the principal components and rotation matrix of the given dataset
def PCA(data, *cols):
    pca = sklearn.decomposition.PCA()
    components = pca.fit_transform(data[list(cols)])
    rotation = pca.components_.T

    components = pd.DataFrame(components, columns=("PC1", "PC2", "PC3")) \
        .assign(time_sec = data.time_sec)

    return rotation, components

# a 3D matrix, each R[:, :, i] is the rotation matrix of sample i
def rot_mat(qw, qx, qy, qz):
    q_norm = np.sqrt(qw ** 2 + qx ** 2 + qy ** 2 + qz ** 2)
    qw /= q_norm
    qx /= q_norm
    qy /= q_norm
    qz /= q_norm

    R = np.zeros((3, 3, qw.shape[0]))
    R[0, 0, :] = 1 - 2*(qy**2 + qz**2)
    R[1, 0, :] = 2*(qx*qy + qz*qw)
    R[2, 0, :] = 2*(qx*qz - qy*qw)
    R[0, 1, :] = 2*(qx*qy - qz*qw)
    R[1, 1, :] = 1 - 2*(qx**2 + qz**2)
    R[2, 1, :] = 2*(qy*qz + qx*qw)
    R[0, 2, :] = 2*(qx*qz + qy*qw)
    R[1, 2, :] = 2*(qy*qz - qx*qw)
    R[2, 2, :] = 1 - 2 * (qx ** 2 + qy ** 2)
    
    return R

# Applies a rotation matrix from rot_mat()
def rotate(M, R):
    colnames = M.columns
    M = M.to_numpy()
    M2 = M.copy()

    for row in range(M.shape[0]):
        M2[row, :] = np.matmul(M[row, :], R[:, :, row])
        
    return pd.DataFrame(M2, columns=colnames)