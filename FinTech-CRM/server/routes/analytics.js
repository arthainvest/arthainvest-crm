import express from 'express';
import pool from '../config/database.js';

const router = express.Router();

// Dashboard KPIs
router.get('/dashboard', async (req, res) => {
  try {
    const kpis = await pool.query(`
      SELECT
        -- Contact Stats
        COUNT(*) FILTER (WHERE contact_type = 'LEAD') as total_leads,
        COUNT(*) FILTER (WHERE contact_type = 'CLIENT') as total_clients,
        COUNT(*) FILTER (WHERE contact_type = 'WARM_NETWORK') as total_warm,

        -- Conversion
        ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'Converted') / COUNT(*), 2) as conversion_rate,
        COUNT(*) FILTER (WHERE status = 'Converted' AND DATE(date_converted) >= CURRENT_DATE - INTERVAL '30 days') as conversions_this_month,

        -- Financial
        COALESCE(SUM(aum) FILTER (WHERE contact_type = 'CLIENT'), 0) as total_aum,
        COALESCE(SUM(lifetime_commission), 0) as total_commission,
        COALESCE(SUM(budget) FILTER (WHERE contact_type = 'LEAD'), 0) as potential_budget,

        -- Activity
        COUNT(*) FILTER (WHERE last_contact >= CURRENT_DATE - INTERVAL '30 days') as active_contacts_30d,
        COUNT(DISTINCT owner) as total_users
      FROM contacts
      WHERE status != 'Dead'
    `);

    res.json(kpis.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Top performers
router.get('/top-performers', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        owner,
        COUNT(*) as total_contacts,
        COUNT(*) FILTER (WHERE status = 'Converted') as conversions,
        COALESCE(SUM(lifetime_commission), 0) as commission,
        ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'Converted') / COUNT(*), 2) as conversion_rate
      FROM contacts
      WHERE owner != 'Unassigned' AND status != 'Dead'
      GROUP BY owner
      ORDER BY commission DESC
      LIMIT 10
    `);

    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Contact source effectiveness
router.get('/source-effectiveness', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        source,
        list,
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE status = 'Converted') as conversions,
        ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'Converted') / COUNT(*), 2) as conversion_rate,
        COALESCE(AVG(budget), 0) as avg_budget,
        COALESCE(AVG(aum), 0) as avg_aum
      FROM contacts
      WHERE status != 'Dead'
      GROUP BY source, list
      ORDER BY conversion_rate DESC
    `);

    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Segment analysis
router.get('/segment-analysis', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        segment,
        tier,
        COUNT(*) as total_contacts,
        COUNT(*) FILTER (WHERE contact_type = 'CLIENT') as clients,
        COALESCE(SUM(aum), 0) as total_aum,
        COALESCE(AVG(aum), 0) as avg_aum,
        COALESCE(SUM(lifetime_commission), 0) as commission,
        ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'Converted') / COUNT(*), 2) as conversion_rate
      FROM contacts
      WHERE status != 'Dead'
      GROUP BY segment, tier
      ORDER BY commission DESC
    `);

    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Recent activities
router.get('/recent-activities', async (req, res) => {
  try {
    const limit = req.query.limit || 50;

    const result = await pool.query(`
      SELECT
        action,
        entity_type,
        user_id,
        contact_id,
        new_values,
        created_at
      FROM activity_logs
      ORDER BY created_at DESC
      LIMIT $1
    `, [limit]);

    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Deal analytics
router.get('/deals', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        status,
        COUNT(*) as deal_count,
        COALESCE(SUM(amount), 0) as total_value,
        ROUND(AVG(probability)) as avg_probability,
        ROUND(SUM(amount * probability / 100.0)) as weighted_value
      FROM deals
      WHERE status != 'LOST'
      GROUP BY status
      ORDER BY total_value DESC
    `);

    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Communication analytics
router.get('/communications', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        channel,
        type,
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE status = 'SENT') as sent,
        COUNT(*) FILTER (WHERE read_at IS NOT NULL) as read,
        ROUND(100.0 * COUNT(*) FILTER (WHERE read_at IS NOT NULL) / COUNT(*), 2) as read_rate
      FROM communications
      WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
      GROUP BY channel, type
      ORDER BY total DESC
    `);

    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
