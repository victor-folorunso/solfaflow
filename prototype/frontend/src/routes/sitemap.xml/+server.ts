import { PUBLIC_PAGES, absoluteUrl } from '#lib/site.ts';

export const prerender = true;

export function GET(): Response {
	const urls = PUBLIC_PAGES.map((page) => `  <url><loc>${absoluteUrl(page.path)}</loc></url>`).join('\n');
	const body = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>
`;
	return new Response(body, { headers: { 'Content-Type': 'application/xml' } });
}
