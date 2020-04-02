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

PCs <- function(data, ...)
{
	cols <- enquos(...)

	data %>%
		select(!!!cols) %>%
		prcomp() %>%
		extract2("x") %>%
		as_tibble() %>%
		mutate(time.sec = data$time.sec)
}

####################################


setwd("C:/Users/thana/Documents/Research")
#system("python3 read_serial.py ip x x 20 output.csv") # autoname file with datetime

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




# Recognition

sample <- pca %>%
	dplyr::filter(time.sec > 1580 & time.sec < 1583)

plot.row(sample, PC1)

bow.start <- sample %>%
	top_n(1, -PC1) %>%
	pull(time.sec)

bow.end <- sample %>%
	top_n(1, PC1) %>%
	pull(time.sec)

bow <- sample %>%
	dplyr::filter(time.sec >= bow.start & time.sec <= bow.end)

plot.row(bow, PC1)

template <- diff(bow$PC1)



# how in the world to convolve to match??