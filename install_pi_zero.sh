#!/bin/bash
# Installation script for Raspberry Pi Zero 2W
# CamCap Image Capture System

echo "🚀 Installing CamCap on Raspberry Pi Zero 2W..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv git ffmpeg v4l-utils sqlite3 curl wget

# Install GPIO libraries
echo "🔌 Installing GPIO libraries..."
sudo apt install -y python3-gpiozero python3-rpi.gpio

# Create project directory
echo "📁 Creating project directory..."
mkdir -p /home/pi/camcap
cd /home/pi/camcap

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv camcap_env
source camcap_env/bin/activate

# Install Python dependencies
echo "📚 Installing Python packages..."
pip install Flask==3.0.3
pip install gpiozero==2.0.1
pip install RPi.GPIO==0.7.1
pip install python-dotenv==1.0.1
pip install requests==2.32.3
pip install opencv-python-headless==4.8.1.78
pip install Pillow==10.0.1

# Create directories
echo "📂 Creating directories..."
mkdir -p images logs
chmod 755 images

# Create systemd service
echo "⚙️ Creating system service..."
sudo tee /etc/systemd/system/camcap.service > /dev/null <<EOF
[Unit]
Description=CamCap Image Capture System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/camcap
Environment=PATH=/home/pi/camcap/camcap_env/bin
ExecStart=/home/pi/camcap/camcap_env/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable service
echo "🔄 Enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable camcap.service

# Test GPIO access
echo "🧪 Testing GPIO access..."
python3 -c "from gpiozero import Button; print('✅ GPIO access: OK')" || echo "❌ GPIO access failed"

# Create startup script
echo "📝 Creating startup script..."
cat > start_camcap.sh <<EOF
#!/bin/bash
cd /home/pi/camcap
source camcap_env/bin/activate
python app.py
EOF
chmod +x start_camcap.sh

# Create test script
echo "🧪 Creating test script..."
cat > test_gpio.sh <<EOF
#!/bin/bash
cd /home/pi/camcap
source camcap_env/bin/activate
python test_gpio_minimal.py
EOF
chmod +x test_gpio.sh

echo "✅ Installation completed!"
echo ""
echo "📋 Next steps:"
echo "1. Configure your .env file with camera URLs and settings"
echo "2. Test GPIO: ./test_gpio.sh"
echo "3. Start system: ./start_camcap.sh"
echo "4. Enable auto-start: sudo systemctl start camcap.service"
echo ""
echo "🌐 Web dashboard will be available at: http://your-pi-ip:8080"
echo "🔌 GPIO pins: Button 1 (GPIO 18), Button 2 (GPIO 19)"

