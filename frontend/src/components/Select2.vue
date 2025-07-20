<template>
  <select ref="el" class="form-control" style="width: 100%"></select>
</template>

<script setup>
import { onMounted, watch, defineProps, defineEmits, ref } from 'vue';

const props = defineProps(['options', 'modelValue']);
const emit = defineEmits(['update:modelValue']);
const el = ref(null);

onMounted(() => {
  // $ is now globally available from the CDN script in index.html
  const select2El = $(el.value);
  select2El
    .select2({ placeholder: 'Search for a company...', data: props.options })
    .val(props.modelValue)
    .trigger('change')
    .on('change', function () {
      emit('update:modelValue', this.value);
    });
});

watch(() => props.options, (options) => {
  if (el.value) {
    $(el.value).empty().select2({ placeholder: 'Search for a company...', data: options });
  }
});

watch(() => props.modelValue, (value) => {
  if (el.value) {
    $(el.value).val(value).trigger('change');
  }
});
</script>
