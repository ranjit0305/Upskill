# Upskill - AI Placement Preparation Platform

An AI-based, open-source placement preparation platform designed to help students prepare effectively for campus placements through structured practice, continuous performance analysis, personalized learning paths, and company-specific preparation.

## 🎯 Features

- **User Management**: Role-based authentication (Student, Senior/Alumni, Admin)
- **Assessment System**: Aptitude, Technical MCQs, and Coding challenges
- **Performance Analytics**: Track accuracy, speed, consistency, and improvement
- **AI Readiness Scoring**: ML-based placement readiness calculation
- **Personalized Learning**: Adaptive recommendations based on performance
- **Company-Specific Prep**: Targeted preparation for specific companies

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **MongoDB**: NoSQL database with Beanie ODM
- **JWT**: Secure authentication
- **Scikit-learn**: ML for readiness scoring
- **Judge0 API**: Code execution engine

### Frontend
- **React**: UI library
- **Vite**: Build tool
- **React Router**: Navigation
- **Recharts**: Data visualization
- **Axios**: HTTP client

## 📦 Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- MongoDB (local or Atlas)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
copy .env.example .env
```

5. Update `.env` with your configuration:
- MongoDB URI
- JWT Secret Key
- Judge0 API credentials

6. Run the server:
```bash
uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run development server:
```bash
npm run dev
```

Frontend will be available at `http://localhost:5173`

## 🚀 Usage

1. **Register**: Create an account as Student, Senior, or Admin
2. **Login**: Access your dashboard
3. **Take Tests**: Practice aptitude, technical, and coding questions
4. **View Analytics**: Track your performance and readiness score
5. **Follow Recommendations**: Get personalized study plans

## 📊 API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔑 Key Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user

### Assessment
- `GET /assessment/questions` - Get questions
- `POST /assessment/questions` - Create question (Admin/Senior)
- `POST /assessment/submissions` - Submit assessment

### Performance
- `GET /performance/me` - Get performance metrics
- `GET /performance/readiness` - Get readiness score

## 🎨 Project Structure

```
Upskill/
├── backend/
│   ├── app/
│   │   ├── models/          # Database models
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── utils/           # Utilities
│   │   └── main.py          # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── context/         # Context providers
│   │   ├── services/        # API services
│   │   └── App.jsx
│   └── package.json
└── README.md
```

## 🤝 Contributing

This is an open-source project. Contributions are welcome!

## 📝 License

MIT License

## 👥 User Roles

- **Student**: Take tests, view analytics, get recommendations
- **Senior/Alumni**: Share interview experiences, create questions
- **Admin**: Manage content, view batch analytics

## 🔮 Future Enhancements

- Mock interview simulations
- LLM-powered feedback generation
- Advanced analytics dashboards
- Mobile application
- Batch management for placement cells

## 📧 Support

For issues and questions, please open an issue on GitHub.

---

Built with ❤️ for students preparing for placements
