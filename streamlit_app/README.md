# 🚀 HEGEMON Streamlit UI - Deployment Guide

## Quick Start (Vertex AI Workbench)

### 1. Installation (5 minutes)

```bash
# Navigate to project root
cd ~/olga_zydziak/version_beta/Folder/hegemon_mvp/

# Install Streamlit dependencies
pip install -r streamlit_app/requirements.txt

# Verify installation
streamlit --version
```

### 2. Run Streamlit App

```bash
# From project root
streamlit run streamlit_app/app.py --server.port 8080 --server.address 0.0.0.0
```

**Output:**
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8080
  Network URL: http://0.0.0.0:8080
```

### 3. Access in Browser

**Option A: Port Forwarding (Recommended for Vertex AI)**

1. In VS Code / JupyterLab, look for port forwarding notification
2. Click "Open in Browser" for port 8080
3. Or manually set up SSH tunnel:

```bash
# On your local machine:
gcloud compute ssh YOUR_INSTANCE_NAME \
    --project=YOUR_PROJECT \
    --zone=YOUR_ZONE \
    --ssh-flag="-L 8080:localhost:8080"
```

Then open: http://localhost:8080

**Option B: Public IP (Less Secure)**

If your VM has external IP, access directly:
```
http://YOUR_EXTERNAL_IP:8080
```

⚠️ **Security:** Configure firewall rules first!

---

## 📋 Features

✅ **No Jupyter Widget Issues** - Pure web interface  
✅ **Real-time Updates** - Automatic refresh during debate  
✅ **Full HITL Control** - All checkpoints with feedback  
✅ **Mobile Friendly** - Responsive design  
✅ **Results Download** - Export debate results as JSON  
✅ **History Tracking** - View all feedback submissions  

---

## 🎯 Usage

### Starting a Debate

1. **Enter Mission** in sidebar text area
2. **Select Mode:**
   - **Observer**: Minimal checkpoints
   - **Reviewer**: Standard (recommended)
   - **Collaborator**: Maximum control
3. **Click "Start Debate"**

### At Checkpoints

1. **Review:** Executive summary, highlights, suggestions
2. **Decide:**
   - ✅ Approve → Continue
   - ✏️ Revise → Provide guidance
   - ❌ Reject → End debate
3. **Submit Feedback**

### After Completion

- **View Results:** Full plan, workflow, agents
- **Download JSON:** Complete debate history
- **Start New:** Reset and begin another debate

---

## 🔧 Configuration

### Environment Variables

Create `.streamlit/config.toml` in project root:

```toml
[server]
port = 8080
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8f9fa"
textColor = "#262730"
```

### Custom Settings

Edit `streamlit_app/config.py`:

```python
DEBATE_CONFIG = {
    "default_mode": "reviewer",
    "max_cycles": 10,
    "consensus_threshold": 0.75,
}
```

---

## 🐛 Troubleshooting

### Issue: "Address already in use"

**Solution:**
```bash
# Kill existing Streamlit process
pkill -f streamlit

# Or use different port
streamlit run streamlit_app/app.py --server.port 8081
```

### Issue: "Module not found"

**Solution:**
```bash
# Ensure you're in project root
pwd  # Should show: .../hegemon_mvp

# Reinstall dependencies
pip install -r streamlit_app/requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

### Issue: "Can't access from browser"

**Solution:**
```bash
# Check if Streamlit is running
ps aux | grep streamlit

# Verify port 8080 is open
sudo netstat -tulpn | grep 8080

# Check firewall (if using external IP)
gcloud compute firewall-rules list
```

### Issue: Debate stuck at checkpoint

**Solution:**
- Check browser console for errors (F12)
- Refresh page (Ctrl+R)
- If persists, restart Streamlit

---

## 🚀 Production Deployment

### Option 1: Streamlit Cloud (Easiest)

1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Connect repository
4. Deploy (free tier available)

### Option 2: Docker (Scalable)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt streamlit_app/requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["streamlit", "run", "streamlit_app/app.py", "--server.port=8080", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t hegemon-ui .
docker run -p 8080:8080 hegemon-ui
```

### Option 3: Google Cloud Run (Serverless)

```bash
# Build container
gcloud builds submit --tag gcr.io/YOUR_PROJECT/hegemon-ui

# Deploy
gcloud run deploy hegemon-ui \
    --image gcr.io/YOUR_PROJECT/hegemon-ui \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

---

## 📊 Performance

### Resource Usage

- **CPU:** ~5-10% idle, ~30-50% during debate
- **Memory:** ~500MB baseline, ~1GB peak
- **Network:** Minimal (local processing)

### Optimization Tips

1. **Increase timeout** for long debates:
   ```python
   # In config.py
   DEBATE_CONFIG["checkpoint_timeout"] = 1200  # 20 min
   ```

2. **Reduce refresh rate**:
   ```python
   # In config.py
   UI_CONSTANTS["checkpoint_refresh_interval"] = 5.0  # 5 sec
   ```

3. **Limit output preview**:
   ```python
   UI_CONSTANTS["max_output_preview"] = 1000  # chars
   ```

---

## 🔒 Security

### Best Practices

1. **Never expose on public IP without auth**
2. **Use SSH tunneling** for remote access
3. **Enable HTTPS** for production
4. **Sanitize user inputs** (already implemented)
5. **Rate limit** API calls (add middleware)

### Authentication (Optional)

Add to `app.py`:

```python
import streamlit_authenticator as stauth

# Simple password protection
def check_password():
    def password_entered():
        if st.session_state["password"] == "your_secure_password":
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()
```

---

## 📞 Support

**Common Issues:**
- Checkpoint not appearing → Check console, restart Streamlit
- Feedback not submitting → Browser refresh
- Debate not starting → Check backend logs

**Logs:**
```bash
# View Streamlit logs
streamlit run streamlit_app/app.py --server.port 8080 --logger.level=debug
```

---

## 🎓 Next Steps

After deploying Streamlit UI:

1. ✅ **Test with real debates** - Verify full workflow
2. 📊 **Add Phase 2.5** - Adaptive learning (optional)
3. 🚀 **Move to Phase 3** - Multi-agent execution
4. 🌐 **Custom domain** - professional URL
5. 📈 **Analytics** - Track usage patterns

---

**Version:** 2.6.0  
**Status:** ✅ Production Ready  
**Last Updated:** October 2025
