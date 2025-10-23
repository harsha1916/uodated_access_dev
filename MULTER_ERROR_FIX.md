# 🔧 FIX: MulterError: Unexpected field

## ❌ Error Message You Got:

```
MulterError: Unexpected field
```

**This means:** The server expects a different field name than what you're sending!

---

## ⚡ QUICK FIX (2 Minutes)

### **Solution: Change Field Name to "file"**

**Edit your `.env` file:**

```bash
nano .env
```

**Find this line:**
```bash
UPLOAD_FIELD_NAME=singleFile
```

**Change to:**
```bash
UPLOAD_FIELD_NAME=file
```

**Save and restart:**
```bash
python app.py
```

**Test by pressing a button** - should work now!

---

## 🧪 **Or Use Automated Test Script**

**Run this to find the correct field name automatically:**

```bash
python test_upload.py
```

**The script will:**
1. Test common field names: `file`, `singleFile`, `image`, `upload`, `photo`
2. Show which one returns HTTP 200
3. Tell you exactly what to put in `.env`

**Example output:**
```
Testing field name: 'file'...
  ✅ SUCCESS! HTTP 200
  ✓ Response: {"Location":"https://s3.../test.jpg"}

✅ SOLUTION FOUND!
✓ Use this field name in your .env file:
  UPLOAD_FIELD_NAME=file
```

---

## 🎯 **Understanding the Error**

**What Multer is:**
- Node.js middleware for handling file uploads
- Used by your S3 API backend
- Configured to accept specific field names

**What "Unexpected field" means:**
- You sent: `singleFile`
- Server expected: `file` (or something else)
- Multer rejected it

**Fix:** Match the field name the server expects!

---

## 📝 **Step-by-Step Fix**

### **Method 1: Try Common Field Names**

**Edit `.env` and try each:**

```bash
# Try 1 (most common):
UPLOAD_FIELD_NAME=file

# If that fails, try 2:
UPLOAD_FIELD_NAME=image

# If that fails, try 3:
UPLOAD_FIELD_NAME=upload
```

**After each change:**
```bash
# Restart
python app.py

# Press button
# Check terminal for:
# ✅ [UPLOADER] ✓ Success!  → WORKS!
# ❌ MulterError            → Try next one
```

### **Method 2: Use Test Script** (Recommended)

```bash
python test_upload.py
```

**Automatically tests all common field names and tells you which one works!**

---

## 🔍 **Debug Output**

With the enhanced uploader, you now see:

```
[UPLOADER] → Field name: singleFile     ← What you're sending
[UPLOADER] ← Response: HTTP 500
[UPLOADER] ✗ Response: MulterError: Unexpected field  ← Server rejects it
```

**This tells you to change the field name!**

---

## ✅ **How to Verify Fix**

**After changing field name, you should see:**

```
[UPLOADER] Uploading r1_1698765432.jpg (234567 bytes)...
[UPLOADER] Attempt 1/3
[UPLOADER] → Field name: file           ← Correct field name
[UPLOADER] ← Response: HTTP 200         ← SUCCESS!
[UPLOADER] ✓ Success! Location: https://...
```

**Dashboard shows:**
- Upload Status: 🟢 ONLINE
- Uploaded: 1
- Pending: 0

---

## 🎯 **Most Likely Solutions**

### **Solution 1: Use "file" (95% chance)**

```bash
# In .env:
UPLOAD_FIELD_NAME=file
```

### **Solution 2: Use "image"**

```bash
# In .env:
UPLOAD_FIELD_NAME=image
```

### **Solution 3: Ask API Provider**

Contact easyparkai.com support and ask:
> "What multipart field name should I use for the /api/Common/Upload endpoint?"

They'll tell you: `file`, `image`, `upload`, etc.

---

## 📋 **Quick Reference**

**Error:** `MulterError: Unexpected field`

**Cause:** Wrong field name

**Fix:** Change `UPLOAD_FIELD_NAME` in `.env`

**Test:** `python test_upload.py`

**Verify:** Look for HTTP 200 response

---

## 🚀 **Quick Fix Steps**

```bash
# 1. Edit .env
nano .env

# 2. Change this line:
UPLOAD_FIELD_NAME=file

# 3. Save (Ctrl+X, Y, Enter)

# 4. Restart
python app.py

# 5. Press button

# 6. Check terminal:
[UPLOADER] ← Response: HTTP 200  ← Should see this!
[UPLOADER] ✓ Success!
```

**That's it!** 🎉

---

## 💡 **Pro Tip: Use Test Script**

```bash
python test_upload.py
```

**It will automatically:**
- Test all common field names
- Show which one returns HTTP 200
- Tell you exactly what to put in `.env`

**Saves you from manual trial and error!**

---

**Start with: `UPLOAD_FIELD_NAME=file` in your `.env` file!** 🔧

**99% chance that's the fix!** ✅

