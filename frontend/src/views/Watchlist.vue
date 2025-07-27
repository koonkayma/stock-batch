<template>
  <div class="container mt-4">
    <h2>My Watchlists</h2>

    <!-- Create New Watchlist -->
    <div class="card mb-4">
      <div class="card-header">Create New Watchlist</div>
      <div class="card-body">
        <div class="input-group">
          <input type="text" class="form-control" placeholder="New Watchlist Name" v-model="newWatchlistName" @keyup.enter="createWatchlist">
          <button class="btn btn-primary" @click="createWatchlist">Create</button>
        </div>
        <div v-if="createWatchlistError" class="text-danger mt-2">{{ createWatchlistError }}</div>
      </div>
    </div>

    <!-- Select Existing Watchlist -->
    <div class="card mb-4">
      <div class="card-header">Select Watchlist</div>
      <div class="card-body">
        <select class="form-select" v-model="selectedWatchlistId" @change="selectWatchlist">
          <option :value="null">-- Select a Watchlist --</option>
          <option v-for="watchlist in watchlists" :key="watchlist.id" :value="watchlist.id">{{ watchlist.name }}</option>
        </select>
        <div v-if="watchlists.length === 0 && !isLoadingWatchlists" class="mt-2">No watchlists created yet.</div>
        <div v-if="isLoadingWatchlists" class="text-center mt-2">
          <div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div>
        </div>
      </div>
    </div>

    <!-- Tag Management -->
    <div class="card mb-4">
      <div class="card-header">Manage Tags</div>
      <div class="card-body">
        <div class="input-group mb-3">
          <input type="text" class="form-control" placeholder="New Tag Name" v-model="newTagName" @keyup.enter="createTag">
          <button class="btn btn-primary" @click="createTag">Create Tag</button>
        </div>
        <div v-if="createTagError" class="text-danger mt-2">{{ createTagError }}</div>
        <div class="d-flex flex-wrap">
          <span v-for="tag in tags" :key="tag.id" class="badge bg-secondary me-2 mb-2">
            {{ tag.name }}
            <button type="button" class="btn-close btn-close-white" aria-label="Close" @click="deleteTag(tag.id)"></button>
          </span>
        </div>
      </div>
    </div>

    <!-- Display Selected Watchlist Stocks -->
    <div v-if="selectedWatchlistId">
      <h3>Stocks in {{ selectedWatchlistName }}</h3>

      <!-- Add Stock to Watchlist -->
      <div class="card mb-4">
        <div class="card-header">Add Stock</div>
        <div class="card-body">
          <div class="input-group mb-3">
            <input type="text" class="form-control" placeholder="Ticker Symbol (e.g., AAPL)" v-model="newStockTicker" @input="lookupCompany" @keyup.enter="addStockToWatchlist">
            <button class="btn btn-primary" @click="addStockToWatchlist">Add Stock</button>
          </div>
          <div v-if="companyLookupError" class="text-danger mt-2">{{ companyLookupError }}</div>
          <div v-if="companyLookupResult" class="mt-2">
            <p><strong>Company:</strong> {{ companyLookupResult.company_name }}</p>
            <p><strong>Latest PE Ratio:</strong> {{ companyLookupResult.latest_pe_ratio || 'N/A' }}</p>
          </div>
          <div v-if="addStockError" class="text-danger mt-2">{{ addStockError }}</div>
        </div>
      </div>

      <!-- Filter and Search -->
      <div class="row mb-3">
        <div class="col-md-6">
          <label class="form-label">Filter by Tag:</label>
          <select class="form-select" v-model="selectedTagFilterId" @change="fetchStocksForWatchlist(selectedWatchlistId, selectedTagFilterId, searchQuery)">
            <option :value="null">All Tags</option>
            <option v-for="tag in tags" :key="tag.id" :value="tag.id">{{ tag.name }}</option>
          </select>
        </div>
        <div class="col-md-6">
          <label class="form-label">Search Notes:</label>
          <div class="input-group">
            <input type="text" class="form-control" placeholder="Search in notes..." v-model="searchQuery" @keyup.enter="fetchStocksForWatchlist(selectedWatchlistId, selectedTagFilterId, searchQuery)">
            <button class="btn btn-outline-secondary" type="button" @click="fetchStocksForWatchlist(selectedWatchlistId, selectedTagFilterId, searchQuery)">Search</button>
          </div>
        </div>
      </div>

      <!-- Stocks Table -->
      <div class="table-responsive">
        <table class="table table-striped table-bordered">
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Company Name</th>
              <th>Latest PE Ratio</th>
              <th class="resizable-column">Notes</th>
              <th>Tags</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoadingStocks">
              <td colspan="6" class="text-center">
                <div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div>
              </td>
            </tr>
            <tr v-else-if="stocks.length === 0">
              <td colspan="6" class="text-center">No stocks in this watchlist yet.</td>
            </tr>
            <tr v-else v-for="stock in stocks" :key="stock.id">
              <td>{{ stock.ticker }}</td>
              <td>{{ stock.company_name }}</td>
              <td>{{ stock.latest_pe_ratio || 'N/A' }}</td>
              <td class="resizable-cell">
                <div v-html="stock.note"></div>
                <button class="btn btn-sm btn-info mt-2" @click="editNote(stock)">Edit Note</button>
              </td>
              <td>
                <span v-for="tag in (stock.tags || '').split(',')" :key="tag" class="badge bg-primary me-1">{{ tag }}</span>
                <button class="btn btn-sm btn-secondary mt-2" @click="manageTagsForStock(stock)">Manage Tags</button>
              </td>
              <td>
                <button class="btn btn-sm btn-danger" @click="deleteStockFromWatchlist(stock.id)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Rich Text Editor Modal -->
      <div v-if="editingNote" class="modal" tabindex="-1" style="display: block;">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Edit Note for {{ currentStockForNote.ticker }}</h5>
              <button type="button" class="btn-close" @click="cancelEditNote"></button>
            </div>
            <div class="modal-body">
              <RichTextEditor v-model="currentNoteContent"></RichTextEditor>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="cancelEditNote">Cancel</button>
              <button type="button" class="btn btn-primary" @click="saveNote">Save Note</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Manage Tags Modal -->
      <div v-if="managingTags" class="modal" tabindex="-1" style="display: block;">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Manage Tags for {{ currentStockForTags.ticker }}</h5>
              <button type="button" class="btn-close" @click="cancelManageTags"></button>
            </div>
            <div class="modal-body">
              <div v-for="tag in tags" :key="tag.id" class="form-check">
                <input class="form-check-input" type="checkbox" :id="'tag-' + tag.id" :value="tag.id" v-model="currentStockTags" @change="toggleStockTag(tag.id)">
                <label class="form-check-label" :for="'tag-' + tag.id">
                  {{ tag.name }}
                </label>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="cancelManageTags">Done</button>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import RichTextEditor from '../components/RichTextEditor.vue';

