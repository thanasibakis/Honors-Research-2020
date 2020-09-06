# Ensure your XQuartz/X410 server is running!
docker run \
	-it \
	--rm \
	--privileged \
	-e DISPLAY=host.docker.internal:0.0 \
	-v "`pwd`/src":/code/src \
	mugic-positioning
