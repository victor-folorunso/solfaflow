<script lang="ts">
	import { PUBLIC_PAGES } from '#lib/site.ts';

	const guides = PUBLIC_PAGES.filter((p) => p.path !== '/');
</script>

<footer>
	<div class="wrap grid">
		<div>
			<p class="name">SolfaFlow</p>
			<p class="note">
				Free. Transcription is automatic, so some notes will be wrong. Check by ear and change the key
				if it sounds off.
			</p>
		</div>
		<nav aria-label="Guides">
			<p class="heading">Guides</p>
			<ul>
				{#each guides as guide (guide.path)}
					<li><a href={guide.path}>{guide.title}</a></li>
				{/each}
			</ul>
		</nav>
	</div>
</footer>

<style>
	footer {
		margin-top: var(--space-8);
		padding: var(--space-7) 0 var(--space-6);
		border-top: 1px solid var(--rule);
		color: var(--slate);
		font-size: var(--step--1);
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
		gap: var(--space-6);
	}

	.name,
	.heading {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: var(--step-0);
		color: var(--ink);
		margin-bottom: var(--space-2);
	}

	.note {
		max-width: 36ch;
	}

	ul {
		list-style: none;
		padding: 0;
		margin: 0;
		display: grid;
		gap: var(--space-2);
	}
</style>
