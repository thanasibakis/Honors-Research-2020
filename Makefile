default:
	@echo "Please choose a target."
	@echo "\tbuild-mac"
	@echo "\tbuild-docker"
	@echo "\tclean"

build-mac:
	cd build_resources/
	pyinstaller macos.spec
	cd ../
	@echo "\nYour executable is now in build_resources/dist/"
	@echo "Done."

build-docker:
	docker build -t mugic-positioning .
	@echo "Done."

clean:
	rm -rf build_resources/build
	rm -rf build_resources/dist
	echo "Done."
