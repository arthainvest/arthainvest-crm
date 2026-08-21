import express from 'express';
import { v4 as uuidv4 } from 'uuid';
import pool from '../config/database.js';

const router = express.Router();

// Create pipeline
router.post('/', async (req, res) => {
  try {
    const { name, description, type, color = '#0066cc', created_by } = req.body;

    if (!name || !type) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const id = uuidv4();

    const result = await pool.query(
      `INSERT INTO pipelines (id, name, description, type, color, created_by)
       VALUES ($1, $2, $3, $4, $5, $6) RETURNING *`,
      [id, name, description, type, color, created_by]
    );

    res.status(201).json({
      message: 'Pipeline created successfully',
      pipeline: result.rows[0]
    });
  } catch (error) {
    console.error('Error creating pipeline:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get all pipelines
router.get('/', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM pipelines WHERE is_active = true ORDER BY order_sequence ASC'
    );

    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get pipeline with stages
router.get('/:id', async (req, res) => {
  try {
    const pipelineResult = await pool.query(
      'SELECT * FROM pipelines WHERE id = $1',
      [req.params.id]
    );

    if (pipelineResult.rows.length === 0) {
      return res.status(404).json({ error: 'Pipeline not found' });
    }

    const stagesResult = await pool.query(
      `SELECT * FROM pipeline_stages WHERE pipeline_id = $1
       ORDER BY order_sequence ASC`,
      [req.params.id]
    );

    res.json({
      ...pipelineResult.rows[0],
      stages: stagesResult.rows
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update pipeline
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { name, description, color } = req.body;

    const result = await pool.query(
      `UPDATE pipelines SET
        name = COALESCE($1, name),
        description = COALESCE($2, description),
        color = COALESCE($3, color),
        updated_at = CURRENT_TIMESTAMP
       WHERE id = $4 RETURNING *`,
      [name, description, color, id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Pipeline not found' });
    }

    res.json({
      message: 'Pipeline updated successfully',
      pipeline: result.rows[0]
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Create stage
router.post('/:pipelineId/stages', async (req, res) => {
  try {
    const { pipelineId } = req.params;
    const { name, description, color, order_sequence, is_terminal = false } = req.body;

    if (!name) {
      return res.status(400).json({ error: 'Stage name is required' });
    }

    const id = uuidv4();

    const result = await pool.query(
      `INSERT INTO pipeline_stages (
        id, pipeline_id, name, description, color, order_sequence, is_terminal
      ) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *`,
      [id, pipelineId, name, description, color, order_sequence, is_terminal]
    );

    res.status(201).json({
      message: 'Stage created successfully',
      stage: result.rows[0]
    });
  } catch (error) {
    console.error('Error creating stage:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get pipeline funnel data
router.get('/:id/funnel', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT
        ps.id,
        ps.name,
        COUNT(d.id) as deal_count,
        SUM(d.amount) as total_amount,
        AVG(d.probability) as avg_probability
       FROM pipeline_stages ps
       LEFT JOIN deals d ON ps.id = d.stage_id
       WHERE ps.pipeline_id = $1
       GROUP BY ps.id, ps.name
       ORDER BY ps.order_sequence ASC`,
      [req.params.id]
    );

    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
