<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

// Explicit marker icon — the default icon's image paths break under bundlers.
const PIN_ICON = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

const props = defineProps({
  places: { type: Array, default: () => [] },
})

const mapEl = ref(null)
let map = null

function locatable() {
  return props.places.filter(p => p.lat != null && p.lng != null)
}

onMounted(async () => {
  const points = locatable()
  if (!points.length) return
  await nextTick()

  map = L.map(mapEl.value, { scrollWheelZoom: false })
  // CARTO Voyager — modern, clean color basemap (no API key).
  L.tileLayer(
    'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    {
      attribution: '© OpenStreetMap, © CARTO',
      subdomains: 'abcd',
      maxZoom: 20,
      detectRetina: true,
    },
  ).addTo(map)

  const markers = points.map(p => L.marker([p.lat, p.lng], { icon: PIN_ICON }).bindPopup(`<strong>${p.name}</strong>`))
  const group = L.featureGroup(markers).addTo(map)
  if (points.length === 1) map.setView([points[0].lat, points[0].lng], 15)
  else map.fitBounds(group.getBounds().pad(0.25))
})

onBeforeUnmount(() => {
  if (map) { map.remove(); map = null }
})
</script>

<template>
  <div v-if="locatable().length" class="bg-white rounded-2xl shadow-sm border border-surface-100 overflow-hidden">
    <div ref="mapEl" class="h-64 w-full" />
    <div class="px-5 py-3 space-y-1">
      <p v-for="(p, i) in places" :key="i" class="text-sm text-surface-700">
        <span class="font-semibold">{{ p.name }}</span>
        <span v-if="p.address" class="text-surface-500"> — {{ p.address }}</span>
      </p>
    </div>
  </div>
</template>
