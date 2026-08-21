import express from 'express';
import { v4 as uuidv4 } from 'uuid';
import pool from '../config/database.js';

const router = express.Router();

// Create task
router.post('/', async (req, res) => {
  try {
    const {
      contact_id, deal_id, title, description, type, priority = 'MEDIUM',
      assigned_to_id, created_by_id, due_date, due_time
    } = req.body;

    if (!contact_id || !title || !due_date) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const id = uuidv4();

    const result = await pool.query(
      `INSERT INTO tasks (
        id, contact_id, deal_id, title, description, type, priority,
        assigned_to_id, created_by_id, due_date, due_time
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
      RETURNING *`,
      [
        id, contact_id, deal_id, title, description, type, priority,
        assigned_to_id, created_by_id, due_date, due_time
      ]
    );

    res.status(201).json({
      message: 'Task created successfully',
      task: result.rows[0]
    });
  } catch (error) {
    console.error('Error creating task:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get tasks
router.get('/', async (req, res) => {
  try {
    const {
      contact_id, assigned_to_id, status = 'TODO',
      page = 1, limit = 20
    } = req.query;

    let query = 'SELECT * FROM tasks WHERE 1=1';
    const params = [];
    let paramCount = 1;

    if (contact_id) {
      query += ` AND contact_id = $${paramCount}`;
      params.push(contact_id);
      paramCount++;
    }

    if (assigned_to_id) {
      query += ` AND assigned_to_id = $${paramCount}`;
      params.push(assigned_to_id);
      paramCount++;
    }

    if (status) {
      query += ` AND status = $${paramCount}`;
      params.push(status);
      paramCount++;
    }

    const countResult = await pool.query(
      `SELECT COUNT(*) as count FROM (${query}) as counted`,
      params
    );
    const total = parseInt(countResult.rows[0].count);

    const offset = (parseInt(page) - 1) * parseInt(limit);
    query += ` ORDER BY due_date ASC LIMIT $${paramCount} OFFSET $${paramCount + 1}`;
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

// Get single task
router.get('/:id', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM tasks WHERE id = $1',
      [req.params.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Task not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update task
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { status, completion_date, ...updates } = req.body;

    let query = 'UPDATE tasks SET ';
    const params = [];
    let paramCount = 1;
    const setClauses = [];

    for (const [key, value] of Object.entries({ status, completion_date, ...updates })) {
      if (value !== undefined && key !== 'id') {
        setClauses.push(`${key} = $${paramCount}`);
        params.push(value);
        paramCount++;
      }
    }

    if (status === 'COMPLETED' && !completion_date) {
      setClauses.push(`completion_date = CURRENT_TIMESTAMP`);
    }

    query += setClauses.join(', ') + ', updated_at = CURRENT_TIMESTAMP';
    query += ` WHERE id = $${paramCount} RETURNING *`;
    params.push(id);

    const result = await pool.query(query, params);

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Task not found' });
    }

    res.json({
      message: 'Task updated successfully',
      task: result.rows[0]
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Complete task
router.put('/:id/complete', async (req, res) => {
  try {
    const result = await pool.query(
      `UPDATE tasks SET
        status = 'COMPLETED',
        completion_date = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
       WHERE id = $1 RETURNING *`,
      [req.params.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Task not found' });
    }

    res.json({
      message: 'Task completed successfully',
      task: result.rows[0]
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Delete task
router.delete('/:id', async (req, res) => {
  try {
    const result = await pool.query(
      'DELETE FROM tasks WHERE id = $1 RETURNING *',
      [req.params.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Task not found' });
    }

    res.json({
      message: 'Task deleted successfully',
      task: result.rows[0]
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
