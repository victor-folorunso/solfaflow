// Music logic for the player: labels, slide cleanup, chords and the sheet layout.
// Pure functions only, so they can be tested and shared by the player and the home-page demo.

export const NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
// Same convention as backend/solfaflow/solfa.py (major, raised chromatics).
export const SYLLABLES = ['do', 'di', 're', 'ri', 'mi', 'fa', 'fi', 'so', 'si', 'la', 'li', 'ti'];
const ROMAN = ['I', 'bII', 'II', 'bIII', 'III', 'IV', '#IV', 'V', 'bVI', 'VI', 'bVII', 'VII']; // as chords.py

export interface Note {
	start: number;
	end: number;
	pitch_midi: number;
	exact_pitch_midi?: number; // older results have no cleanup fields
	tuned_pitch?: number;
}

export interface Chord {
	start: number;
	end: number;
	root: number;
	quality: 'maj' | 'min';
}

export interface KeyCandidate {
	do: string;
	do_pitch_class: number;
	minor: boolean;
	score: number;
}

export interface SolfaResult {
	notes: Note[];
	chords?: Chord[];
	do: string | null;
	do_pitch_class: number | null;
	do_source: string | null;
	minor_by_do?: boolean[];
	key_candidates: KeyCandidate[];
	duration: number;
	processed_seconds?: number;
	complete?: boolean; // absent on results from before progressive processing: finished
	version?: number;
	synth_file?: string;
}

const mod12 = (n: number) => ((n % 12) + 12) % 12;
export const exactPitch = (n: Note) => n.exact_pitch_midi ?? n.pitch_midi;
export const isComplete = (r: SolfaResult) => r.complete !== false;

export function formatTime(seconds: number): string {
	return `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`;
}

/** The do that puts the melody's median note in the unmarked octave (keyboard.home_do_midi). */
export function homeDo(notes: Note[], doPc: number | null): number {
	if (!notes.length || doPc === null) return 60;
	const sorted = notes.map(exactPitch).sort((a, b) => a - b);
	const median = sorted[Math.floor(sorted.length / 2)];
	return median - mod12(median - doPc);
}

/** Semitones to move key names so do lands on C (within half an octave). */
export function transposeShift(doPc: number | null, toC: boolean): number {
	if (!toC || doPc === null) return 0;
	const s = (12 - doPc) % 12;
	return s > 6 ? s - 12 : s;
}

export function keyName(midi: number, shift = 0): string {
	const m = midi + shift;
	return NOTE_NAMES[mod12(m)] + (Math.floor(m / 12) - 1);
}

export function syllable(pitch: number, home: number): { syl: string; mark: string } {
	const rel = pitch - home;
	const octave = Math.floor(rel / 12);
	return { syl: SYLLABLES[mod12(rel)], mark: octave > 0 ? "'".repeat(octave) : ','.repeat(-octave) };
}

// Mirrors clean_slides() in keyboard.py; slides.test.ts checks both agree on real songs.
const MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11];
const SI = 8; // raised so: the leading tone of a la-based minor key
const PASSING_SPAN = 4;
const KEEP_CHROMATIC_SECONDS = 0.6;
const KEEP_CHROMATIC_TOLERANCE = 0.25;

/**
 * Out-of-key notes that come from sliding into a note move to the nearer in-key
 * neighbour; held, squarely sung chromatics are kept; a passing step within a third
 * goes to the neighbour between its two neighbours ("mi ri do" reads "mi re do").
 */
export function cleanSlides(notes: Note[], doPc: number, minor: boolean): number[] {
	const scale = new Set(MAJOR_SCALE.concat(minor ? [SI] : []).map((s) => (doPc + s) % 12));
	const inKey = (p: number) => scale.has(mod12(p));
	const out: number[] = [];
	notes.forEach((n, i) => {
		let p = exactPitch(n);
		if (n.tuned_pitch === undefined) {
			out.push(n.pitch_midi);
			return;
		}
		const held = n.end - n.start >= KEEP_CHROMATIC_SECONDS;
		const centred = Math.abs(n.tuned_pitch - p) <= KEEP_CHROMATIC_TOLERANCE;
		if (!inKey(p) && !(held && centred)) {
			let below = p - 1;
			let above = p + 1;
			while (!inKey(below)) below--;
			while (!inKey(above)) above++;
			let [near, far] = n.tuned_pitch - below <= above - n.tuned_pitch ? [below, above] : [above, below];
			const prev = out.length ? out[out.length - 1] : null;
			const next = i + 1 < notes.length ? exactPitch(notes[i + 1]) : null;
			if (
				prev !== null && next !== null && Math.abs(prev - next) <= PASSING_SPAN &&
				(near === prev || near === next) && Math.min(prev, next) < far && far < Math.max(prev, next)
			)
				near = far;
			p = near;
		}
		out.push(p);
	});
	return out;
}

