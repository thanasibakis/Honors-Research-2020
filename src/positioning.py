import pandas as pd
import numpy as np
import sklearn.decomposition
from scipy import signal
#from scipy.integrate import simps

# points: Nx3 matrix of x,y,z points
# vec: 3-tuple
# Projects points onto a plane perpendicular to vec,
# returning Nx2 matrix of 2D points
def project_3D_to_2D(points, vec):
    P = np.array([vec[1], -vec[0], 0])
    Q = np.array([vec[0] * vec[2], vec[1] * vec[2], -(vec[0] ** 2 + vec[1] ** 2)])

    P /= np.sqrt(np.sum(P ** 2))
    Q /= np.sqrt(np.sum(Q ** 2))

    proj_mat = np.vstack((P, Q)).T
    pts_on_plane = np.matmul(points, proj_mat)

    return pts_on_plane

# Filter and integrate a column (high pass filter removes low freq noise,
#   aka the constant drift that the sensor reports... keeping just the interesting motion we do)
# https://forums.adafruit.com/viewtopic.php?f=8&t=81842&hilit=bno055+position&start=0#p414708
def filter_and_integrate(col, time):
    samp_rate = col.shape[0] / (time.max() - time.min())
    b, a = signal.butter(5, 0.36 * 2 / samp_rate, "high")
    col_filtered = signal.filtfilt(b, a, col)

    return np.cumsum(col_filtered / samp_rate) # simps(col_filtered, time) ?

# Get the principal components and rotation matrix of the given dataset
def PCA(df):
    pca = sklearn.decomposition.PCA()
    components = pca.fit_transform(df)
    rotation = pca.components_.T

    components = pd.DataFrame(components, columns=(f"PC{i}" for i,_ in enumerate(df.columns)))

    return rotation, components

# a 3D matrix, each R[:, :, i] is the rotation matrix of quaternion sample i
def quaternions_as_rotation_matrix(qw, qx, qy, qz):
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

# M: an Nx3 matrix
# R: a 3x3xN array
# Rotates each row in M using the corresponding 3x3 rotation matrix in R
def rotate_each_row(M, R):
    colnames = M.columns
    M = M.to_numpy()
    M2 = M.copy()

    for row in range(M.shape[0]):
        M2[row, :] = np.matmul(M[row, :], R[:, :, row])
        
    return pd.DataFrame(M2, columns=colnames)