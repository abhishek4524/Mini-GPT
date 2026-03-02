require('dotenv').config();
const express = require('express');
const cors = require('cors');
const connectDB = require('./config/db');
const analyzeRoutes = require('./routes/analyzeRoutes');

const app = express();
const PORT = process.env.PORT || 5000;

// Connect to MongoDB
connectDB();

// Middleware
app.use(cors({
  origin: 'http://localhost:8080' // or your Vite port
}));
app.use(express.json());

// Routes
app.use('/api', analyzeRoutes);

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', message: 'Server is running' });
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});