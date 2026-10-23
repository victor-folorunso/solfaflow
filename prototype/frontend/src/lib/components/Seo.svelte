<script lang="ts">
	import { SITE_NAME, absoluteUrl } from '#lib/site.ts';

	interface Props {
		title: string;
		description: string;
		path: string;
		/** Structured data (schema.org JSON-LD) for this page, if any. */
		schema?: object | object[];
		/** Private pages (a user's songs) must never be indexed. */
		noindex?: boolean;
	}

	let { title, description, path, schema, noindex = false }: Props = $props();
	const fullTitle = $derived(path === '/' ? `${SITE_NAME}: ${title}` : `${title} | ${SITE_NAME}`);
	const url = $derived(absoluteUrl(path));
	const jsonLd = $derived(schema ? JSON.stringify(schema).replace(/</g, '\\u003c') : '');
</script>

<svelte:head>
	<title>{fullTitle}</title>
	<meta name="description" content={description} />
	{#if noindex}
		<meta name="robots" content="noindex, nofollow" />
	{:else}
		<link rel="canonical" href={url} />
	{/if}
	<meta property="og:type" content="website" />
	<meta property="og:site_name" content={SITE_NAME} />
	<meta property="og:title" content={fullTitle} />
	<meta property="og:description" content={description} />
	<meta property="og:url" content={url} />
	<meta property="og:image" content={absoluteUrl('/og-image.png')} />
	<meta name="twitter:card" content="summary_large_image" />
	{#if jsonLd}
		{@html `<script type="application/ld+json">${jsonLd}</` + 'script>'}
	{/if}
</svelte:head>
