#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status
set -o pipefail  # Prevents errors in a pipeline from being masked

# Define installation directories
GEOS_VERSION="3.13.0"
PROJ_VERSION="9.5.1"
GDAL_VERSION="3.10.1"
INSTALL_PREFIX="/usr/local"

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Install GEOS
if command_exists geos-config && geos-config --version | grep -q "$GEOS_VERSION"; then
    echo "GEOS $GEOS_VERSION is already installed. Skipping..."
else
    echo "Downloading and installing GEOS..."
    if [ ! -f "geos-${GEOS_VERSION}.tar.bz2" ]; then
        wget https://download.osgeo.org/geos/geos-${GEOS_VERSION}.tar.bz2
    fi
    if [ ! -d "geos-${GEOS_VERSION}" ]; then
        tar xjf geos-${GEOS_VERSION}.tar.bz2
    fi
    cd geos-${GEOS_VERSION}
    mkdir -p build && cd build
    cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$INSTALL_PREFIX ..
    cmake --build .
    sudo cmake --build . --target install
    cd ../..
fi

# Install PROJ
if command_exists proj && proj -V | grep -q "$PROJ_VERSION"; then
    echo "PROJ $PROJ_VERSION is already installed. Skipping..."
else
    echo "Downloading and installing PROJ..."
    if [ ! -f "proj-${PROJ_VERSION}.tar.gz" ]; then
        wget https://download.osgeo.org/proj/proj-${PROJ_VERSION}.tar.gz
    fi
    if [ ! -d "proj-${PROJ_VERSION}" ]; then
        tar xzf proj-${PROJ_VERSION}.tar.gz
    fi
#     cd proj-${PROJ_VERSION}/data
#     tar xzf ../../proj-data-${PROJ_VERSION}.tar.gz
#     cd ../..
    cd proj-${PROJ_VERSION}
    mkdir -p build && cd build
    cmake -DCMAKE_INSTALL_PREFIX=$INSTALL_PREFIX ..
    cmake --build .
    sudo cmake --build . --target install
    cd ../..
fi

# Install GDAL
if command_exists gdal-config && gdal-config --version | grep -q "$GDAL_VERSION"; then
    echo "GDAL $GDAL_VERSION is already installed. Skipping..."
else
    echo "Downloading and installing GDAL..."
    if [ ! -f "gdal-${GDAL_VERSION}.tar.gz" ]; then
        wget https://download.osgeo.org/gdal/CURRENT/gdal-${GDAL_VERSION}.tar.gz
    fi
    if [ ! -d "gdal-${GDAL_VERSION}" ]; then
        tar xzf gdal-${GDAL_VERSION}.tar.gz
    fi
    cd gdal-${GDAL_VERSION}
    mkdir -p build && cd build
    cmake -DCMAKE_INSTALL_PREFIX=$INSTALL_PREFIX ..
    cmake --build .
    sudo cmake --build . --target install
    cd ../..
fi

echo "Installation of GEOS, PROJ, and GDAL completed successfully!"