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

<main>
  <h1>🏈 NFL Fantasy Predictor</h1>

  {#if loading}
    <p>Loading players...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <PlayerTable {players} />
  {/if}
</main>

<style>
  main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    font-family: sans-serif;
  }

  h1 {
    font-size: 2rem;
    margin-bottom: 1.5rem;
  }

  .error {
    color: red;
  }
</style>