<script>
  import Modal from '../modal/Modal.svelte'

  export let players = []

  const POSITIONS = ['ALL', 'QB', 'RB', 'WR', 'TE', 'K', 'DEF']
  const PLACEHOLDER = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='38' height='38' 
  viewBox='0 0 38 38'%3E%3Ccircle cx='19' cy='19' r='19' fill='%23ffffff'/%3E%3Ccircle cx='19' cy='15' r='7' 
  fill='%239ca3af'/%3E%3Cellipse cx='19' cy='32' rx='12' ry='8' fill='%239ca3af'/%3E%3C/svg%3E`

  let selectedPosition = 'ALL'
  let sortColumn = 'projected_points'
  let sortAsc = false
  let searchQuery = ''
  let selectedPlayer = null
  let visibleCount = 50

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

  $: paginated = sorted.slice(0, visibleCount)

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
        <th on:click={() => handleSort('estimated_adp')}>Est. ADP {sortIcon('estimated_adp')}</th>
      </tr>
    </thead>
    <tbody>
    {#each paginated as player}
      <tr on:click={() => selectedPlayer = player} style="cursor:pointer">
        <td>
          <div class="player-cell">
            {#if player.position === 'DEF'}
              {#key player.player_id}
              <img 
                src={`https://sleepercdn.com/images/team_logos/nfl/${player.team?.toLowerCase()}.png`}
                alt={player.team}
                class="player-avatar"
                loading="lazy"
                on:error={(e) => { e.currentTarget.setAttribute('src', PLACEHOLDER) }}
              />
              {/key}
            {:else}
              {#key player.player_id}
              <img 
                src={`https://sleepercdn.com/content/nfl/players/thumb/${player.player_id}.jpg`}
                alt={player.name}
                class="player-avatar"
                loading="lazy"
                on:error={(e) => { e.currentTarget.setAttribute('src', PLACEHOLDER) }}
              />
              {/key}
            {/if}
            {player.name}
          </div>
        </td>
        <td><span class="pos-badge {player.position}">{player.position}</span></td>
        <td>{player.team ?? '—'}</td>
        <td>{player.age ?? '—'}</td>
        <td class="pts">
          {player.projected_points}
          {#if player.tag === 'sleeper'}
            <span class="tag sleeper">BOOM</span>
          {:else if player.tag === 'bust'}
            <span class="tag bust">BUST</span>
          {/if}
        </td>
        <td>{player.estimated_adp ?? '—'}</td>
      </tr>
    {/each}
  </tbody>
  </table>
    {#if visibleCount < sorted.length}
      <button on:click={() => visibleCount += 50} class="load-more">
        Load more
      </button>
    {/if}
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
    background: #ebebeb;
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

  .player-cell {
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }

.player-avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    object-fit: cover;
    background: #FFFFFF;
  }

  .load-more {
    width: 100%;
    margin-top: 1rem;
    padding: 0.6rem;
    background: #1f2937;
    border: 1px solid #374151;
    color: #9ca3af;
    border-radius: 8px;
    cursor: pointer;
  }

  .load-more:hover {
    background: #374151;
    color: #f9fafb;
  }

.pts-cell {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.tag {
  font-size: 0.6rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.05em;
  margin-left: 0.4rem;
  vertical-align: middle;
}

.tag.sleeper {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
  border: 1px solid #34d399;
}

.tag.bust {
  background: rgba(248, 113, 113, 0.15);
  color: #f87171;
  border: 1px solid #f87171;
}

  .pos-badge.QB  { background: #2d0a1e; color: #fc2b6d; }
  .pos-badge.RB  { background: #0a2420; color: #20ceb8; }
  .pos-badge.WR  { background: #0f1f35; color: #59a7ff; }
  .pos-badge.TE  { background: #2d1a08; color: #feae58; }
  .pos-badge.K   { background: #1e0a2d; color: #c96cff; }
  .pos-badge.DEF { background: #2d1508; color: #bf5f40; }
</style>