const watchlists = ref([]);
const newWatchlistName = ref('');
const createWatchlistError = ref(null);
const selectedWatchlistId = ref(null);
const isLoadingWatchlists = ref(false);

const stocks = ref([]);
const isLoadingStocks = ref(false);
const newStockTicker = ref('');
const companyLookupResult = ref(null);
const companyLookupError = ref(null);
const addStockError = ref(null);

const editingNote = ref(false);
const currentStockForNote = ref(null);
const currentNoteContent = ref('');

const tags = ref([]);
const newTagName = ref('');
const createTagError = ref(null);
const selectedTagFilterId = ref(null);
const searchQuery = ref('');

const managingTags = ref(false);
const currentStockForTags = ref(null);
const currentStockTags = ref([]); // Array of tag IDs assigned to the current stock

const selectedWatchlistName = computed(() => {
  const selected = watchlists.value.find(w => w.id === selectedWatchlistId.value);
  return selected ? selected.name : '';
});

const fetchWatchlists = async () => {
  isLoadingWatchlists.value = true;
  try {
    const response = await fetch('/api/watchlists');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    watchlists.value = await response.json();
  } catch (error) {
    console.error("Error fetching watchlists:", error);
  } finally {
    isLoadingWatchlists.value = false;
  }
};

const createWatchlist = async () => {
  createWatchlistError.value = null;
  if (!newWatchlistName.value.trim()) {
    createWatchlistError.value = 'Watchlist name cannot be empty.';
    return;
  }

  try {
    const response = await fetch('/api/watchlists', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name: newWatchlistName.value.trim() }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`);
    }
    
    newWatchlistName.value = ''; // Clear input
    fetchWatchlists(); // Refresh the list of watchlists
  } catch (error) {
    console.error("Error creating watchlist:", error);
    createWatchlistError.value = error.message;
  }
};

const fetchStocksForWatchlist = async (watchlistId, tagId = null, searchQuery = null) => {
  if (!watchlistId) {
    stocks.value = [];
    return;
  }
  isLoadingStocks.value = true;
  let url = `/api/watchlists/${watchlistId}/stocks`;
  const params = new URLSearchParams();
  if (tagId) {
    params.append('tag_id', tagId);
  }
  if (searchQuery) {
    params.append('search_query', searchQuery);
  }
  if (params.toString()) {
    url += `?${params.toString()}`;
  }

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    stocks.value = await response.json();
  } catch (error) {
    console.error("Error fetching stocks:", error);
  } finally {
    isLoadingStocks.value = false;
  }
};

const selectWatchlist = () => {
  fetchStocksForWatchlist(selectedWatchlistId.value, selectedTagFilterId.value, searchQuery.value);
};

const lookupCompany = async () => {
  companyLookupResult.value = null;
  companyLookupError.value = null;
  if (!newStockTicker.value.trim()) {
    return;
  }
  try {
    const response = await fetch(`/api/company_lookup/${newStockTicker.value.trim()}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    companyLookupResult.value = await response.json();
  } catch (error) {
    console.error("Error looking up company:", error);
    companyLookupError.value = 'Company not found or error fetching data.';
  }
};

