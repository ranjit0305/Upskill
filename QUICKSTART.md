# Quick Start Guide

## Prerequisites
- Python 3.9+
- Node.js 18+
- MongoDB (local or Atlas)

## Backend Setup (5 minutes)

1. **Navigate to backend:**
   ```bash
   cd d:\Upskill\backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment:**
   ```bash
   copy .env.example .env
   ```
   
   Edit `.env` and update:
   - `SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
   - `MONGODB_URI` - Use `mongodb://localhost:27017` for local MongoDB

5. **Run server:**
   ```bash
   uvicorn app.main:app --reload
   ```
   
   ✅ Backend running at: http://localhost:8000

## Frontend Setup (3 minutes)

1. **Navigate to frontend:**
   ```bash
   cd d:\Upskill\frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```
   
   ✅ Frontend running at: http://localhost:5173

## First Steps

1. Open http://localhost:5173
2. Click "Sign up" and create a student account
3. Login with your credentials
4. Explore the dashboard!

## API Documentation

Visit http://localhost:8000/docs for interactive API documentation.

## Need Help?

Check the full [README.md](file:///d:/Upskill/README.md) or [walkthrough.md](file:///C:/Users/Ranjit/.gemini/antigravity/brain/ce50422f-2608-42ac-9b20-9464e3b2cb56/walkthrough.md) for detailed instructions.
