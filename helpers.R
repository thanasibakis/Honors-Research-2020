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
	#coef = signal::butter(5, 0.36 * 2 / samp.rate, "high")
	coef <- signal::butter(5, 0.0065, "high") # sample rate is known 100 hz from loop delay
	col_filtered <- signal::filtfilt(coef$b, coef$a, col)

	return(cumsum(col_filtered / samp.rate)) # aka sum(column * dtime), which is an integral :)
	# maybe use the real dt for each sample, not this avg dt calcuated using the sample rate
}

# Get the principal components and rotation matrix of the given columns of the dataset
PCA <- function(data, ...)
{
	cols <- enquos(...)

	pca <- data %>%
		select(!!!cols) %>%
		prcomp()

	rotation <- pca[["rotation"]]

	components <- pca[["x"]] %>%
		as_tibble() %>%
		mutate(time.sec = data$time.sec)

	list(rotation = rotation, components = components)
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

# a 3D matrix, each R[, , i] is the rotation matrix of sample i
rot.mat <- function(qw, qx, qy, qz)
{
	q.norm <- sqrt(qw^2 + qx^2 + qy^2 + qz^2)
	qw <- qw / q.norm
	qx <- qx / q.norm
	qy <- qy / q.norm
	qz <- qz / q.norm

	R <- array(dim = c(3, 3, length(qw)))
	R[1, 1, ] <- 1 - 2*(qy^2 + qz^2)
	R[2, 1, ] <- 2*(qx*qy + qz*qw)
	R[3, 1, ] <- 2*(qx*qz - qy*qw)
	R[1, 2, ] <- 2*(qx*qy - qz*qw)
	R[2, 2, ] <- 1 - 2*(qx^2 + qz^2)
	R[3, 2, ] <- 2*(qy*qz + qx*qw)
	R[1, 3, ] <- 2*(qx*qz + qy*qw)
	R[2, 3, ] <- 2*(qy*qz - qx*qw)
	R[3, 3, ] <- 1 - 2*(qx^2 + qy^2)

	R
}

# Applies a rotation matrix from rot.mat()
rotate <- function(M, R)
{
	M2 <- M

	for(row in 1:dim(M)[1])
		M2[row, ] <- M[row, ] %*% R[, , row]

	M2
}