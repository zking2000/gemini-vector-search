<template>
  <div class="document-list">
    <div class="header">
      <h2>{{ $t('documentList.title') }}</h2>
      <div class="actions">
        <button @click="uploadDocument" class="upload-btn">
          {{ $t('documentList.upload') }}
        </button>
      </div>
    </div>

    <div v-if="documents.length === 0" class="empty-state">
      {{ $t('documentList.empty') }}
    </div>

    <div v-else class="documents">
      <div v-for="doc in documents" :key="doc.id" class="document-item">
        <div class="document-info">
          <div class="title">{{ doc.title }}</div>
          <div class="metadata">
            <span class="source">{{ $t('documentList.source') }}: {{ doc.metadata.source || $t('common.unknown') }}</span>
            <span class="strategy">{{ $t('documentList.chunkingStrategy.' + (doc.metadata.chunking_strategy || 'fixed_size')) }}</span>
            <span class="time">{{ $t('documentList.createdAt') }}: {{ formatDate(doc.created_at) }}</span>
          </div>
        </div>
        <div class="actions">
          <button @click="deleteDocument(doc.id)" class="delete-btn">
            {{ $t('documentList.delete') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DocumentList',
  props: {
    documents: {
      type: Array,
      required: true
    }
  },
  methods: {
    uploadDocument() {
      this.$emit('upload');
    },
    deleteDocument(id) {
      this.$emit('delete', id);
    },
    formatDate(date) {
      return new Date(date).toLocaleString();
    }
  }
}
</script>

<style scoped>
.document-list {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.upload-btn {
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

.documents {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.document-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.document-info {
  flex: 1;
}

.title {
  font-weight: bold;
  margin-bottom: 8px;
}

.metadata {
  display: flex;
  gap: 16px;
  color: #666;
  font-size: 0.9em;
}

.delete-btn {
  padding: 6px 12px;
  background-color: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style> 