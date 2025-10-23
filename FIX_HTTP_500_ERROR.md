# 🔧 Fix HTTP 500 Upload Error

## ❌ Error: Upload failed: HTTP 500

HTTP 500 = **Server-side error** (the S3 API is rejecting your upload)

---

## 🔍 Debug Information

With the updated uploader.py, you'll now see detailed debug output:

```
[UPLOADER] Uploading r1_1698765432.jpg (234567 bytes)...
[UPLOADER] Attempt 1/3
[UPLOADER] → Endpoint: https://api.easyparkai.com/api/Common/Upload?modulename=anpr
[UPLOADER] → Field name: singleFile
[UPLOADER] → Filename: r1_1698765432.jpg
[UPLOADER] ← Response: HTTP 500
[UPLOADER] ✗ Response: <error message from server>
```

**Check the response message** - it tells you what the server didn't like!

---

## 🎯 Common Causes of HTTP 500

### **1. Wrong Field Name** ⚠️

**Your API might expect a different field name!**

**Test:**

Edit `.env` and try different field names:

```bash
# Try option 1 (current):
UPLOAD_FIELD_NAME=singleFile

# Try option 2:
UPLOAD_FIELD_NAME=file

# Try option 3:
UPLOAD_FIELD_NAME=image

# Try option 4 (based on your endpoint):
UPLOAD_FIELD_NAME=anpr
```

**Most common:** `singleFile` or `file`

### **2. Missing or Wrong Query Parameters**

Your endpoint is:
```
https://api.easyparkai.com/api/Common/Upload?modulename=anpr
```

**Check:**
- Is `modulename=anpr` correct?
- Are there other required parameters?

**Try:**
```bash
# If API needs different module name:
UPLOAD_ENDPOINT=https://api.easyparkai.com/api/Common/Upload?modulename=camera

# Or no module name:
UPLOAD_ENDPOINT=https://api.easyparkai.com/api/Common/Upload
```

### **3. Missing Authentication**

**Check if API needs authentication:**

```bash
# Try with bearer token:
UPLOAD_AUTH_BEARER=your-api-key-here
```

### **4. File Name Format**

Some APIs reject certain filename patterns.

**Current:** `r1_1698765432.jpg`

**If API expects different format:**
- Check if it needs specific prefix/suffix
- Check if underscore is allowed
- Check if epoch timestamp is too long

### **5. Image Format or Corruption**

**Check if image is valid:**

```bash
# View the captured image
file /home/maxpark/r1_*.jpg

# Should show: JPEG image data

# Try opening with image viewer
display /home/maxpark/r1_1234567890.jpg
```

---

## 🔧 Debugging Steps

### **Step 1: Check What's Being Sent**

Run your system and press a button:

```bash
python app.py
# Press button
# Watch terminal output carefully
```

**You'll see:**
```
[UPLOADER] Uploading r1_1698765432.jpg (234567 bytes)...
[UPLOADER] Attempt 1/3
[UPLOADER] → Endpoint: <your endpoint>
[UPLOADER] → Field name: <field name>
[UPLOADER] → Filename: <filename>
[UPLOADER] ← Response: HTTP 500
[UPLOADER] ✗ Response: <SERVER ERROR MESSAGE HERE>
```

**Look at the error message!** It usually tells you what's wrong.

### **Step 2: Test with curl**

Test upload manually to see exact error:

```bash
# Replace with your actual file and endpoint
curl -X POST \
  -F "singleFile=@/home/maxpark/r1_1234567890.jpg" \
  "https://api.easyparkai.com/api/Common/Upload?modulename=anpr"
```

**Look at response** - should tell you the issue.

### **Step 3: Try Different Field Names**

```bash
# Test 1: singleFile (current)
curl -F "singleFile=@image.jpg" <endpoint>

# Test 2: file
curl -F "file=@image.jpg" <endpoint>

# Test 3: image
curl -F "image=@image.jpg" <endpoint>
```

**Find which one works, then update .env:**
```bash
UPLOAD_FIELD_NAME=<the_one_that_worked>
```

### **Step 4: Check API Documentation**

**Questions to answer:**
1. What is the correct multipart field name?
2. Are there required query parameters?
3. Is authentication required?
4. Is there a file size limit?
5. Are there filename restrictions?

---

## ✅ Quick Fixes to Try

### **Fix 1: Change Field Name**

```bash
# Edit .env
nano .env

# Try this:
UPLOAD_FIELD_NAME=file

# Restart and test
python app.py
```

### **Fix 2: Check Endpoint URL**

```bash
# Make sure endpoint is complete and correct
UPLOAD_ENDPOINT=https://api.easyparkai.com/api/Common/Upload?modulename=anpr

# No typos in:
# - Domain name
# - Path (/api/Common/Upload)
# - Query parameters (?modulename=anpr)
```

### **Fix 3: Add Authentication**

```bash
# If API needs auth token
UPLOAD_AUTH_BEARER=your-api-key-or-token-here
```

### **Fix 4: Disable Upload Temporarily**

```bash
# Test system without upload first
UPLOAD_ENABLED=false

# System will work fine, just won't upload
# Verify captures work correctly
# Then fix upload separately
```

