import express from 'express';
import pool from '../config/database.js';

const router = express.Router();

// Get funnel report
router.get('/funnel', async (req, res) => {
  try {
    const { contact_type = 'LEAD', owner } = req.query;

    let query = `
      SELECT
        status,
        COUNT(*) as count,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER ()) as percentage,
        AVG(EXTRACT(DAY FROM (CURRENT_TIMESTAMP - status_updated_at))) as avg_days
      FROM contacts
      WHERE contact_type = $1 AND status != 'Dead'
    `;
    const params = [contact_type];
    let paramCount = 2;

    if (owner) {
      query += ` AND owner = $${paramCount}`;
      params.push(owner);
      paramCount++;
    }

    query += ` GROUP BY status ORDER BY count DESC`;

    const result = await pool.query(query, params);
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get revenue report
router.get('/revenue', async (req, res) => {
  try {
    const { segment, tier } = req.query;

    let query = `
      SELECT
        segment,
        tier,
        COUNT(*) as contact_count,
        COUNT(CASE WHEN contact_type = 'CLIENT' THEN 1 END) as client_count,
        COALESCE(SUM(CASE WHEN contact_type = 'CLIENT' THEN aum ELSE 0 END), 0) as total_aum,
        COALESCE(SUM(CASE WHEN contact_type = 'LEAD' THEN budget ELSE 0 END), 0) as potential_budget,
        COALESCE(SUM(lifetime_commission), 0) as total_commission
      FROM contacts
      WHERE status != 'Dead'
    `;
    const params = [];
    let paramCount = 1;

    if (segment) {
      query += ` AND segment = $${paramCount}`;
      params.push(segment);
      paramCount++;
    }

    if (tier) {
      query += ` AND tier = $${paramCount}`;
      params.push(tier);
      paramCount++;
    }

    query += ` GROUP BY segment, tier ORDER BY total_commission DESC`;

    const result = await pool.query(query, params);
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get activity report by user
router.get('/user-performance', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        owner,
        COUNT(*) as total_contacts,
        COUNT(CASE WHEN contact_type = 'CLIENT' THEN 1 END) as client_count,
        COUNT(CASE WHEN status = 'Interested' THEN 1 END) as interested,
        COUNT(CASE WHEN status = 'Converted' THEN 1 END) as conversions,
        COALESCE(SUM(lifetime_commission), 0) as commission_earned,
        COUNT(DISTINCT CASE WHEN last_contact IS NOT NULL THEN contact_id END) as contacted,
        ROUND(100.0 * COUNT(CASE WHEN last_contact IS NOT NULL THEN 1 END) / COUNT(*)) as contact_rate
      FROM contacts
      WHERE owner != 'Unassigned'
      GROUP BY owner
      ORDER BY commission_earned DESC
    `);

    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get contact timeline report
router.get('/contact-history/:contactId', async (req, res) => {
  try {
    const { contactId } = req.params;

    // Combine multiple activity sources
    const [communications, tasks, calls, deals] = await Promise.all([
      pool.query(
        `SELECT id, 'COMMUNICATION' as type, channel as action, created_at as timestamp
         FROM communications WHERE contact_id = $1`,
        [contactId]
      ),
      pool.query(
        `SELECT id, 'TASK' as type, status as action, updated_at as timestamp
         FROM tasks WHERE contact_id = $1`,
        [contactId]
      ),
      pool.query(
        `SELECT id, 'CALL' as type, call_status as action, created_at as timestamp
         FROM call_logs WHERE contact_id = $1`,
        [contactId]
      ),
      pool.query(
        `SELECT id, 'DEAL' as type, status as action, updated_at as timestamp
         FROM deals WHERE contact_id = $1`,
        [contactId]
      )
    ]);

    const timeline = [
      ...communications.rows,
      ...tasks.rows,
      ...calls.rows,
      ...deals.rows
    ].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    res.json(timeline);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get pipeline velocity
router.get('/pipeline-velocity/:pipelineId', async (req, res) => {
  try {
    const { pipelineId } = req.params;

    const result = await pool.query(`
      SELECT
        ps.name as stage,
        COUNT(d.id) as deal_count,
        ROUND(AVG(EXTRACT(DAY FROM (CURRENT_TIMESTAMP - d.created_at)))) as avg_days_in_stage,
        SUM(d.amount) as stage_value,
        AVG(d.probability) as avg_probability
      FROM pipeline_stages ps
      LEFT JOIN deals d ON ps.id = d.stage_id
      WHERE ps.pipeline_id = $1
      GROUP BY ps.id, ps.name
      ORDER BY ps.order_sequence ASC
    `, [pipelineId]);

    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get deals forecast
router.get('/forecast', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        DATE_TRUNC('month', expected_close_date)::DATE as month,
        status,
        COUNT(*) as deal_count,
        SUM(amount) as predicted_revenue,
        ROUND(AVG(probability)) as avg_probability,
        ROUND(SUM(amount * probability / 100.0)) as weighted_revenue
      FROM deals
      WHERE status != 'LOST' AND expected_close_date IS NOT NULL
      GROUP BY DATE_TRUNC('month', expected_close_date), status
      ORDER BY month DESC
    `);

    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
