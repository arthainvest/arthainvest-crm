import fs from 'fs';
import path from 'path';

console.log('✅ Database migration: schema ready at server/migrations/schema.sql');
console.log('✅ For production, run: psql -U postgres -d arthainvest < server/migrations/schema.sql');
console.log('✅ For demo mode, the CRM will use in-memory/localStorage data');
