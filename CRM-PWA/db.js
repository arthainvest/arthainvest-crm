// IndexedDB Database for offline support
class CRMDatabase {
  constructor() {
    this.dbName = 'ArthaInvestCRM';
    this.dbVersion = 1;
    this.db = null;
  }

  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => {
        console.error('Database failed to open');
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        console.log('Database opened successfully');
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Create object stores if they don't exist
        const stores = [
          { name: 'contacts', keyPath: 'id', indexes: [{ name: 'email', unique: false }] },
          { name: 'pipeline', keyPath: 'id', indexes: [{ name: 'status', unique: false }] },
          { name: 'calls', keyPath: 'id', indexes: [{ name: 'clientId', unique: false }] },
          { name: 'team', keyPath: 'id', indexes: [{ name: 'role', unique: false }] },
          { name: 'documents', keyPath: 'id', indexes: [{ name: 'clientId', unique: false }, { name: 'status', unique: false }] },
          { name: 'syncQueue', keyPath: 'id', indexes: [{ name: 'timestamp', unique: false }, { name: 'synced', unique: false }] },
          { name: 'credentials', keyPath: 'key' },
          { name: 'userSettings', keyPath: 'userId' }
        ];

        stores.forEach(store => {
          if (!db.objectStoreNames.contains(store.name)) {
            const objectStore = db.createObjectStore(store.name, { keyPath: store.keyPath });
            if (store.indexes) {
              store.indexes.forEach(index => {
                objectStore.createIndex(index.name, index.name, { unique: index.unique });
              });
            }
          }
        });
      };
    });
  }

  // CONTACTS
  async saveContact(contact) {
    const tx = this.db.transaction('contacts', 'readwrite');
    contact.id = contact.id || Date.now().toString();
    contact.syncedAt = new Date().toISOString();
    await this.addToSyncQueue('contacts', 'add', contact);
    return tx.objectStore('contacts').put(contact);
  }

  async getContacts() {
    const tx = this.db.transaction('contacts', 'readonly');
    return new Promise((resolve, reject) => {
      const request = tx.objectStore('contacts').getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async deleteContact(id) {
    const tx = this.db.transaction('contacts', 'readwrite');
    await this.addToSyncQueue('contacts', 'delete', { id });
    return tx.objectStore('contacts').delete(id);
  }

  // PIPELINE
  async savePipeline(deal) {
    const tx = this.db.transaction('pipeline', 'readwrite');
    deal.id = deal.id || Date.now().toString();
    deal.syncedAt = new Date().toISOString();
    await this.addToSyncQueue('pipeline', 'add', deal);
    return tx.objectStore('pipeline').put(deal);
  }

  async getPipeline() {
    const tx = this.db.transaction('pipeline', 'readonly');
    return new Promise((resolve, reject) => {
      const request = tx.objectStore('pipeline').getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  // CALLS
  async saveCall(call) {
    const tx = this.db.transaction('calls', 'readwrite');
    call.id = call.id || Date.now().toString();
    call.timestamp = call.timestamp || new Date().toISOString();
    call.syncedAt = new Date().toISOString();
    await this.addToSyncQueue('calls', 'add', call);
    return tx.objectStore('calls').put(call);
  }

  async getCalls() {
    const tx = this.db.transaction('calls', 'readonly');
    return new Promise((resolve, reject) => {
      const request = tx.objectStore('calls').getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  // TEAM
  async saveTeamMember(member) {
    const tx = this.db.transaction('team', 'readwrite');
    member.id = member.id || Date.now().toString();
    member.syncedAt = new Date().toISOString();
    await this.addToSyncQueue('team', 'add', member);
    return tx.objectStore('team').put(member);
  }

  async getTeam() {
    const tx = this.db.transaction('team', 'readonly');
    return new Promise((resolve, reject) => {
      const request = tx.objectStore('team').getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  // DOCUMENTS
  async saveDocument(doc) {
    const tx = this.db.transaction('documents', 'readwrite');
    doc.id = doc.id || Date.now().toString();
    doc.uploadedAt = doc.uploadedAt || new Date().toISOString();
    doc.syncedAt = new Date().toISOString();
    await this.addToSyncQueue('documents', 'add', doc);
    return tx.objectStore('documents').put(doc);
  }

  async getDocuments() {
    const tx = this.db.transaction('documents', 'readonly');
    return new Promise((resolve, reject) => {
      const request = tx.objectStore('documents').getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  // SYNC QUEUE
  async addToSyncQueue(storeName, operation, data) {
    const tx = this.db.transaction('syncQueue', 'readwrite');
    const queueItem = {
      id: Date.now().toString(),
      storeName,
      operation, // 'add', 'update', 'delete'
      data,
      timestamp: new Date().toISOString(),
      synced: false,
      retries: 0
    };
    return tx.objectStore('syncQueue').add(queueItem);
  }

  async getSyncQueue() {
    const tx = this.db.transaction('syncQueue', 'readonly');
    return new Promise((resolve, reject) => {
      const request = tx.objectStore('syncQueue').getAll();
      request.onsuccess = () => resolve(request.result.filter(item => !item.synced));
      request.onerror = () => reject(request.error);
    });
  }

  async markAsSynced(id) {
    const tx = this.db.transaction('syncQueue', 'readwrite');
    return tx.objectStore('syncQueue').update({ ...await this.getById('syncQueue', id), synced: true });
  }

  async getById(storeName, id) {
    const tx = this.db.transaction(storeName, 'readonly');
    return new Promise((resolve, reject) => {
      const request = tx.objectStore(storeName).get(id);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  // CREDENTIALS
  async saveCredentials(credentials) {
    const tx = this.db.transaction('credentials', 'readwrite');
    for (const [key, value] of Object.entries(credentials)) {
      tx.objectStore('credentials').put({ key, ...value });
    }
    return;
  }

  async getCredentials() {
    const tx = this.db.transaction('credentials', 'readonly');
    return new Promise((resolve, reject) => {
      const request = tx.objectStore('credentials').getAll();
      request.onsuccess = () => {
        const result = {};
        request.result.forEach(item => {
          const { key, ...data } = item;
          result[key] = data;
        });
        resolve(result);
      };
      request.onerror = () => reject(request.error);
    });
  }

  // USER SETTINGS
  async saveUserSettings(userId, settings) {
    const tx = this.db.transaction('userSettings', 'readwrite');
    return tx.objectStore('userSettings').put({ userId, ...settings });
  }

  async getUserSettings(userId) {
    const tx = this.db.transaction('userSettings', 'readonly');
    return new Promise((resolve, reject) => {
      const request = tx.objectStore('userSettings').get(userId);
      request.onsuccess = () => resolve(request.result || {});
      request.onerror = () => reject(request.error);
    });
  }

  // SYNC DATA TO SERVER
  async syncToServer() {
    const queue = await this.getSyncQueue();

    for (const item of queue) {
      try {
        // Send to server (implement your API endpoint)
        const response = await fetch('/api/sync', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(item)
        });

        if (response.ok) {
          await this.markAsSynced(item.id);
          console.log(`Synced: ${item.storeName} - ${item.operation}`);
        } else {
          item.retries++;
          if (item.retries < 3) {
            const tx = this.db.transaction('syncQueue', 'readwrite');
            tx.objectStore('syncQueue').put(item);
          }
        }
      } catch (error) {
        console.error('Sync error:', error);
        item.retries++;
        if (item.retries < 3) {
          const tx = this.db.transaction('syncQueue', 'readwrite');
          tx.objectStore('syncQueue').put(item);
        }
      }
    }
  }

  // CLEAR ALL DATA
  async clearAllData() {
    const tx = this.db.transaction(this.db.objectStoreNames, 'readwrite');
    for (let i = 0; i < tx.objectStoreNames.length; i++) {
      tx.objectStore(tx.objectStoreNames[i]).clear();
    }
  }
}

// Initialize database
const crmDb = new CRMDatabase();
crmDb.init().catch(err => console.error('Failed to initialize database:', err));

// Auto-sync when online
window.addEventListener('online', () => {
  console.log('Online - Starting sync');
  crmDb.syncToServer();
});

window.addEventListener('offline', () => {
  console.log('Offline - Changes saved locally');
});
