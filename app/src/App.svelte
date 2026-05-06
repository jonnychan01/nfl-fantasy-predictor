<script>
  import { onMount } from 'svelte'
import PlayerTable from './lib/PlayerTable.svelte'
let players = []
let loading = true
let error = null
onMount(async () => {
try {
const res = await fetch('http://localhost:8000/api/players')
players = await res.json()
    } catch (e) {
error = 'Failed to load players. Is the API running?'
    } finally {
loading = false
    }
  })
</script>
<main class="max-w-[1200px] mx-auto p-8 text-center">
<h1 class="text-3xl mb-6 font-semibold text-gray-900">🏈 NFL Fantasy Predictor</h1>
  {#if loading}
<p>Loading players...</p>
  {:else if error}
<p class="text-red-500">{error}</p>
  {:else}
<PlayerTable {players} />
  {/if}
</main>