const addStockToWatchlist = async () => {
  addStockError.value = null;
  if (!selectedWatchlistId.value) {
    addStockError.value = 'Please select a watchlist first.';
    return;
  }
  if (!newStockTicker.value.trim()) {
    addStockError.value = 'Ticker cannot be empty.';
    return;
  }

  try {
    const response = await fetch(`/api/watchlists/${selectedWatchlistId.value}/stocks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ticker: newStockTicker.value.trim() }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`);
    }
    
    newStockTicker.value = ''; // Clear input
    companyLookupResult.value = null; // Clear lookup result
    fetchStocksForWatchlist(selectedWatchlistId.value, selectedTagFilterId.value, searchQuery.value); // Refresh stocks
  } catch (error) {
    console.error("Error adding stock:", error);
    addStockError.value = error.message;
  }
};

const deleteStockFromWatchlist = async (stockId) => {
  if (!confirm('Are you sure you want to delete this stock?')) {
    return;
  }
  try {
    const response = await fetch(`/api/watchlists/${selectedWatchlistId.value}/stocks/${stockId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || `HTTP error! status: ${response.status}`);
    }
    fetchStocksForWatchlist(selectedWatchlistId.value, selectedTagFilterId.value, searchQuery.value); // Refresh stocks
  } catch (error) {
    console.error("Error deleting stock:", error);
    alert(`Failed to delete stock: ${error.message}`);
  }
};

const editNote = (stock) => {
  currentStockForNote.value = stock;
  currentNoteContent.value = stock.note;
  editingNote.value = true;
};

const saveNote = async () => {
  if (!currentStockForNote.value) return;

  try {
    const response = await fetch(`/api/watchlists/${selectedWatchlistId.value}/stocks/${currentStockForNote.value.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ note: currentNoteContent.value }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || `HTTP error! status: ${response.status}`);
    }
    editingNote.value = false;
    fetchStocksForWatchlist(selectedWatchlistId.value, selectedTagFilterId.value, searchQuery.value); // Refresh stocks to show updated note
  } catch (error) {
    console.error("Error saving note:", error);
    alert(`Failed to save note: ${error.message}`);
  }
};

