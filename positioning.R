library(tidyverse)
library(patchwork)


# Easily plot each several vectors in a row of line plots
# eg plot.row(data, col1, col2, col3)
plot.row <- function(data, ...)
{
	plot <- function(col)
	{
		data %>%
			ggplot(aes(time.sec, !!col)) +
			geom_line() +
			ylim(-bound, bound)
	}

	cols <- enquos(...)

	bound <- data %>%
		select(!!!cols) %>%
		summarize_all( ~ max(abs(.))) %>%
		max() # for the AccelStatus's sake

	Reduce("+", lapply(cols, plot))
}

# Filter and integrate a column (high pass filter removes low freq noise,
#   aka the constant drift that the sensor reports... keeping just the interesting motion we do)
#https://forums.adafruit.com/viewtopic.php?f=8&t=81842&hilit=bno055+position&start=0#p414708
integ <- function(col, time)
{
	samp.rate <- length(col) / (max(time) - min(time))
	#coef = butter(5, 0.36 * 2 / samp.rate, "high")
	coef <- signal::butter(5, 0.0065, "high") # sample rate is known 100 hz from loop delay
	col_filtered <- signal::filtfilt(coef$b, coef$a, col)

	return(cumsum(col_filtered / samp.rate)) # aka sum(column * dtime), which is an integral :)
	# maybe use the real dt for each sample, not this avg dt calcuated using the sample rate
}

# Get the principal components of the given columns of the dataset
PCs <- function(data, ...)
{
	cols <- enquos(...)

	data %>%
		select(!!!cols) %>%
		prcomp() %>%
		magrittr::extract2("x") %>%
		as_tibble() %>%
		mutate(time.sec = data$time.sec)
}

# Performs a cross-correlation to search for matches of a template signal
# in a larger signal
find_matches <- function(data, template)
{
	template <- c(template, rep(0, length(data) - length(template)))

	correlation <- ccf(data, template, lag.max = length(data))
	plot(correlation)

	peaks <- quantmod::findPeaks(correlation$acf)
	lags <- correlation$lag[peaks]

	lags[lags > 0]
}

####################################


setwd("C:/Users/thana/Documents/Honors-Research-2020")
#system("python3 read_serial.py 20 output.csv")
# TODO: autoname file with datetime

data <- read.csv("violinbowingdata/fullbow.csv") %>%
	mutate(time.sec = Timestamp) %>%
	mutate(vx = integ(ax, time.sec),
		   vy = integ(ay, time.sec),
		   vz = integ(az, time.sec)) %>%
	mutate( x = integ(vx, time.sec),
		    y = integ(vy, time.sec),
		    z = integ(vz, time.sec)) %>%
	mutate( d = sqrt(x^2 + y^2 + z^2))

pca <- PCs(data, x, y, z)

plot.row(data, ax, ay, az) /
	plot.row(data, vx, vy, vz) /
	plot.row(data, x, y, z) /
	plot.row(data, d) /
	plot.row(pca, PC1, PC2, PC3)


# TODO:
# Get the first eigenvector (corresponding to PC1)
# Get a plane perpendicular to it
# Project x,y,z onto the plane
# to measure if the bowing is close to a straight line


# Recognition

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
