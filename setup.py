from setuptools import setup

setup(
    name="mugic",
    version="2020.05.13.4",
    description="Plotting data from the MUGIC sensor",
    url="https://github.com/thanasibakis/Honors-Research-2020",
    author="Thanasi Bakis",
    author_email="thanasibakis@gmail.com",
    packages=["mugic"],
    install_requires=[
        "pandas",
        "pyqt5",
        "pyqtgraph",
        "pyserial",
        "scipy",
        "seaborn",
        "sklearn"
    ],
    entry_points={
        "console_scripts": ["mugic=mugic.__init__:run_app"]
    },
    zip_safe=False,
    include_package_data=True
)
