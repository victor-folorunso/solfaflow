<script lang="ts">
	import { onMount } from 'svelte';
	import { listJobs, type Job } from '#lib/api.ts';
	import Seo from '#lib/components/Seo.svelte';
	import { formatTime } from '#lib/solfa.ts';

	let jobs = $state<Job[] | null>(null);
	let offline = $state(false);

	async function refresh() {
		try {
			jobs = await listJobs();
			offline = false;
		} catch {
			offline = true; // server restarting or unreachable; the next tick retries
		}
	}

	onMount(() => {
		refresh();
		const timer = setInterval(refresh, 2000);
		return () => clearInterval(timer);
	});

	const when = (job: Job) =>
		new Date(job.created * 1000).toLocaleString(undefined, {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});

	function status(job: Job): string {
		if (job.status === 'done') {
			const length = job.audio_seconds ? `${formatTime(job.audio_seconds)} long, ` : '';
			return `Ready. ${length}do = ${job.do ?? '?'}`;
		}
		if (job.status === 'error') return job.error ?? 'Stopped before finishing.';
		if (job.status === 'queued') return `Waiting for ${job.queue_position === 1 ? 'the song ahead' : 'the songs ahead'} to finish`;
		if (job.total_seconds)
			return `Solfa ready up to ${formatTime(job.processed_seconds ?? 0)} of ${formatTime(job.total_seconds)}`;
		return 'Getting started';
	}

	const progress = (job: Job) =>
		job.total_seconds ? Math.round((100 * (job.processed_seconds ?? 0)) / job.total_seconds) : 0;
</script>

<Seo title="Your songs" description="Songs you have turned into tonic solfa." path="/songs" noindex />

<div class="wrap page">
	<div class="top">
		<h1>Your songs</h1>
		<a class="button" href="/">Add a song</a>
	</div>

	{#if offline}
		<p class="notice" role="status">Can't reach the SolfaFlow server. Retrying…</p>
	{/if}

	{#if jobs === null}
		<p class="empty">Loading…</p>
	{:else if jobs.length === 0}
		<p class="empty">No songs yet. <a href="/">Upload one</a> to get its tonic solfa.</p>
	{:else}
		<ul class="list">
			{#each jobs as job (job.id)}
				<li class:failed={job.status === 'error'}>
					<div class="main">
						{#if job.player_ready}
							<a class="name" href="/songs/{job.id}">{job.name}</a>
						{:else}
							<span class="name">{job.name}</span>
						{/if}
						<span class="status">{status(job)}</span>
						{#if job.status === 'running'}
							<div class="bar" role="progressbar" aria-valuenow={progress(job)} aria-valuemin={0} aria-valuemax={100} aria-label="Transcribed so far">
								<i style:width="{progress(job)}%"></i>
							</div>
						{/if}
					</div>
					<time datetime={new Date(job.created * 1000).toISOString()}>{when(job)}</time>
				</li>
			{/each}
		</ul>
	{/if}
</div>

<style>
	.page {
		padding-top: var(--space-7);
	}

	.top {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		justify-content: space-between;
		gap: var(--space-4);
		margin-bottom: var(--space-5);
	}

	.list {
		list-style: none;
		padding: 0;
		margin: 0;
		border-top: 1px solid var(--rule);
	}

	li {
		display: flex;
		gap: var(--space-4);
		justify-content: space-between;
		align-items: flex-start;
		padding: var(--space-4) 0;
		border-bottom: 1px solid var(--rule);
		max-width: none;
	}

	.main {
		display: grid;
		gap: var(--space-1);
		min-width: 0;
		flex: 1;
	}

	.name {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: var(--step-1);
		overflow-wrap: anywhere;
	}

	.status,
	time,
	.empty {
		color: var(--slate);
		font-size: var(--step--1);
	}

	.failed .status {
		color: var(--danger);
	}

	time {
		white-space: nowrap;
	}

	.bar {
		height: 5px;
		max-width: 24rem;
		border-radius: 3px;
		background: var(--rule);
		overflow: hidden;
	}

	.bar i {
		display: block;
		height: 100%;
		background: var(--indigo);
		transition: width 0.4s;
	}

	.notice {
		padding: var(--space-3) var(--space-4);
		border-radius: var(--radius-control);
		background: var(--indigo-soft);
	}
</style>
