import express from 'express';
import { v4 as uuidv4 } from 'uuid';
import crypto from 'crypto';
import pool from '../config/database.js';

const router = express.Router();

// Helper function to generate contact ID
const generateContactId = () => {
  const date = new Date().toISOString().split('T')[0].replace(/-/g, '');
  const serial = Math.floor(Math.random() * 10000).toString().padStart(5, '0');
  return `ARTH-${date}-${serial}`;
};

// Helper function to generate dedup hash
const generateDedupHash = (mobile, email, name) => {
  const cleanMobile = (mobile || '').toLowerCase().trim();
  const cleanEmail = (email || '').toLowerCase().trim();
  const nameParts = (name || '').toLowerCase().trim().split(' ');
  const firstName = nameParts[0] || '';
  const lastName = nameParts[nameParts.length - 1] || '';

  const hashInput = `${cleanMobile}|${cleanEmail}|${firstName}|${lastName}`;
  return crypto.createHash('sha256').update(hashInput).digest('hex');
};

// Create a new contact
router.post('/', async (req, res) => {
  try {
    const {
      name, mobile, email, city, tier, segment, contact_type,
      status = 'Uncontacted', owner = 'Unassigned', source,
      list, budget, employer, job_title, notes
    } = req.body;

    // Validation
    if (!name || !mobile || !contact_type || !segment) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const contact_id = generateContactId();
    const dedup_hash = generateDedupHash(mobile, email, name);

    // Check for existing dedup_hash
    const existing = await pool.query(
      'SELECT contact_id FROM contacts WHERE dedup_hash = $1',
      [dedup_hash]
    );

    if (existing.rows.length > 0) {
      return res.status(409).json({
        error: 'Duplicate contact',
        existing_id: existing.rows[0].contact_id,
        message: 'A contact with this phone/email already exists'
      });
    }

    const result = await pool.query(
      `INSERT INTO contacts (
        contact_id, dedup_hash, name, mobile, email, city,
        tier, segment, contact_type, status, owner, source,
        list, budget, employer, job_title, notes
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
      RETURNING *`,
      [
        contact_id, dedup_hash, name, mobile, email, city,
        tier || 'C', segment, contact_type, status, owner, source || 'Cold',
        list, budget, employer, job_title, notes
      ]
    );

    res.status(201).json({
      message: 'Contact created successfully',
      contact: result.rows[0]
    });
  } catch (error) {
    console.error('Error creating contact:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get all contacts with filters
router.get('/', async (req, res) => {
  try {
    const {
      page = 1, limit = 20, search, contact_type,
      status, tier, segment, owner, source
    } = req.query;

    let query = 'SELECT * FROM contacts WHERE 1=1';
    const params = [];
    let paramCount = 1;

    if (search) {
      query += ` AND (name ILIKE $${paramCount} OR mobile LIKE $${paramCount} OR email ILIKE $${paramCount})`;
      params.push(`%${search}%`);
      paramCount++;
    }

    if (contact_type) {
      query += ` AND contact_type = $${paramCount}`;
      params.push(contact_type);
      paramCount++;
    }

    if (status) {
      query += ` AND status = $${paramCount}`;
      params.push(status);
      paramCount++;
    }

    if (tier) {
      query += ` AND tier = $${paramCount}`;
      params.push(tier);
      paramCount++;
    }

    if (segment) {
      query += ` AND segment = $${paramCount}`;
      params.push(segment);
      paramCount++;
    }

    if (owner) {
      query += ` AND owner = $${paramCount}`;
      params.push(owner);
      paramCount++;
    }

    if (source) {
      query += ` AND source = $${paramCount}`;
      params.push(source);
      paramCount++;
    }

    // Count total
    const countResult = await pool.query(
      `SELECT COUNT(*) as count FROM (${query}) as counted`,
      params
    );
    const total = parseInt(countResult.rows[0].count);

    // Pagination
    const offset = (parseInt(page) - 1) * parseInt(limit);
    query += ` ORDER BY date_added DESC LIMIT $${paramCount} OFFSET $${paramCount + 1}`;
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
    console.error('Error fetching contacts:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get single contact
router.get('/:id', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM contacts WHERE contact_id = $1',
      [req.params.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Contact not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update contact
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const updates = req.body;

    let query = 'UPDATE contacts SET ';
    const params = [];
    let paramCount = 1;
    const setClauses = [];

    // Build dynamic update query
    for (const [key, value] of Object.entries(updates)) {
      if (value !== undefined && key !== 'contact_id' && key !== 'dedup_hash') {
        setClauses.push(`${key} = $${paramCount}`);
        params.push(value);
        paramCount++;
      }
    }

    if (setClauses.length === 0) {
      return res.status(400).json({ error: 'No fields to update' });
    }

    query += setClauses.join(', ');
    query += ` WHERE contact_id = $${paramCount} RETURNING *`;
    params.push(id);

    const result = await pool.query(query, params);

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Contact not found' });
    }

    res.json({
      message: 'Contact updated successfully',
      contact: result.rows[0]
    });
  } catch (error) {
    console.error('Error updating contact:', error);
    res.status(500).json({ error: error.message });
  }
});

// Delete contact (soft delete - move to Dead status)
router.delete('/:id', async (req, res) => {
  try {
    const result = await pool.query(
      `UPDATE contacts SET status = 'Dead', updated_at = CURRENT_TIMESTAMP
       WHERE contact_id = $1 RETURNING *`,
      [req.params.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Contact not found' });
    }

    res.json({
      message: 'Contact deleted successfully',
      contact: result.rows[0]
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get contact activity history
router.get('/:id/activity', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT * FROM activity_logs WHERE contact_id = $1
       ORDER BY created_at DESC LIMIT 100`,
      [req.params.id]
    );

    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get contacts summary/dashboard stats
router.get('/stats/summary', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        COUNT(*) FILTER (WHERE contact_type = 'LEAD') as total_leads,
        COUNT(*) FILTER (WHERE contact_type = 'CLIENT') as total_clients,
        COUNT(*) FILTER (WHERE contact_type = 'WARM_NETWORK') as total_warm,
        COUNT(*) FILTER (WHERE status = 'Uncontacted') as uncontacted,
        COUNT(*) FILTER (WHERE status = 'Interested') as interested,
        COUNT(*) FILTER (WHERE status = 'Converted') as converted,
        SUM(CASE WHEN aum IS NOT NULL THEN aum ELSE 0 END) as total_aum,
        SUM(CASE WHEN budget IS NOT NULL THEN budget ELSE 0 END) as total_budget,
        SUM(CASE WHEN lifetime_commission IS NOT NULL THEN lifetime_commission ELSE 0 END) as total_commission
      FROM contacts
      WHERE status != 'Dead'
    `);

    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
