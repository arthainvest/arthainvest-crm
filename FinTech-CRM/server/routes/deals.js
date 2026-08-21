import express from 'express';
import { v4 as uuidv4 } from 'uuid';
import pool from '../config/database.js';

const router = express.Router();

// Create a deal
router.post('/', async (req, res) => {
  try {
    const {
      contact_id, pipeline_id, stage_id, title, description,
      amount, probability = 50, expected_close_date,
      owner_id, product
    } = req.body;

    if (!contact_id || !pipeline_id || !stage_id || !title) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const id = uuidv4();

    const result = await pool.query(
      `INSERT INTO deals (
        id, contact_id, pipeline_id, stage_id, title, description,
        amount, probability, expected_close_date, owner_id, product
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
      RETURNING *`,
      [
        id, contact_id, pipeline_id, stage_id, title, description,
        amount, probability, expected_close_date, owner_id, product
      ]
    );

    res.status(201).json({
      message: 'Deal created successfully',
      deal: result.rows[0]
    });
  } catch (error) {
    console.error('Error creating deal:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get all deals
router.get('/', async (req, res) => {
  try {
    const {
      page = 1, limit = 20, pipeline_id, stage_id,
      contact_id, status, owner_id
    } = req.query;

    let query = 'SELECT * FROM deals WHERE 1=1';
    const params = [];
    let paramCount = 1;

    if (pipeline_id) {
      query += ` AND pipeline_id = $${paramCount}`;
      params.push(pipeline_id);
      paramCount++;
    }

    if (stage_id) {
      query += ` AND stage_id = $${paramCount}`;
      params.push(stage_id);
      paramCount++;
    }

    if (contact_id) {
      query += ` AND contact_id = $${paramCount}`;
      params.push(contact_id);
      paramCount++;
    }

    if (status) {
      query += ` AND status = $${paramCount}`;
      params.push(status);
      paramCount++;
    }

    if (owner_id) {
      query += ` AND owner_id = $${paramCount}`;
      params.push(owner_id);
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

// Get single deal
router.get('/:id', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM deals WHERE id = $1',
      [req.params.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Deal not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update deal
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const updates = req.body;

    let query = 'UPDATE deals SET ';
    const params = [];
    let paramCount = 1;
    const setClauses = [];

    for (const [key, value] of Object.entries(updates)) {
      if (value !== undefined && key !== 'id') {
        setClauses.push(`${key} = $${paramCount}`);
        params.push(value);
        paramCount++;
      }
    }

    if (setClauses.length === 0) {
      return res.status(400).json({ error: 'No fields to update' });
    }

    query += setClauses.join(', ') + ', updated_at = CURRENT_TIMESTAMP';
    query += ` WHERE id = $${paramCount} RETURNING *`;
    params.push(id);

    const result = await pool.query(query, params);

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Deal not found' });
    }

    res.json({
      message: 'Deal updated successfully',
      deal: result.rows[0]
    });
  } catch (error) {
    console.error('Error updating deal:', error);
    res.status(500).json({ error: error.message });
  }
});

// Move deal to different stage
router.put('/:id/move-stage', async (req, res) => {
  try {
    const { id } = req.params;
    const { stage_id } = req.body;

    if (!stage_id) {
      return res.status(400).json({ error: 'stage_id is required' });
    }

    const result = await pool.query(
      `UPDATE deals SET stage_id = $1, updated_at = CURRENT_TIMESTAMP
       WHERE id = $2 RETURNING *`,
      [stage_id, id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Deal not found' });
    }

    res.json({
      message: 'Deal moved successfully',
      deal: result.rows[0]
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Delete deal
router.delete('/:id', async (req, res) => {
  try {
    const result = await pool.query(
      'DELETE FROM deals WHERE id = $1 RETURNING *',
      [req.params.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Deal not found' });
    }

    res.json({
      message: 'Deal deleted successfully',
      deal: result.rows[0]
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
