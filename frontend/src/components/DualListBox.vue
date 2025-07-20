<template>
  <div>
    <div class="d-flex justify-content-between mb-1">
      <small class="form-text text-muted w-50 pe-2">Available Columns</small>
      <small class="form-text text-muted w-50 ps-2">Selected Columns</small>
    </div>
    <div class="dual-list-box">
      <div class="list-box-container">
        <input type="text" class="form-control form-control-sm mb-1" placeholder="Search..." v-model="searchQuery">
        <div class="list-box">
          <ul class="list-group" ref="availableList">
            <li v-for="option in availableOptions" :key="option" class="list-group-item" :data-id="option" @dblclick="select(option)">
              {{ option }}
            </li>
          </ul>
        </div>
      </div>
      <div class="list-box-container">
        <div class="list-box">
          <ul class="list-group" ref="selectedList">
            <li v-for="option in modelValue" :key="option" class="list-group-item" :data-id="option" @dblclick="deselect(option)">
              {{ option }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, defineProps, defineEmits } from 'vue';
import Sortable from 'sortablejs';

const props = defineProps(['options', 'modelValue']);
const emit = defineEmits(['update:modelValue']);

const searchQuery = ref('');
const availableList = ref(null);
const selectedList = ref(null);

const availableOptions = computed(() => {
  const lowerCaseQuery = searchQuery.value.toLowerCase();
  return props.options
    .filter(opt => !props.modelValue.includes(opt))
    .filter(opt => opt.toLowerCase().includes(lowerCaseQuery));
});

const select = (option) => {
  emit('update:modelValue', [...props.modelValue, option]);
};

const deselect = (option) => {
  emit('update:modelValue', props.modelValue.filter(item => item !== option));
};

onMounted(() => {
  new Sortable(selectedList.value, {
    group: 'metrics',
    animation: 150,
    onAdd: function (evt) {
      const newSelected = Array.from(evt.to.children).map(el => el.dataset.id);
      emit('update:modelValue', newSelected);
    }
  });
  new Sortable(availableList.value, {
    group: 'metrics',
    animation: 150
  });
});
</script>

<style scoped>
.dual-list-box {
  display: flex;
  justify-content: space-between;
}
.dual-list-box .list-box-container {
  width: 48%;
  display: flex;
  flex-direction: column;
}
.dual-list-box .list-box {
  border: 1px solid #ccc;
  border-radius: 4px;
  height: 200px;
  overflow-y: auto;
  padding: 0;
  flex-grow: 1;
}
.dual-list-box .list-box .list-group-item {
  cursor: grab;
  padding: 0.5rem 1rem;
  border-radius: 0;
  border-left: none;
  border-right: none;
  border-top: 1px solid #eee;
}
.dual-list-box .list-box .list-group-item:first-child {
  border-top: none;
}
</style>
