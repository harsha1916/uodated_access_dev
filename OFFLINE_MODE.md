# 📡 Offline Operation Guide

This document explains how the Camera Capture System handles offline operation and automatic retry of failed uploads.

## 🎯 Overview

The system is designed to **work perfectly without internet connection**. Images are always captured and stored locally first, ensuring you never lose a single image even during prolonged network outages.

## 🔄 How It Works

### Architecture

```
┌─────────────────┐
│  GPIO Trigger   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Capture Service │ ──► Save to images/ (ALWAYS SUCCESSFUL)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Check Internet  │ ──► Every 60 seconds
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
  ONLINE    OFFLINE
    │         │
    ▼         ▼
┌───────┐  ┌──────────────────┐
│Upload │  │Add to            │
│to S3  │  │pending_uploads.  │
│       │  │json              │
└───────┘  └────────┬─────────┘
                    │
                    ▼
           ┌──────────────────┐
           │Retry Worker      │
           │(checks every 60s)│
           └────────┬─────────┘
                    │
              ┌─────┴─────┐
              │           │
            STILL       ONLINE
            OFFLINE     AGAIN!
              │           │
              ▼           ▼
            Wait      Upload All
                      Pending
```

## 📝 Persistent Queue

### File: `pending_uploads.json`

Failed uploads are saved to a JSON file on disk:

```json
[
  {
    "filepath": "images/r1_1698765432.jpg",
    "added_timestamp": 1698765432,
    "added_datetime": "2024-10-31T12:30:32",
    "retry_count": 0
  },
  {
    "filepath": "images/r2_1698765433.jpg",
    "added_timestamp": 1698765433,
    "added_datetime": "2024-10-31T12:30:33",
    "retry_count": 1
  }
]
```

### Key Points

- ✅ **Persists across restarts**: If system reboots, pending uploads are loaded on startup
- ✅ **Thread-safe**: Updates are synchronized with locks
- ✅ **Automatic cleanup**: Successfully uploaded files are removed
- ✅ **Retry tracking**: Each entry tracks number of retry attempts

## 🌐 Internet Connectivity Detection

### Smart Detection

```python
# Checks every 60 seconds (configurable)
check_internet_connectivity()
  ↓
Try to reach www.google.com (timeout: 5s)
  ↓
┌─────────┬─────────┐
│ SUCCESS │ FAILURE │
└────┬────┴────┬────┘
     │         │
  ONLINE     OFFLINE
     │         │
     ▼         ▼
  Upload    Queue
  to S3    for Retry
```

### Configuration

Control in `.env`:

```bash
# How often to check internet connectivity
CONNECTIVITY_CHECK_INTERVAL=60  # seconds

# How often retry worker attempts pending uploads
OFFLINE_RETRY_INTERVAL=60  # seconds
```

## 🔧 Components

### 1. Upload Worker Thread

**Job**: Process new capture uploads

```
While running:
  1. Get image from queue
  2. Check internet connectivity
     - If OFFLINE: Add to pending_uploads.json
     - If ONLINE: Attempt upload
       - If SUCCESS: Mark uploaded
       - If FAILED: Add to pending_uploads.json
  3. Update statistics
```

### 2. Retry Worker Thread

**Job**: Retry pending uploads when online

```
While running:
  1. Sleep 30 seconds (initial delay)
  2. Load pending_uploads.json
  3. If no pending: Sleep 60s, repeat
  4. Check internet connectivity
     - If OFFLINE: Sleep 60s, repeat
     - If ONLINE: Process all pending uploads
       a. For each pending upload:
          - Check file exists
          - Attempt upload
          - If success: Mark for removal
          - If failed: Increment retry_count
       b. Remove successful uploads from queue
       c. Save updated queue
  5. Sleep 60s, repeat
```

## 📊 Statistics & Monitoring

### Web Interface

The dashboard shows:

- **Status**: 🟢 ONLINE or 🔴 OFFLINE
- **Queued**: Total images queued for upload
- **Uploaded**: Successfully uploaded images
- **Failed**: Upload attempts that failed
- **Queue Size**: Current upload queue size
- **Pending Retry**: Images waiting in offline queue

### Example

```
Upload Statistics:
Status:        🟢 ONLINE
Queued:        45
Uploaded:      42
Failed:        3
Queue Size:    0
Pending Retry: 3  ← Images waiting to be retried
```

## 🚨 Offline Scenarios

### Scenario 1: No Internet at Startup

```
1. System starts
2. Camera triggers, image captured → Saved locally ✓
3. Upload worker attempts upload
4. Internet check: OFFLINE
5. Image added to pending_uploads.json
6. Retry worker checks every 60s
7. When internet returns → Automatic upload
```

### Scenario 2: Internet Lost During Operation

```
1. System running normally (ONLINE)
2. Internet connection lost
3. Camera triggers, image captured → Saved locally ✓
4. Upload worker detects OFFLINE
5. Status changes to 🔴 OFFLINE in web interface
6. Image added to pending queue
7. Retry worker waits for connection
8. Internet returns → All pending images uploaded
9. Status changes to 🟢 ONLINE
```

### Scenario 3: System Restart with Pending Uploads

```
1. System had 10 pending uploads
2. System is shut down
3. pending_uploads.json remains on disk
4. System restarts
5. Upload service loads pending_uploads.json
6. Finds 10 pending uploads
7. Retry worker starts
8. All 10 uploads attempted when online
```

## 🎯 User Experience

### For End Users

**What You See:**

- Images appear in web gallery **immediately** (no waiting for upload)
- Upload status shown in dashboard
- Offline indicator when no internet
- Pending count shows how many waiting to upload