export function displayPitches(result: SolfaResult, doPc: number | null, exact: boolean): number[] {
	if (exact || doPc === null) return result.notes.map(exactPitch);
	return cleanSlides(result.notes, doPc, result.minor_by_do?.[doPc] ?? false);
}

export function chordName(c: Chord, shift = 0): string {
	return NOTE_NAMES[mod12(c.root + shift)] + (c.quality === 'min' ? 'm' : '');
}

/** The chord relative to do, the way keyboardists say "go to the four chord". */
export function chordNumeral(c: Chord, doPc: number | null): string {
	if (doPc === null) return '';
	const degree = ROMAN[mod12(c.root - doPc)];
	return c.quality === 'min' ? degree.toLowerCase() : degree;
}

export function chordTones(c: Chord): number[] {
	return (c.quality === 'min' ? [0, 3, 7] : [0, 4, 7]).map((i) => mod12(c.root + i));
}

/** Index of the item sounding at time t, or -1. Items are sorted by start. */
export function activeIndex(items: { start: number; end: number }[], t: number): number {
	for (let i = 0; i < items.length; i++) {
		if (items[i].start > t) break;
		if (t < items[i].end) return i;
	}
	return -1;
}

// Sheet layout: phrases (lines) of notes, rests and chords that change where nobody sings.
const PHRASE_GAP_SECONDS = 0.6;
const REST_GAP_SECONDS = 0.25;
const MAX_NOTES_PER_LINE = 18;
const CHORD_ATTACH_SECONDS = 0.4; // a chord this close before a note is written above that note

export type SheetItem =
	| { kind: 'note'; index: number; chordAbove: Chord | null }
	| { kind: 'rest' }
	| { kind: 'chord'; chord: Chord };

export interface Phrase {
	start: number;
	items: SheetItem[];
}

export function layoutSheet(notes: Note[], chords: Chord[]): Phrase[] {
	const phrases: Phrase[] = [];
	let phrase: Phrase | null = null;
	let prevEnd = -1;
	let count = 0;
	let ci = 0;
	const open = (start: number) => {
		phrase = { start, items: [] };
		phrases.push(phrase);
		count = 0;
		return phrase;
	};
	// Chords before the first sung note (an intro) get their own line.
	const introEnd = notes.length ? notes[0].start - CHORD_ATTACH_SECONDS : Infinity;
	if (chords.length && chords[0].start < introEnd) {
		const intro = open(chords[0].start);
		while (ci < chords.length && chords[ci].start < introEnd) intro.items.push({ kind: 'chord', chord: chords[ci++] });
		phrase = null;
	}
	notes.forEach((n, index) => {
		const gap = n.start - prevEnd;
		const fresh = phrase === null || gap > PHRASE_GAP_SECONDS || count >= MAX_NOTES_PER_LINE;
		const line: Phrase = fresh ? open(n.start) : (phrase as unknown as Phrase);
		if (!fresh && gap > REST_GAP_SECONDS) line.items.push({ kind: 'rest' });
		let chordAbove: Chord | null = null;
		while (ci < chords.length && chords[ci].start <= n.start + CHORD_ATTACH_SECONDS) {
			const c = chords[ci++];
			if (n.start - c.start <= CHORD_ATTACH_SECONDS) chordAbove = c;
			else line.items.push({ kind: 'chord', chord: c }); // changed in a gap with no singing
		}
		line.items.push({ kind: 'note', index, chordAbove });
		prevEnd = n.end;
		count++;
	});
	if (ci < chords.length) {
		// Chords after the last sung note: an outro, or singing not transcribed yet.
		const outro: Phrase = (phrase as Phrase | null) ?? open(chords[ci].start);
		while (ci < chords.length) outro.items.push({ kind: 'chord', chord: chords[ci++] });
	}
	return phrases;
}
