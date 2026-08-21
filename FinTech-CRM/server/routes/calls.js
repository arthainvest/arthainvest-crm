import express from 'express';
import { v4 as uuidv4 } from 'uuid';
import pool from '../config/database.js';

const router = express.Router();

// Log a call
router.post('/', async (req, res) => {
  try {
    const {
      contact_id, user_id, phone_number, call_type,
      call_status, duration_seconds, recording_url, transcript, notes
    } = req.body;

    if (!contact_id || !phone_number || !call_type || !call_status) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const id = uuidv4();

    const result = await pool.query(
      `INSERT INTO call_logs (
        id, contact_id, user_id, phone_number, call_type,
        call_status, duration_seconds, recording_url, transcript, notes
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
      RETURNING *`,
      [
        id, contact_id, user_id, phone_number, call_type,
        call_status, duration_seconds, recording_url, transcript, notes
      ]
    );

    // Update contact last_contact info
    await pool.query(
      `UPDATE contacts SET
        last_contact = CURRENT_TIMESTAMP,
        last_contact_type = 'Call'
       WHERE contact_id = $1`,
      [contact_id]
    );

    res.status(201).json({
      message: 'Call logged successfully',
      call: result.rows[0]
    });
  } catch (error) {
    console.error('Error logging call:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get call logs
router.get('/', async (req, res) => {
  try {
    const {
      contact_id, user_id, call_type, page = 1, limit = 20
    } = req.query;

    let query = 'SELECT * FROM call_logs WHERE 1=1';
    const params = [];
    let paramCount = 1;

    if (contact_id) {
      query += ` AND contact_id = $${paramCount}`;
      params.push(contact_id);
      paramCount++;
    }

    if (user_id) {
      query += ` AND user_id = $${paramCount}`;
      params.push(user_id);
      paramCount++;
    }

    if (call_type) {
      query += ` AND call_type = $${paramCount}`;
      params.push(call_type);
      paramCount++;
    }

    const countResult = await pool.query(
      `SELECT COUNT(*) as count FROM (${query}) as counted`,
      params
    );
    const total = parseInt(countResult.rows[0].count);

    const offset = (parseInt(page) - 1) * parseInt(limit);
    query += ` ORDER BY created_at DESC LIMIT $${paramCount} OFFSET $${paramCount + 1}`;
    params.push(limit, offset);

    const result = await pool.query(query, params);

    res.json({
      data: result.rows,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / parseInt(limit))
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get single call
router.get('/:id', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM call_logs WHERE id = $1',
      [req.params.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Call not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update call
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { call_status, duration_seconds, transcript, notes } = req.body;

    const result = await pool.query(
      `UPDATE call_logs SET
        call_status = COALESCE($1, call_status),
        duration_seconds = COALESCE($2, duration_seconds),
        transcript = COALESCE($3, transcript),
        notes = COALESCE($4, notes)
       WHERE id = $5 RETURNING *`,
      [call_status, duration_seconds, transcript, notes, id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Call not found' });
    }

    res.json({
      message: 'Call updated successfully',
      call: result.rows[0]
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Initiate click-to-call
router.post('/initiate', async (req, res) => {
  try {
    const { contact_id, user_id, phone_number } = req.body;

    if (!contact_id || !user_id || !phone_number) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    // In a real implementation, this would integrate with Twilio or similar
    const callResponse = {
      status: 'initiated',
      call_id: uuidv4(),
      contact_id,
      user_id,
      phone_number,
      initiated_at: new Date().toISOString()
    };

    res.json(callResponse);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get call statistics for user/period
router.get('/stats/:userId', async (req, res) => {
  try {
    const { userId } = req.params;

    const result = await pool.query(
      `SELECT
        COUNT(*) as total_calls,
        SUM(CASE WHEN call_status = 'COMPLETED' THEN 1 ELSE 0 END) as completed_calls,
        SUM(CASE WHEN call_status = 'MISSED' THEN 1 ELSE 0 END) as missed_calls,
        ROUND(AVG(duration_seconds)) as avg_call_duration,
        SUM(duration_seconds) as total_call_duration
       FROM call_logs
       WHERE user_id = $1`,
      [userId]
    );

    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