const cancelEditNote = () => {
  editingNote.value = false;
  currentStockForNote.value = null;
  currentNoteContent.value = '';
};

const fetchTags = async () => {
  try {
    const response = await fetch('/api/tags');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    tags.value = await response.json();
  } catch (error) {
    console.error("Error fetching tags:", error);
  }
};

const createTag = async () => {
  createTagError.value = null;
  if (!newTagName.value.trim()) {
    createTagError.value = 'Tag name cannot be empty.';
    return;
  }

  try {
    const response = await fetch('/api/tags', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name: newTagName.value.trim() }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`);
    }
    newTagName.value = '';
    fetchTags(); // Refresh tags list
  } catch (error) {
    console.error("Error creating tag:", error);
    createTagError.value = error.message;
  }
};

const deleteTag = async (tagId) => {
  if (!confirm('Are you sure you want to delete this tag? This will remove it from all stocks.')) {
    return;
  }
  try {
    const response = await fetch(`/api/tags/${tagId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || `HTTP error! status: ${response.status}`);
    }
    fetchTags(); // Refresh tags list
    fetchStocksForWatchlist(selectedWatchlistId.value, selectedTagFilterId.value, searchQuery.value); // Refresh stocks in case tags were removed
  } catch (error) {
    console.error("Error deleting tag:", error);
    alert(`Failed to delete tag: ${error.message}`);
  }
};

const manageTagsForStock = (stock) => {
  currentStockForTags.value = stock;
  currentStockTags.value = stock.tags ? stock.tags.split(',').map(tagName => {
    const tag = tags.value.find(t => t.name === tagName.trim());
    return tag ? tag.id : null;
  }).filter(id => id !== null) : [];
  managingTags.value = true;
};

const toggleStockTag = async (tagId) => {
  const stockId = currentStockForTags.value.id;
  const isAssigned = currentStockTags.value.includes(tagId);

  try {
    if (isAssigned) {
      // Remove tag
      await fetch(`/api/watchlists/${selectedWatchlistId.value}/stocks/${stockId}/tags/${tagId}`, {
        method: 'DELETE',
      });
    } else {
      // Assign tag
      await fetch(`/api/watchlists/${selectedWatchlistId.value}/stocks/${stockId}/tags`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tag_id: tagId }),
      });
    }
    // Refresh stocks and current stock tags after successful operation
    fetchStocksForWatchlist(selectedWatchlistId.value, selectedTagFilterId.value, searchQuery.value);
    // Update currentStockTags to reflect the change immediately in the modal
    if (isAssigned) {
      currentStockTags.value = currentStockTags.value.filter(id => id !== tagId);
    } else {
      currentStockTags.value.push(tagId);
    }
  } catch (error) {
    console.error("Error toggling tag:", error);
    alert(`Failed to update tag: ${error.message}`);
  }
};

const cancelManageTags = () => {
  managingTags.value = false;
  currentStockForTags.value = null;
  currentStockTags.value = [];
};

onMounted(() => {
  fetchWatchlists();
  fetchTags();
});
watch(selectedWatchlistId, (newVal) => {
  if (newVal) {
    fetchStocksForWatchlist(newVal, selectedTagFilterId.value, searchQuery.value);
  }
});
</script>

<style scoped>
/* Add any specific styles for this component */
.modal {
  background-color: rgba(0, 0, 0, 0.5); /* Darken background */
}

.resizable-column {
  resize: both;
  overflow: auto;
  min-width: 150px; /* Adjust as needed */
}

.resizable-cell {
  resize: both;
  overflow: auto;
  min-width: 150px; /* Adjust as needed */
}
</style>