import express from 'express';
import { v4 as uuidv4 } from 'uuid';
import pool from '../config/database.js';

const router = express.Router();

// Import contacts from CSV/Excel
router.post('/contacts/import', async (req, res) => {
  try {
    const { user_id, contacts, file_name } = req.body;

    if (!Array.isArray(contacts) || contacts.length === 0) {
      return res.status(400).json({ error: 'No contacts provided' });
    }

    const import_id = uuidv4();
    let successful = 0;
    let failed = 0;
    const errors = [];

    // Start import log
    await pool.query(
      `INSERT INTO import_logs (id, user_id, type, file_name, total_records, status)
       VALUES ($1, $2, $3, $4, $5, $6)`,
      [import_id, user_id, 'CONTACTS_IMPORT', file_name, contacts.length, 'PROCESSING']
    );

    // Process each contact
    for (let i = 0; i < contacts.length; i++) {
      try {
        const contact = contacts[i];
        const {
          name, mobile, email, city, tier, segment, contact_type,
          status, owner, source, list, budget, employer, job_title, notes
        } = contact;

        if (!name || !mobile || !segment) {
          failed++;
          errors.push({ row: i + 1, error: 'Missing required fields (name, mobile, segment)' });
          continue;
        }

        // Generate IDs
        const contact_id = `ARTH-${new Date().toISOString().split('T')[0].replace(/-/g, '')}-${uuidv4().split('-')[0].substring(0, 5)}`;
        const crypto = await import('crypto');
        const cleanMobile = (mobile || '').toLowerCase().trim();
        const cleanEmail = (email || '').toLowerCase().trim();
        const nameParts = (name || '').toLowerCase().trim().split(' ');
        const firstName = nameParts[0] || '';
        const lastName = nameParts[nameParts.length - 1] || '';
        const hashInput = `${cleanMobile}|${cleanEmail}|${firstName}|${lastName}`;
        const dedup_hash = crypto.createHash('sha256').update(hashInput).digest('hex');

        // Check for duplicate
        const existing = await pool.query(
          'SELECT contact_id FROM contacts WHERE dedup_hash = $1',
          [dedup_hash]
        );

        if (existing.rows.length > 0) {
          failed++;
          errors.push({ row: i + 1, error: `Duplicate: ${existing.rows[0].contact_id}` });
          continue;
        }

        // Insert contact
        await pool.query(
          `INSERT INTO contacts (
            contact_id, dedup_hash, name, mobile, email, city,
            tier, segment, contact_type, status, owner, source,
            list, budget, employer, job_title, notes
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)`,
          [
            contact_id, dedup_hash, name, mobile, email, city,
            tier || 'C', segment, contact_type || 'LEAD', status || 'Uncontacted',
            owner || 'Unassigned', source || 'Cold', list, budget,
            employer, job_title, notes
          ]
        );

        successful++;
      } catch (error) {
        failed++;
        errors.push({ row: i + 1, error: error.message });
      }
    }

    // Update import log
    await pool.query(
      `UPDATE import_logs SET
        status = 'COMPLETED',
        successful_records = $1,
        failed_records = $2,
        error_log = $3,
        completed_at = CURRENT_TIMESTAMP
       WHERE id = $4`,
      [successful, failed, JSON.stringify(errors), import_id]
    );

    res.json({
      import_id,
      message: 'Import completed',
      summary: {
        total: contacts.length,
        successful,
        failed,
        errors: errors.slice(0, 10) // Return first 10 errors
      }
    });
  } catch (error) {
    console.error('Import error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Export contacts to CSV
router.post('/contacts/export', async (req, res) => {
  try {
    const { filters, format = 'csv' } = req.body;

    let query = 'SELECT * FROM contacts WHERE status != \'Dead\'';
    const params = [];
    let paramCount = 1;

    if (filters) {
      if (filters.contact_type) {
        query += ` AND contact_type = $${paramCount}`;
        params.push(filters.contact_type);
        paramCount++;
      }
      if (filters.status) {
        query += ` AND status = $${paramCount}`;
        params.push(filters.status);
        paramCount++;
      }
      if (filters.tier) {
        query += ` AND tier = $${paramCount}`;
        params.push(filters.tier);
        paramCount++;
      }
      if (filters.owner) {
        query += ` AND owner = $${paramCount}`;
        params.push(filters.owner);
        paramCount++;
      }
    }

    const result = await pool.query(query, params);
    const contacts = result.rows;

    if (format === 'csv') {
      // Generate CSV
      const headers = Object.keys(contacts[0] || {});
      const csv = [
        headers.join(','),
        ...contacts.map(row =>
          headers.map(header => {
            const value = row[header];
            if (value === null || value === undefined) return '';
            if (typeof value === 'string' && value.includes(',')) {
              return `"${value.replace(/"/g, '""')}"`;
            }
            return value;
          }).join(',')
        )
      ].join('\n');

      res.setHeader('Content-Type', 'text/csv');
      res.setHeader('Content-Disposition', 'attachment; filename="contacts.csv"');
      res.send(csv);
    } else if (format === 'excel') {
      // For Excel, return JSON data - client will handle conversion
      res.json({
        data: contacts,
        filename: `contacts_${new Date().toISOString().split('T')[0]}.xlsx`
      });
    } else if (format === 'pdf') {
      // For PDF, return data - client will handle conversion
      res.json({
        data: contacts,
        filename: `contacts_${new Date().toISOString().split('T')[0]}.pdf`
      });
    }
  } catch (error) {
    console.error('Export error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get import status
router.get('/import-logs/:importId', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM import_logs WHERE id = $1',
      [req.params.importId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Import not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get import history
router.get('/import-logs', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT * FROM import_logs ORDER BY created_at DESC LIMIT 20`
    );

    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