**What You DON'T Worry About:**

- ❌ Lost images during internet outage
- ❌ Manual retry of failed uploads
- ❌ Checking if uploads succeeded
- ❌ Complicated recovery procedures

### For Administrators

**Monitoring:**

```bash
# View pending uploads
cat pending_uploads.json

# Check logs for offline/online transitions
tail -f camera_system.log | grep -i "offline\|online"

# View statistics via API
curl http://192.168.1.33:9000/api/stats

# Check web interface
# Navigate to: http://192.168.1.33:9000
```

**Manual Intervention (Rarely Needed):**

```bash
# Force retry now (restart service)
sudo systemctl restart camera-capture.service

# Clear pending queue (if needed)
rm pending_uploads.json

# Check system status
sudo systemctl status camera-capture.service
```

## ⚙️ Configuration Options

### In `.env` file:

```bash
# Enable/disable uploads
UPLOAD_ENABLED=true

# Enable background upload (required for offline retry)
BACKGROUND_UPLOAD=true

# Upload queue size (in-memory queue)
UPLOAD_QUEUE_SIZE=100

# How often to retry pending uploads (seconds)
OFFLINE_RETRY_INTERVAL=60

# How often to check internet connectivity (seconds)
CONNECTIVITY_CHECK_INTERVAL=60

# S3 API endpoint
S3_API_URL=https://api.easyparkai.com/api/Common/Upload?modulename=anpr
```

### Tuning for Your Environment

**High Reliability Network:**
```bash
OFFLINE_RETRY_INTERVAL=30  # Check more frequently
CONNECTIVITY_CHECK_INTERVAL=30
```

**Unstable Network:**
```bash
OFFLINE_RETRY_INTERVAL=120  # Check less frequently to avoid spam
CONNECTIVITY_CHECK_INTERVAL=120
```

**Local Testing (No Upload):**
```bash
UPLOAD_ENABLED=false  # Disable uploads entirely
```

## 🔍 Troubleshooting

### Problem: Images Not Uploading

**Check:**

1. View web interface - Is status OFFLINE?
2. Check `pending_uploads.json` - How many pending?
3. Test internet: `ping google.com`
4. Check logs: `tail -f camera_system.log`

**Solution:**

- If offline: Wait for internet or fix network
- If online but not uploading: Check S3_API_URL
- If pending count growing: Check upload errors in logs

### Problem: Pending Queue Growing

**Possible Causes:**

1. **Internet Down**: Normal - will upload when back online
2. **S3 API Error**: Check API endpoint, credentials
3. **File Permissions**: Check images/ directory permissions
4. **Disk Full**: Check available disk space

**Check Logs:**

```bash
grep -i "error\|failed" camera_system.log | tail -20
```

### Problem: Uploads Slow After Reconnect

**Normal Behavior:**

- Retry worker processes one image at a time
- 2-second delay between uploads
- This prevents overwhelming the network

**If Too Slow:**

Modify `uploader.py` line 370:
```python
time.sleep(2)  # Reduce to time.sleep(0.5) for faster uploads
```

## 📈 Performance

### Resource Usage

- **CPU**: Minimal (worker threads mostly sleep)
- **Memory**: ~1-2MB for pending queue data
- **Disk I/O**: One read/write per pending upload update
- **Network**: Only when uploading (controlled by retry interval)

### Scalability

**Tested With:**

- ✅ 100+ pending uploads
- ✅ 24+ hour offline period
- ✅ Multiple system restarts
- ✅ Concurrent capture + retry

**Limits:**

- Pending queue: No hard limit (JSON file size)
- Recommended: Keep below 1000 pending uploads
- If queue grows too large, consider increasing `IMAGE_RETENTION_DAYS`

## 🛡️ Data Safety

### Guarantees

1. **Images Always Saved**: Capture never depends on upload
2. **Persistent Queue**: Survives system restarts
3. **No Data Loss**: Failed uploads are retried indefinitely
4. **Thread-Safe**: Concurrent access properly synchronized

### Not Guaranteed

- Upload order (may not match capture order)
- Upload timing (depends on retry interval)
- Instant upload (if offline, must wait for retry cycle)

## 🎓 Best Practices

### 1. Monitor Pending Count

Set up alerts if pending count exceeds threshold:

```bash
# Example monitoring script
PENDING=$(curl -s http://localhost:9000/api/stats | jq '.stats.capture.upload_stats.pending_retry')
if [ "$PENDING" -gt 50 ]; then
  echo "WARNING: $PENDING pending uploads"
fi
```

### 2. Regular Connectivity Checks

Ensure your network infrastructure is reliable:

- Use wired connection (more stable than WiFi)
- Configure network auto-reconnect
- Monitor internet connection separately

### 3. Disk Space Management

With 120-day retention and offline uploads:

```bash
# Estimate: 500KB per image, 1000 images/day
# Space needed: 500KB * 1000 * 120 = ~60GB
```

Ensure adequate disk space!

### 4. Logging

Keep logs for troubleshooting:

```bash
# Rotate logs to prevent disk fill
# Add to crontab:
0 0 * * * find /path/to/logs -name "*.log" -mtime +30 -delete
```

## 🎉 Summary

The offline operation feature ensures:

- ✅ **Zero image loss** during network outages
- ✅ **Automatic recovery** when connection returns  
- ✅ **No manual intervention** required
- ✅ **Persistent across restarts**
- ✅ **Real-time monitoring** via web interface
- ✅ **Configurable behavior** for your environment

**Bottom Line:** Capture images without worrying about internet connectivity!

---

For more information, see:
- [README.md](README.md) - Full documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Code architecture

