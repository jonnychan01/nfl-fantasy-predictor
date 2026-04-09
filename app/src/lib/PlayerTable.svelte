<script>
  import Modal from '../components/Modal.svelte'

  export let players = []

  const POSITIONS = ['ALL', 'QB', 'RB', 'WR', 'TE', 'K', 'DEF']

  let selectedPosition = 'ALL'
  let sortColumn = 'projected_points'
  let sortAsc = false
  let searchQuery = ''
  let selectedPlayer = null

  $: filtered = players
    .filter(p => selectedPosition === 'ALL' || p.position === selectedPosition)
    .filter(p => p.name.toLowerCase().includes(searchQuery.toLowerCase()))

  $: sorted = [...filtered].sort((a, b) => {
    const valA = a[sortColumn] ?? ''
    const valB = b[sortColumn] ?? ''
    if (valA < valB) return sortAsc ? -1 : 1
    if (valA > valB) return sortAsc ? 1 : -1
    return 0
  })

  function handleSort(col) {
    if (sortColumn === col) {
      sortAsc = !sortAsc
    } else {
      sortColumn = col
      sortAsc = false
    }
  }

  function sortIcon(col) {
    if (sortColumn !== col) return '↕'
    return sortAsc ? '↑' : '↓'
  }
</script>

<div class="controls">
  <input
    type="text"
    placeholder="Search players..."
    bind:value={searchQuery}
  />
  {#each POSITIONS as pos}
    <button
      class:active={selectedPosition === pos}
      on:click={() => selectedPosition = pos}
    >
      {pos}
    </button>
  {/each}
</div>

<div class="table-wrapper">
  <table>
    <thead>
      <tr>
        <th on:click={() => handleSort('name')}>Name {sortIcon('name')}</th>
        <th on:click={() => handleSort('position')}>POS {sortIcon('position')}</th>
        <th on:click={() => handleSort('team')}>Team {sortIcon('team')}</th>
        <th on:click={() => handleSort('age')}>Age {sortIcon('age')}</th>
        <th on:click={() => handleSort('projected_points')}>Projected Pts {sortIcon('projected_points')}</th>
      </tr>
    </thead>
    <tbody>
      {#each sorted as player}
        <tr on:click={() => selectedPlayer = player} style="cursor:pointer">
          <td>{player.name}</td>
          <td><span class="pos-badge {player.position}">{player.position}</span></td>
          <td>{player.team ?? '—'}</td>
          <td>{player.age ?? '—'}</td>
          <td class="pts">{player.projected_points}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

{#if selectedPlayer}
  <Modal player={selectedPlayer} onClose={() => selectedPlayer = null} />
{/if}

<style>
  .controls {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
    justify-content: center;
  }

  button {
    padding: 0.4rem 1rem;
    border: 1px solid #374151;
    background: #1f2937;
    color: #9ca3af;
    border-radius: 999px;
    cursor: pointer;
    font-size: 0.85rem;
    transition: all 0.2s;
  }

  button:hover {
    background: #374151;
    color: #f9fafb;
  }

  button.active {
    background: #3b82f6;
    border-color: #3b82f6;
    color: white;
  }

  .table-wrapper {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid #1f2937;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
  }

  thead {
    background: #1f2937;
  }

  th {
    padding: 0.75rem 1rem;
    text-align: left;
    font-weight: 600;
    color: #9ca3af;
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
  }

  th:hover {
    color: #f9fafb;
  }

  td {
    padding: 0.65rem 1rem;
    border-top: 1px solid #1f2937;
  }

  tr:hover td {
    background: #1f2937;
  }

  .pts {
    font-weight: 700;
    color: #34d399;
  }

  .pos-badge {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
  }

  input {
    width: 100%;
    padding: 0.6rem 1rem;
    margin-bottom: 1rem;
    border-radius: 8px;
    border: 1px solid #374151;
    background: #f9fafb;
    color: #1f2937;
    font-size: 0.9rem;
    outline: none;
  }

  input:focus {
    border-color: #3b82f6;
  }

  .pos-badge.QB  { background: #2d0a1e; color: #fc2b6d; }
  .pos-badge.RB  { background: #0a2420; color: #20ceb8; }
  .pos-badge.WR  { background: #0f1f35; color: #59a7ff; }
  .pos-badge.TE  { background: #2d1a08; color: #feae58; }
  .pos-badge.K   { background: #1e0a2d; color: #c96cff; }
  .pos-badge.DEF { background: #2d1508; color: #bf5f40; }
</style>