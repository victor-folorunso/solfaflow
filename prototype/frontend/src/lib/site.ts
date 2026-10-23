// Placeholder until the real domain is chosen; every canonical URL, the sitemap and
// link previews are built from this one value.
export const SITE_URL = 'https://solfaflow.com';
export const SITE_NAME = 'SolfaFlow';
export const SITE_DESCRIPTION =
	'Upload a song and get its tune in tonic solfa, with the keyboard key under every note and the solfa lighting up as the song plays. Free.';

export function absoluteUrl(path: string): string {
	return SITE_URL + (path === '/' ? '' : path);
}

/** Public pages, for the sitemap and footer. Song pages are private and never listed. */
export const PUBLIC_PAGES = [
	{ path: '/', title: 'Turn any song into tonic solfa for keyboard' },
	{ path: '/how-to-read-tonic-solfa-on-keyboard', title: 'How to read tonic solfa on the keyboard' },
	{ path: '/audio-to-tonic-solfa', title: 'Audio to tonic solfa' },
	{ path: '/audio-to-midi-or-tonic-solfa', title: 'Audio to MIDI, or tonic solfa?' },
	{ path: '/solfege-and-tonic-solfa', title: 'Solfège and tonic solfa' }
] as const;
