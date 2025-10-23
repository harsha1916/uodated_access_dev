# CamCap (Pi Zero 2 W)

Press-to-capture stills from two RTSP cameras using two GPIO buttons.
Saves locally for 120 days and uploads in the background to your endpoint.
Includes a Flask gallery UI.

## Quickstart

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv
mkdir -p ~/camcap && cd ~/camcap
# copy these files into ~/camcap (unzip)
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

cp config.example.env .env
# edit .env with your RTSP URLs and upload endpoint

# run once to test
sudo -E env "PATH=$PATH" ./.venv/bin/python app.py
# open http://<pi-ip>:8080

# install as service
sudo cp camcap.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable camcap
sudo systemctl start camcap
```

Wire buttons to BCM GPIO 18 and 23, pull-up with button to GND.
Filenames are r1_{epoch}.jpg or r2_{epoch}.jpg.
