<script lang="ts">
	import type { Snippet } from 'svelte';
	import Seo from './Seo.svelte';
	import { SITE_NAME, absoluteUrl } from '#lib/site.ts';

	interface Props {
		title: string;
		description: string;
		path: string;
		lede: string;
		children: Snippet;
	}

	let { title, description, path, lede, children }: Props = $props();

	const schema = $derived({
		'@context': 'https://schema.org',
		'@type': 'Article',
		headline: title,
		description,
		mainEntityOfPage: absoluteUrl(path),
		publisher: { '@type': 'Organization', name: SITE_NAME, url: absoluteUrl('/') }
	});
</script>

<Seo {title} {description} {path} {schema} />

<article class="wrap guide">
	<header>
		<h1>{title}</h1>
		<p class="lede">{lede}</p>
	</header>
	<div class="prose">
		{@render children()}
	</div>
	<aside class="try">
		<h2>Try it with a song you know</h2>
		<p>Upload a song and get its tune in tonic solfa, with the key under every syllable. Free.</p>
		<a class="button" href="/">Choose a song</a>
	</aside>
</article>

<style>
	.guide {
		padding-top: var(--space-7);
	}

	header {
		max-width: 48rem;
		margin-bottom: var(--space-6);
	}

	.lede {
		font-size: var(--step-1);
		color: var(--slate);
	}

	.prose {
		max-width: 44rem;
	}

	.prose :global(table) {
		border-collapse: collapse;
		margin: var(--space-4) 0 var(--space-5);
		font-variant-numeric: tabular-nums;
		width: 100%;
		max-width: 40rem;
	}

	.prose :global(th),
	.prose :global(td) {
		text-align: left;
		padding: var(--space-2) var(--space-3);
		border-bottom: 1px solid var(--rule);
	}

	.prose :global(th) {
		font-family: var(--font-display);
	}

	.prose :global(.table-scroll) {
		overflow-x: auto;
	}

	.try {
		margin-top: var(--space-8);
		padding: var(--space-6);
		border-radius: var(--radius-panel);
		background: var(--indigo-soft);
		max-width: 44rem;
	}

	.try h2 {
		font-size: var(--step-2);
	}
</style>