---

## 🔍 Enhanced Debug Mode

I've added **verbose debugging** to uploader.py. It now shows:

- ✅ File being uploaded (name & size)
- ✅ Attempt number
- ✅ Endpoint URL
- ✅ Field name being used
- ✅ Filename being sent
- ✅ HTTP response code
- ✅ **Full server error message** (first 500 chars)

**This will help you see exactly what the server doesn't like!**

---

## 📋 Checklist for HTTP 500

Go through these one by one:

- [ ] Check server error message in terminal output
- [ ] Try different field names (singleFile, file, image)
- [ ] Verify endpoint URL is correct
- [ ] Test endpoint with curl
- [ ] Check if auth token needed
- [ ] Verify image file is valid JPEG
- [ ] Check API documentation for requirements
- [ ] Test with Postman or similar tool
- [ ] Contact API support if needed

---

## 🎯 Most Likely Causes

**Based on your endpoint:**
```
https://api.easyparkai.com/api/Common/Upload?modulename=anpr
```

**1. Wrong Field Name (90% likely)**

Try these in order:
```bash
UPLOAD_FIELD_NAME=singleFile  # Current (from uploader1.py)
UPLOAD_FIELD_NAME=file        # Common alternative
UPLOAD_FIELD_NAME=anpr        # Based on module name
```

**2. Missing Authentication (5% likely)**

```bash
UPLOAD_AUTH_BEARER=your-api-key
```

**3. Wrong Module Name (5% likely)**

```bash
# Try different module name
UPLOAD_ENDPOINT=https://api.easyparkai.com/api/Common/Upload?modulename=camera
```

---

## 🧪 Test Upload Directly

### **Create test image:**

```bash
# Create a small test JPEG
ffmpeg -f lavfi -i color=c=blue:s=640x480 -frames:v 1 test.jpg
```

### **Test upload with curl:**

```bash
# Test 1: singleFile field
curl -v -X POST \
  -F "singleFile=@test.jpg" \
  "https://api.easyparkai.com/api/Common/Upload?modulename=anpr"

# Test 2: file field
curl -v -X POST \
  -F "file=@test.jpg" \
  "https://api.easyparkai.com/api/Common/Upload?modulename=anpr"
```

**Look for:**
- HTTP 200 = SUCCESS! (use that field name)
- HTTP 500 = Server error (check response body)
- HTTP 401 = Auth needed
- HTTP 400 = Bad request (wrong format)

---

## 💡 What the Debug Output Shows

**Run your system now:**

```bash
python app.py
# Press button
```

**Terminal will show:**
```
[UPLOADER] Uploading r1_1698765432.jpg (234567 bytes)...
[UPLOADER] Attempt 1/3
[UPLOADER] → Endpoint: https://api.easyparkai.com/...
[UPLOADER] → Field name: singleFile     ← CHECK THIS!
[UPLOADER] → Filename: r1_1698765432.jpg
[UPLOADER] ← Response: HTTP 500
[UPLOADER] ✗ Response: {"error":"Invalid field name"} ← LOOK HERE!
```

**The response message tells you exactly what to fix!**

---

## 🚀 Quick Solution

**Most likely you just need to change the field name:**

```bash
# Edit .env
nano .env

# Find this line:
UPLOAD_FIELD_NAME=singleFile

# Change to:
UPLOAD_FIELD_NAME=file

# Save and restart:
python app.py

# Press button and check if HTTP 200 now!
```

---

## 📞 If Still Not Working

**Gather this information:**

1. **Full terminal output:**
   ```
   [UPLOADER] → Endpoint: <paste here>
   [UPLOADER] → Field name: <paste here>
   [UPLOADER] ← Response: HTTP 500
   [UPLOADER] ✗ Response: <paste full error message>
   ```

2. **API documentation or contact:**
   - Check API docs for correct field name
   - Contact easyparkai.com support
   - Ask what field name they expect

3. **Test with curl:**
   - Try different field names
   - Find which one works
   - Update .env

---

## ✅ Success Criteria

**You'll know it's working when you see:**

```
[UPLOADER] Uploading r1_1698765432.jpg (234567 bytes)...
[UPLOADER] Attempt 1/3
[UPLOADER] → Endpoint: https://...
[UPLOADER] → Field name: file           ← Whatever works
[UPLOADER] → Filename: r1_1698765432.jpg
[UPLOADER] ← Response: HTTP 200         ← SUCCESS!
[UPLOADER] ✓ Success! Location: https://s3.../r1_1698765432.jpg
```

**Dashboard will show:**
- Upload Status: 🟢 ONLINE
- Uploaded: 1 (or more)
- Pending: 0

---

## 🎯 Summary

**HTTP 500 = Server rejected upload**

**Most likely fix:**
```bash
# Change field name in .env
UPLOAD_FIELD_NAME=file  # Instead of singleFile
```

**Debug output now shows:**
- Exact request details
- Server response
- Error messages

**Use this info to fix the configuration!**

---

**Try changing `UPLOAD_FIELD_NAME` first - that's usually the issue!** 🔧

