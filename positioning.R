library(tidyverse)
library(patchwork)

source("helpers.R")


####################################


setwd("C:/Users/thana/Documents/Honors-Research-2020")
#system("python3 read_serial.py 20")

data <- read.csv("violinbowingdata/fullbow.csv")

R <- rot.mat(data$qw, data$qx, data$qy, data$qz)

accel <- data %>%
	select(ax, ay, az) %>%
	as.matrix() %>%
	rotate(R)

data <- data %>%
	mutate(lax = accel[, "ax"],
		   lay = accel[, "ay"],
		   laz = accel[, "az"]) %>%
	mutate(time.sec = Timestamp) %>%
	mutate(vx = integ(ax, time.sec),
		   vy = integ(ay, time.sec),
		   vz = integ(az, time.sec)) %>%
	mutate( x = integ(vx, time.sec),
		    y = integ(vy, time.sec),
		    z = integ(vz, time.sec)) %>%
	mutate( d = sqrt(x^2 + y^2 + z^2))


pca.info <- PCA(data, x, y, z)
pca.data <- pca.info[["components"]]
pca.matrix <- pca.info[["rotation"]] # the columns are eigenvectors


plot.row(data, ax, ay, az) /
	plot.row(data, vx, vy, vz) /
	plot.row(data, x, y, z) /
	plot.row(data, d) /
	plot.row(pca.data, PC1, PC2, PC3)


### HELP ###

# is it normal for qwxy to be 0? only qz has stuff

plot.row(data, ax, ay, az) /
	plot.row(data, lax, lay, laz)

# note i did not switch out ax/... for lax/... in the integration yet

###


# Get the first eigenvector (corresponding to PC1)
# Get a plane perpendicular to it
# Project x,y,z onto the plane
# to measure if the bowing is close to a straight line

# https://math.stackexchange.com/questions/1872783/projection-onto-a-plane
eig1 <- pca.matrix[, 1]

P <- c(eig1[2], -eig1[1], 0)
Q <- c(eig1[1]*eig1[3], eig1[2]*eig1[3], -(eig1[1]^2 + eig1[2]^2))

P <- P / sqrt(sum(P^2))
Q <- Q / sqrt(sum(Q^2))

proj.mat <- matrix(c(P, Q), byrow = F, ncol = 2)

pts.on.plane <- as.matrix(select(data, x, y, z)) %*% proj.mat
plot(pts.on.plane)










# Pattern Recognition

bow.start <- pca %>%
	filter(time.sec > 1580 & time.sec < 1583) %>%
	top_n(1, -PC1) %>%
	pull(time.sec)

bow.end <- pca %>%
	filter(time.sec > 1580 & time.sec < 1583) %>%
	top_n(1, PC1) %>%
	pull(time.sec)

# Let's find similar instances of this up-motion
bow <- pca %>%
	filter(time.sec >= bow.start & time.sec <= bow.end) %>%
	select(PC1, time.sec)

plot.row(pca, PC1) /
plot.row(bow, PC1)

lags <- find_matches(pca$PC1, bow$PC1)
locations <- pca$time.sec[lags]

plot.row(pca, PC1) +
	geom_vline(xintercept = locations, col = "dodgerblue4", alpha = 0.7, size = 1)
