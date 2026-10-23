<script lang="ts">
	import Demo from '#lib/components/Demo.svelte';
	import Seo from '#lib/components/Seo.svelte';
	import UploadBox from '#lib/components/UploadBox.svelte';
	import { FAQ } from '#lib/faq.ts';
	import { PUBLIC_PAGES, SITE_DESCRIPTION, SITE_NAME, SITE_URL } from '#lib/site.ts';

	const schema = [
		{
			'@context': 'https://schema.org',
			'@type': 'WebApplication',
			name: SITE_NAME,
			url: SITE_URL,
			description: SITE_DESCRIPTION,
			applicationCategory: 'MultimediaApplication',
			operatingSystem: 'Any (runs in the browser)',
			offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' }
		},
		{
			'@context': 'https://schema.org',
			'@type': 'FAQPage',
			mainEntity: FAQ.map(({ q, a }) => ({
				'@type': 'Question',
				name: q,
				acceptedAnswer: { '@type': 'Answer', text: a }
			}))
		}
	];
	const guides = PUBLIC_PAGES.filter((p) => p.path !== '/');
</script>

<Seo
	title="Turn any song into tonic solfa for keyboard"
	description={SITE_DESCRIPTION}
	path="/"
	{schema}
/>

<section class="wrap hero">
	<div class="pitch">
		<h1><span>Hear a song.</span> <span>Play it in tonic solfa.</span></h1>
		<p class="lede">
			Upload any song and SolfaFlow writes its tune in tonic solfa, with the keyboard key under
			every syllable and the chords above. Press play and the solfa lights up with the singer.
		</p>
		<UploadBox />
	</div>
	<div class="show">
		<Demo />
	</div>
</section>

<section class="wrap steps" aria-labelledby="how">
	<h2 id="how">How it works</h2>
	<ol>
		<li>
			<h3>Upload a song</h3>
			<p>Any recording with a lead singer: an MP3 from your phone, a voice note, a song you love.</p>
		</li>
		<li>
			<h3>SolfaFlow finds the tune</h3>
			<p>
				It separates the singer from the band, writes down every note they sing, and works out the
				key and the chords.
			</p>
		</li>
		<li>
			<h3>Play along</h3>
			<p>
				The song plays while the current syllable and the key to press light up. Slow it down to
				half speed while you learn.
			</p>
		</li>
	</ol>
</section>

<section class="wrap features" aria-labelledby="keys">
	<h2 id="keys">Made for the keyboard</h2>
	<dl>
		<div>
			<dt>The key under every note</dt>
			<dd>Each syllable shows the exact key to press, so "so" in G is written G4, not left to you.</dd>
		</div>
		<div>
			<dt>Move it to C</dt>
			<dd>One switch shifts the key names so do is C, and most of the tune lands on white keys.</dd>
		</div>
		<div>
			<dt>Chords above the solfa</dt>
			<dd>
				The chord name and its number in the key, like IV or V, appear where the chord changes, for
				your left hand.
			</dd>
		</div>
		<div>
			<dt>Hear what was written</dt>
			<dd>
				Switch from the original song to the detected notes on a piano sound and check the
				transcription by ear.
			</dd>
		</div>
	</dl>
</section>

<section class="wrap faq" aria-labelledby="faq">
	<h2 id="faq">Questions</h2>
	{#each FAQ as item (item.q)}
		<details>
			<summary>{item.q}</summary>
			<p>{item.a}</p>
		</details>
	{/each}
</section>

<section class="wrap guides" aria-labelledby="learn">
	<h2 id="learn">Learn more</h2>
	<ul>
		{#each guides as guide (guide.path)}
			<li><a href={guide.path}>{guide.title}</a></li>
		{/each}
	</ul>
</section>

<style>
	.hero {
		display: grid;
		grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
		gap: var(--space-7);
		align-items: center;
		padding-block: var(--space-7) var(--space-8);
	}

	h1 span {
		display: block; /* one sentence per line, so neither breaks mid-thought */
	}

	.lede {
		font-size: var(--step-1);
		line-height: 1.5;
		color: var(--slate);
		max-width: 40ch;
		margin-bottom: var(--space-6);
	}

	section + section {
		margin-top: var(--space-8);
	}

	.steps ol {
		list-style: none;
		counter-reset: step;
		padding: 0;
		margin: 0;
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr));
		gap: var(--space-6);
	}

	.steps li {
		counter-increment: step;
		border-top: 3px solid var(--indigo);
		padding-top: var(--space-4);
	}

	.steps li::before {
		content: counter(step);
		display: block;
		font-family: var(--font-display);
		font-size: var(--step-3);
		font-weight: 800;
		line-height: 1;
		color: var(--indigo);
		margin-bottom: var(--space-3);
	}

	.steps p {
		color: var(--slate);
	}

	.features dl {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr)); /* four features: two rows of two */
		max-width: 56rem;
		gap: var(--space-6) var(--space-7);
		margin: 0;
	}

	dt {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: var(--step-1);
		margin-bottom: var(--space-2);
	}

	dd {
		margin: 0;
		color: var(--slate);
	}

	.faq details {
		border-bottom: 1px solid var(--rule);
		max-width: 48rem;
	}

	.faq summary {
		cursor: pointer;
		padding: var(--space-4) 0;
		font-weight: 700;
		font-size: var(--step-1);
		font-family: var(--font-display);
	}

	.faq details p {
		color: var(--slate);
		padding-bottom: var(--space-3);
	}

	.guides ul {
		padding-left: 1.25em;
	}

	@media (max-width: 52rem) {
		.features dl {
			grid-template-columns: 1fr;
		}

		.hero {
			grid-template-columns: 1fr;
			gap: var(--space-6);
			padding-top: var(--space-6);
		}
	}
</style>
