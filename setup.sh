#!/bin/bash

# Camera Capture System - Setup Script
# This script helps you set up the camera capture system

set -e

echo "=========================================="
echo "Camera Capture System - Setup"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✓ Python 3 found: $PYTHON_VERSION"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Installing..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

echo "✓ pip3 found"

# Install system dependencies for OpenCV
echo ""
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3-opencv \
    libopencv-dev \
    python3-dev \
    python3-pip

# Create virtual environment (optional but recommended)
read -p "Do you want to create a virtual environment? (recommended) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    echo "✓ Virtual environment created"
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Check if running on Raspberry Pi
if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo ""
    echo "✓ Raspberry Pi detected"
    read -p "Do you want to install GPIO support (RPi.GPIO)? [Y/n]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        pip3 install RPi.GPIO
        echo "✓ RPi.GPIO installed"
    fi
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env configuration file..."
    cp env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file with your camera settings:"
    echo "   - Camera IP addresses"
    echo "   - Camera credentials"
    echo "   - GPIO pins (if using Raspberry Pi)"
    echo "   - S3 API URL"
    echo ""
    read -p "Press Enter to edit .env file now or Ctrl+C to exit..."
    ${EDITOR:-nano} .env
else
    echo "✓ .env file already exists"
fi

# Create images directory
mkdir -p images
echo "✓ Images directory created"

# Test the installation
echo ""
echo "=========================================="
echo "Testing Installation"
echo "=========================================="
echo ""

read -p "Do you want to test camera capture? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 main.py --test-capture
fi

# Offer to set up as systemd service
echo ""
read -p "Do you want to install as a systemd service (auto-start on boot)? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Update paths in service file
    CURRENT_DIR=$(pwd)
    PYTHON_PATH=$(which python3)
    
    # Create temporary service file with correct paths
    sed -e "s|/home/pi/camera_capture_system|$CURRENT_DIR|g" \
        -e "s|/usr/bin/python3|$PYTHON_PATH|g" \
        camera-capture.service > /tmp/camera-capture.service
    
    # Install service
    sudo cp /tmp/camera-capture.service /etc/systemd/system/camera-capture.service
    sudo systemctl daemon-reload
    sudo systemctl enable camera-capture.service
    
    echo "✓ Systemd service installed"
    echo ""
    read -p "Do you want to start the service now? [Y/n]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        sudo systemctl start camera-capture.service
        echo "✓ Service started"
        echo ""
        echo "Check status with: sudo systemctl status camera-capture.service"
        echo "View logs with: sudo journalctl -u camera-capture.service -f"
    fi
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To start the system manually:"
echo "  python3 main.py"
echo ""
echo "To test camera capture:"
echo "  python3 main.py --test-capture"
echo ""
echo "To test GPIO (Raspberry Pi only):"
echo "  python3 main.py --test-gpio"
echo ""
echo "Web interface will be available at:"
echo "  http://$(hostname -I | awk '{print $1}'):9000"
echo ""
echo "For more information, see README.md"
echo ""

