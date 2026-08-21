import express from 'express';
import { v4 as uuidv4 } from 'uuid';
import pool from '../config/database.js';

const router = express.Router();

// Create communication
router.post('/', async (req, res) => {
  try {
    const {
      contact_id, deal_id, type, channel, direction = 'OUTBOUND',
      subject, message, from_id, to_number, to_email
    } = req.body;

    if (!contact_id || !type || !channel) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const id = uuidv4();

    const result = await pool.query(
      `INSERT INTO communications (
        id, contact_id, deal_id, type, channel, direction,
        subject, message, from_id, to_number, to_email, status
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
      RETURNING *`,
      [
        id, contact_id, deal_id, type, channel, direction,
        subject, message, from_id, to_number, to_email, 'SENT'
      ]
    );

    // Update contact last_contact info
    await pool.query(
      `UPDATE contacts SET
        last_contact = CURRENT_TIMESTAMP,
        last_contact_type = $1
       WHERE contact_id = $2`,
      [channel, contact_id]
    );

    res.status(201).json({
      message: 'Communication created successfully',
      communication: result.rows[0]
    });
  } catch (error) {
    console.error('Error creating communication:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get communications
router.get('/', async (req, res) => {
  try {
    const { contact_id, deal_id, type, channel, page = 1, limit = 20 } = req.query;

    let query = 'SELECT * FROM communications WHERE 1=1';
    const params = [];
    let paramCount = 1;

    if (contact_id) {
      query += ` AND contact_id = $${paramCount}`;
      params.push(contact_id);
      paramCount++;
    }

    if (deal_id) {
      query += ` AND deal_id = $${paramCount}`;
      params.push(deal_id);
      paramCount++;
    }

    if (type) {
      query += ` AND type = $${paramCount}`;
      params.push(type);
      paramCount++;
    }

    if (channel) {
      query += ` AND channel = $${paramCount}`;
      params.push(channel);
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

// Get single communication
router.get('/:id', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM communications WHERE id = $1',
      [req.params.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Communication not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update communication
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { status, read_at } = req.body;

    const result = await pool.query(
      `UPDATE communications SET
        status = COALESCE($1, status),
        read_at = COALESCE($2, read_at),
        updated_at = CURRENT_TIMESTAMP
       WHERE id = $3 RETURNING *`,
      [status, read_at, id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Communication not found' });
    }

    res.json({
      message: 'Communication updated successfully',
      communication: result.rows[0]
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get communication templates
router.get('/templates/email', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM email_templates WHERE is_active = true ORDER BY name ASC'
    );

    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/templates/whatsapp', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM whatsapp_templates WHERE is_active = true ORDER BY name ASC'
    );

    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
