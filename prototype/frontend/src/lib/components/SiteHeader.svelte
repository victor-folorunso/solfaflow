<script lang="ts">
	import { page } from '$app/state';
	import logo from '#lib/assets/favicon.svg';

	const links = [
		{ href: '/how-to-read-tonic-solfa-on-keyboard', label: 'Reading solfa' },
		{ href: '/songs', label: 'Your songs' }
	];
</script>

<header>
	<div class="wrap bar">
		<a class="brand" href="/">
			<img src={logo} alt="" width="28" height="28" />
			<span>SolfaFlow</span>
		</a>
		<nav aria-label="Main">
			{#each links as link (link.href)}
				<a href={link.href} aria-current={page.url.pathname.startsWith(link.href) ? 'page' : undefined}>
					{link.label}
				</a>
			{/each}
		</nav>
	</div>
</header>

<style>
	header {
		border-bottom: 1px solid var(--rule);
		background: var(--paper);
	}

	.bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-4);
		min-height: 64px;
	}

	.brand {
		display: inline-flex;
		align-items: center;
		gap: var(--space-2);
		font-family: var(--font-display);
		font-weight: 750;
		font-size: var(--step-1);
		letter-spacing: -0.02em;
		text-decoration: none;
	}

	nav {
		display: flex;
		gap: var(--space-5);
		font-weight: 600;
	}

	nav a {
		text-decoration: none;
		padding: var(--space-2) 0;
		border-bottom: 2px solid transparent;
	}

	nav a[aria-current='page'] {
		border-bottom-color: var(--ink);
	}

	@media (max-width: 30rem) {
		.brand span {
			display: none;
		}
	}
</style>
