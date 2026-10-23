<script lang="ts">
	import '@fontsource-variable/bricolage-grotesque/wdth.css';
	import '@fontsource/atkinson-hyperlegible-next/400.css';
	import '@fontsource/atkinson-hyperlegible-next/700.css';
	import '../app.css';
	import favicon from '#lib/assets/favicon.svg';
	import SiteFooter from '#lib/components/SiteFooter.svelte';
	import SiteHeader from '#lib/components/SiteHeader.svelte';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<meta name="theme-color" content="#1e2350" />
</svelte:head>

<a class="visually-hidden skip" href="#main">Skip to content</a>
<SiteHeader />
<main id="main">
	{@render children()}
</main>
<SiteFooter />

<style>
	.skip:focus {
		position: fixed;
		top: var(--space-2);
		left: var(--space-2);
		width: auto;
		height: auto;
		clip: auto;
		padding: var(--space-2) var(--space-4);
		background: var(--surface);
		z-index: 10;
	}
</style>
