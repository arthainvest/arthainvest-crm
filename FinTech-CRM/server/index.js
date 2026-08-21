import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import pool from './config/database.js';

// Import routes
import authRoutes from './routes/auth.js';
import contactsRoutes from './routes/contacts.js';
import dealsRoutes from './routes/deals.js';
import pipelinesRoutes from './routes/pipelines.js';
import communicationsRoutes from './routes/communications.js';
import tasksRoutes from './routes/tasks.js';
import callsRoutes from './routes/calls.js';
import reportsRoutes from './routes/reports.js';
import analyticsRoutes from './routes/analytics.js';
import importExportRoutes from './routes/importExport.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb', extended: true }));

// Health Check
app.get('/health', async (req, res) => {
  try {
    const result = await pool.query('SELECT NOW()');
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      database: 'connected'
    });
  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      error: error.message
    });
  }
});

// API Routes
app.use('/api/auth', authRoutes);
app.use('/api/contacts', contactsRoutes);
app.use('/api/deals', dealsRoutes);
app.use('/api/pipelines', pipelinesRoutes);
app.use('/api/communications', communicationsRoutes);
app.use('/api/tasks', tasksRoutes);
app.use('/api/calls', callsRoutes);
app.use('/api/reports', reportsRoutes);
app.use('/api/analytics', analyticsRoutes);
app.use('/api/import-export', importExportRoutes);

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    error: 'Internal server error',
    message: err.message
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not found',
    path: req.path
  });
});

app.listen(PORT, () => {
  console.log(`🚀 CRM Server running on port ${PORT}`);
  console.log(`📊 Database connected: ${process.env.DB_HOST}:${process.env.DB_PORT}`);
});

export default app;
