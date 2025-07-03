# Hey Chef v2 - Fix Instructions

## 🐛 **Current Issues**

The Hey Chef v2 application has several import and configuration issues preventing it from starting properly.

## 🔧 **Issues Identified**

### **1. Import Errors in API Files**
- ✅ **FIXED**: `websocket.py` - Fixed import of `RecipeRequest` → `RecipeSearchRequest`
- ✅ **FIXED**: `recipes.py` - Fixed import of `RecipeRequest` → `RecipeSearchRequest`  
- ✅ **FIXED**: `websocket.py` - Fixed `AudioStatus` usage → replaced with dict

### **2. Configuration Issues**
- ❌ **NEEDS FIX**: `Settings` class missing `logging` attribute
- ❌ **NEEDS FIX**: Logger setup expects different configuration structure

### **3. Missing Model Classes**
- ❌ **NEEDS FIX**: Several model classes referenced in imports don't exist

## 🚀 **Step-by-Step Fix Instructions**

### **Step 1: Fix Settings Configuration**

**File**: `/Users/jamesdowzard/Documents/code/gh/hey_chef/hey_chef_v2/backend/app/core/config.py`

Add a LoggingSettings class and update the main Settings class:

```python
@dataclass
class LoggingSettings:
    """Logging settings for compatibility"""
    logs_directory: str = "logs"
    log_level: str = "INFO"
    max_session_logs: int = 5

class Settings:
    # ... existing attributes ...
    
    # Add logging settings
    logging: LoggingSettings = None
    
    def __init__(self):
        if self.logging is None:
            self.logging = LoggingSettings()
        # ... rest of init ...
```

### **Step 2: Simplify Logger Usage (Alternative)**

**Alternative approach - simplify the main.py logging instead:**

**File**: `/Users/jamesdowzard/Documents/code/gh/hey_chef/hey_chef_v2/backend/main.py`

Replace the complex logger setup with basic Python logging (already partially done):

```python
# Instead of:
# from app.core.logger import setup_logging, get_logger
# logger = setup_logging(settings)

# Use:
import logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hey_chef_v2")
```

### **Step 3: Fix Remaining Import Issues**

Check all API files for missing model imports and replace with existing models:

**Files to check:**
- `/Users/jamesdowzard/Documents/code/gh/hey_chef/hey_chef_v2/backend/app/api/websocket.py`
- `/Users/jamesdowzard/Documents/code/gh/hey_chef/hey_chef_v2/backend/app/api/audio.py`
- `/Users/jamesdowzard/Documents/code/gh/hey_chef/hey_chef_v2/backend/app/api/recipes.py`

**Common fixes needed:**
- Replace undefined model classes with dict objects
- Use existing model classes from `app.core.models`
- Remove unused imports

### **Step 4: Test Backend Startup**

```bash
cd /Users/jamesdowzard/Documents/code/gh/hey_chef/hey_chef_v2/backend
python main.py
```

**Expected output:**
```
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### **Step 5: Test Frontend Startup**

```bash
cd /Users/jamesdowzard/Documents/code/gh/hey_chef/hey_chef_v2/frontend
npm run dev
```

**Expected output:**
```
➜  Local:   http://localhost:3000/
➜  Network: http://192.168.x.x:3000/
```

### **Step 6: Test Full Application**

1. **Start both servers** (backend and frontend)
2. **Navigate to** http://localhost:3000
3. **Check connection status** - should show "Connected"
4. **Test basic functionality**:
   - Settings panel loads
   - Voice controller shows ready state
   - No console errors in browser

## 🔍 **Debugging Commands**

### **Check Backend Health**
```bash
curl http://localhost:8000/health
```

### **Check API Documentation**
Visit: http://localhost:8000/docs

### **Check WebSocket Connection**
```bash
# In browser console:
const ws = new WebSocket('ws://localhost:8000/ws/audio');
ws.onopen = () => console.log('Connected');
ws.onmessage = (msg) => console.log('Message:', msg.data);
```

### **Check Frontend Console**
Open browser DevTools and look for:
- WebSocket connection messages
- React component errors
- Network request failures

## 📋 **Common Error Solutions**

### **"ModuleNotFoundError" or "ImportError"**
- Check if all required packages are installed: `pip install -r requirements.txt`
- Verify Python path includes the app directory
- Check for typos in import statements

### **"WebSocket connection failed"**
- Ensure backend is running on port 8000
- Check firewall settings
- Verify CORS configuration in FastAPI

### **"Cannot find module" (Frontend)**
- Run `npm install` in frontend directory
- Check if `lucide-react` is in package.json dependencies
- Clear node_modules and reinstall if needed

### **Audio/Voice Issues**
- Set environment variables: `OPENAI_API_KEY` and `PICO_ACCESS_KEY`
- Check microphone permissions in browser
- Verify API keys are valid

## ✅ **Success Criteria**

The application is working correctly when:

1. ✅ Backend starts without errors on port 8000
2. ✅ Frontend starts without errors on port 3000  
3. ✅ Browser shows "Connected" status
4. ✅ Settings panel loads and displays options
5. ✅ Voice controller shows "Voice control ready" status
6. ✅ No error messages in browser console
7. ✅ API documentation accessible at http://localhost:8000/docs

## 🎯 **Next Steps After Fixes**

Once the application starts successfully:

1. **Test voice functionality** with API keys
2. **Test recipe integration** with Notion API
3. **Verify all UI components** work as expected
4. **Check mobile responsiveness**
5. **Test different chef personality modes**

## 📞 **Additional Help**

If you encounter issues not covered here:

1. **Check logs** in terminal output for specific error messages
2. **Use browser DevTools** to inspect network requests and console errors
3. **Test individual components** by accessing API endpoints directly
4. **Verify environment variables** are set correctly

The goal is to have a fully functional Hey Chef v2 application with real-time voice interaction capabilities!