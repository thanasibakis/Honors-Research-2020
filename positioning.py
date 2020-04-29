import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import seaborn as sns
from helpers import *

data = pd.read_csv("mari-bowing-data/variable-speed.csv")

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

pca_matrix, pca_data = PCA(data, "x", "y", "z")

eig1 = pca_matrix[:, 0]

P = np.array([eig1[1], -eig1[0], 0])
Q = np.array([eig1[0] * eig1[2], eig1[1] * eig1[2], -(eig1[0] ** 2 + eig1[1] ** 2)])

P /= np.sqrt(np.sum(P ** 2))
Q /= np.sqrt(np.sum(Q ** 2))

proj_mat = np.vstack((P, Q)).T

pts_on_plane = np.matmul(data[["x", "y", "z"]].to_numpy(), proj_mat)




fig, ax = plt.subplots(5, 3)

bound = np.amax(np.abs(data[["lax", "lay", "laz"]]))[0]
sns.lineplot(data=data, x="time_sec", y="lax", ax=ax[0, 0])
sns.lineplot(data=data, x="time_sec", y="lay", ax=ax[0, 1])
sns.lineplot(data=data, x="time_sec", y="laz", ax=ax[0, 2])
for i in range(3):
    ax[0, i].set_ylim((-bound, bound))

bound = np.amax(np.abs(data[["vx", "vy", "vz"]]))[0]
sns.lineplot(data=data, x="time_sec", y="vx", ax=ax[1, 0])
sns.lineplot(data=data, x="time_sec", y="vy", ax=ax[1, 1])
sns.lineplot(data=data, x="time_sec", y="vz", ax=ax[1, 2])
for i in range(3):
    ax[1, i].set_ylim((-bound, bound))

bound = np.amax(np.abs(data[["x", "y", "z"]]))[0]
sns.lineplot(data=data, x="time_sec", y="x", ax=ax[2, 0])
sns.lineplot(data=data, x="time_sec", y="y", ax=ax[2, 1])
sns.lineplot(data=data, x="time_sec", y="z", ax=ax[2, 2])
for i in range(3):
    ax[2, i].set_ylim((-bound, bound))

sns.lineplot(data=data, x="time_sec", y="d", ax=ax[3, 0])

bound = np.amax(np.abs(pca_data[["PC1", "PC2", "PC3"]]))[0]
sns.lineplot(data=pca_data, x="time_sec", y="PC1", ax=ax[4, 0])
sns.lineplot(data=pca_data, x="time_sec", y="PC2", ax=ax[4, 1])
sns.lineplot(data=pca_data, x="time_sec", y="PC3", ax=ax[4, 2])
for i in range(3):
    ax[4, i].set_ylim((-bound, bound))

plt.show()

sns.scatterplot(pts_on_plane[:, 0], pts_on_plane[:, 1])
plt.show()