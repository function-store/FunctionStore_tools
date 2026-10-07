"""FuzzyMatch -- the tiered matcher behind FNS_CommandPalette, FNS_SearchPalette
and the TDXL launcher's quick launch (the launcher's src/fuzzy.ts mirrors it).

Pure Python, no TouchDesigner imports: tests import it by path, and the
TypeScript port can be checked against it line for line.

A query splits on whitespace into tokens and every token must hit the text
(AND). A token hits at exactly one TIER, the best it can reach:

	0 EXACT        the whole text is the token
	1 PREFIX       the text starts with the token
	2 WORD         a word of the text starts with the token      blur -> hsvBlur
	3 SUBSTRING    the token sits inside the text                lur  -> blur
	4 INITIALS     the token spells the first letters of words   mfo  -> movieFileOut
	5 TYPO         a word, or its prefix, is within a bounded    nosie -> noise
	               Damerau distance: 1 for 4..7 letters, 2 for 8+
	6 SUBSEQUENCE  the token's letters appear in order           fbg  -> feedbackGen

Tiers 0..3 are the strict matches every surface had before this module;
4..6 only ever FILL BELOW them, so nothing that matched before ranks
differently. Typo sits above subsequence on purpose: for a token of four or
more letters, one slip away from a real word ("nosie") is a far stronger
signal than its letters scattered through a longer name ("noiseSimple").

Both sides are FOLDED before comparing: lower case, a few British spellings
to American (randomise/randomize, colour/color), separators dropped, so
"movie_file" and "movieFile" are one string. Words are split on separators
and camelCase humps BEFORE folding, because folding loses the humps.
"""
import re

EXACT, PREFIX, WORD, SUBSTRING, INITIALS, TYPO, SUBSEQUENCE = range(7)
TIER_NAMES = ('exact', 'prefix', 'word', 'substring', 'initials', 'typo', 'subsequence')

# Spelling folds, applied per WORD and anchored at its end. Narrow on
# purpose: a fold changes typo distances, so "ise" only folds after the
# consonants British -ise verbs end in (randomise, realise, recognise,
# quantise), never "noise", "raise" or "wise" -- an unanchored fold turned
# noise into noize and put "nosie" two edits away from it. It still folds
# a few -ise nouns (promise -> promize); harmless, both sides fold alike.
# Capture groups, not lookbehind: the TypeScript mirror runs on
# JavaScriptCore builds without lookbehind, and the two stay identical.
SPELLING = (
	(re.compile(r'([lmnrt])is(e|es|ed|er|ers|ing|ation|ations)$'), r'\1iz\2'),
	(re.compile(r'(l)ys(e|es|ed|er|ers|ing)$'), r'\1yz\2'),
	(re.compile(r'^(.{3,})our(s|ed|ing|ite|ites|ful|less)?$'), r'\1or\2'),
	(re.compile(r'^grey'), 'gray'),
	(re.compile(r'^centre(s)?$'), r'center\1'),
	(re.compile(r'^centred$'), 'centered'),
)
_WORDS = re.compile(r'[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z0-9]+|[A-Z]+|[0-9]+|[^\W_]+')

# Typo tolerance by token length: nothing under four letters (too many
# neighbours), one slip up to seven letters, two from eight.
TYPO_MIN = 4
TYPO_WIDE = 8


def _spell(word):
	for pattern, repl in SPELLING:
		word = pattern.sub(repl, word)
	return word


# A palette re-scores the same catalogue on every keystroke, and splitting
# plus spelling-folding a name is regex work -- measured at a third of the
# CommandPalette's per-keystroke cost over 1554 rows. Both are pure functions
# of the text, so each name is folded once. Bounded by clearing, not LRU: the
# corpora are a few thousand names, so the bound only guards a runaway caller.
_CACHE_MAX = 50000
_words_cache = {}
_fold_cache = {}


def _words(text):
	"""words(text) as a cached tuple -- the hot path's read-only form."""
	key = text or ''
	ws = _words_cache.get(key)
	if ws is None:
		if len(_words_cache) >= _CACHE_MAX:
			_words_cache.clear()
		ws = tuple(_spell(w.lower()) for w in _WORDS.findall(key))
		_words_cache[key] = ws
	return ws


def words(text):
	"""The words of a name, split on separators and camelCase humps, folded.

	hsvBlur -> [hsv, blur]; HSVBlur -> [hsv, blur]; movie_file_in2 -> [movie, file, in2].
	"""
	return list(_words(text))


def fold(text):
	"""Lower case, spelling folds, separators and humps dropped: one string."""
	key = text or ''
	f = _fold_cache.get(key)
	if f is None:
		if len(_fold_cache) >= _CACHE_MAX:
			_fold_cache.clear()
		f = ''.join(_words(key))
		_fold_cache[key] = f
	return f


def damerau(a, b, limit):
	"""Optimal-string-alignment distance between a and b, or None past limit.

	Insert, delete, substitute and adjacent transposition each cost one.
	"""
	if abs(len(a) - len(b)) > limit:
		return None
	if a == b:
		return 0
	la, lb = len(a), len(b)
	prev2 = None
	prev = list(range(lb + 1))
	for i in range(1, la + 1):
		cur = [i] + [0] * lb
		ca = a[i - 1]
		for j in range(1, lb + 1):
			cb = b[j - 1]
			cost = 0 if ca == cb else 1
			d = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
			if i > 1 and j > 1 and ca == b[j - 2] and a[i - 2] == cb:
				d = min(d, prev2[j - 2] + 1)
			cur[j] = d
		if min(cur) > limit:
			return None
		prev2, prev = prev, cur
	return prev[lb] if prev[lb] <= limit else None


def subsequence(tok, text):
	"""Quality in 0..1 when tok is a subsequence of text, else None.

	Rewards a match that starts early and runs contiguously, so "che" prefers
	"checker" over c, h and e scattered through a longer word. This is the
	CommandPalette's original scorer, kept as the lowest tier.
	"""
	if not tok:
		return 0.0
	if not text:
		return None
	qi, runs, run, first = 0, 0, 0, None
	for i, ch in enumerate(text):
		if qi < len(tok) and ch == tok[qi]:
			if first is None:
				first = i
			qi += 1
			run += 1
		elif run:
			runs = max(runs, run)
			run = 0
	if qi < len(tok):
		return None
	runs = max(runs, run)
	contiguity = runs / float(len(tok))
	position = 1.0 - (first / float(len(text))) if first is not None else 0.0
	density = len(tok) / float(len(text))
	return 0.5 * contiguity + 0.3 * position + 0.2 * density


def _typo(tk, ws, tf):
	"""Best quality of a bounded-distance hit against the words, or None.

	Each word is tried whole and cut to the token's length, give or take one,
	so a slip in the first word of a longer name still lands (kinnect ->
	kinectAzure). The joined text is tried too when there are several words,
	for a slip that straddles a hump (opneext -> openExt).
	"""
	n = len(tk)
	if n < TYPO_MIN:
		return None
	limit = 1 if n < TYPO_WIDE else 2
	best = None
	candidates = list(ws)
	if len(ws) > 1:
		candidates.append(tf)
	for i, w in enumerate(candidates):
		forms = {w}
		for cut in (n - 1, n, n + 1):
			if 0 < cut < len(w):
				forms.add(w[:cut])
		for form in forms:
			if len(form) < TYPO_MIN:
				continue
			# Every letter of the token that the form lacks costs an edit of
			# its own (a transposition cannot supply a letter), so more of
			# them than the limit rules the form out without the O(n*m) table.
			missing = 0
			for ch in tk:
				if ch not in form:
					missing += 1
					if missing > limit:
						break
			if missing > limit:
				continue
			d = damerau(tk, form, limit)
			if d is None:
				continue
			# distance first, then an earlier word, then a fuller word
			q = 1.0 - d / float(limit + 1) - 0.05 * min(i, 9) - 0.01 * (len(w) - len(form))
			if best is None or q > best:
				best = q
	return best


def match_token(tok, text, ws=None, strict=False):
	"""(tier, quality) for one token against one text, or None.

	`ws` is words(text) when the caller already has it (a corpus scan reuses
	it per name); quality is 0..1 within the tier, higher is better. `strict`
	stops at SUBSTRING: a caller that would discard a fuzzier hit anyway (a
	path field) must not pay for the typo and subsequence passes.
	"""
	tk = fold(tok)
	if not tk:
		return None
	if ws is None:
		ws = _words(text)
		tf = fold(text)
	else:
		tf = ''.join(ws)
	if not tf:
		return None
	if tf == tk:
		return EXACT, 1.0
	if tf.startswith(tk):
		return PREFIX, len(tk) / float(len(tf))
	for i, w in enumerate(ws):
		if w.startswith(tk):
			return WORD, 0.5 * len(tk) / float(len(w)) + 0.5 * (1.0 - i / float(len(ws)))
	at = tf.find(tk)
	if at >= 0:
		return SUBSTRING, 1.0 - at / float(len(tf))
	if strict:
		return None
	if len(ws) >= 2 and len(tk) >= 2:
		initials = ''.join(w[0] for w in ws)
		if initials.startswith(tk):
			return INITIALS, len(tk) / float(len(initials))
	q = _typo(tk, ws, tf)
	if q is not None:
		return TYPO, q
	q = subsequence(tk, tf)
	if q is not None:
		return SUBSEQUENCE, q
	return None


def tokens(query):
	"""The tokens of a query: whitespace-split, empty after folding dropped."""
	return [t for t in (query or '').split() if fold(t)]


def match(query, text, ws=None):
	"""(tier, quality) for a whole query against one text, or None.

	Every token must hit. The tier is the WORST token's tier (a query is as
	fuzzy as its loosest word). The quality is the mean over tokens of
	(quality - tier), so between two rows on the same worst tier the one
	whose OTHER tokens hit tighter wins, and a token's tier always outweighs
	its within-tier quality: -6..1, higher is better.
	"""
	toks = tokens(query)
	if not toks:
		return EXACT, 0.0
	if ws is None:
		ws = _words(text)
	worst, total = EXACT, 0.0
	for t in toks:
		m = match_token(t, text, ws)
		if m is None:
			return None
		worst = max(worst, m[0])
		total += m[1] - m[0]
	return worst, total / len(toks)


def score_fields(query, fields):
	"""Best (tier, quality) for a query across several fields of one row.

	`fields` is a sequence of (text, penalty, substring_only): the penalty is
	added to the tier so a title hit outranks the same hit in a category
	(0.4) or a path (0.7); substring_only refuses the fuzzy tiers, because a
	subsequence over a long path matches almost anything. Each token takes
	its best field; the row's tier is the worst token's penalised tier and
	the quality the mean of (quality - penalised tier), as in match().
	Returns None when any token misses every field.
	"""
	toks = tokens(query)
	if not toks:
		return EXACT, 0.0
	prepared = [(text, penalty, sub_only) for text, penalty, sub_only in fields if text]
	worst, total = 0.0, 0.0
	for t in toks:
		best = None
		for text, penalty, sub_only in prepared:
			m = match_token(t, text, strict=sub_only)
			if m is None:
				continue
			key = (m[0] + penalty, -m[1])
			if best is None or key < best:
				best = key
		if best is None:
			return None
		worst = max(worst, best[0])
		total += -best[1] - best[0]
	return worst, total / len(toks)


def rank(query, texts, limit=None):
	"""The texts that match, best first, as (tier, quality, text) tuples."""
	hits = []
	for text in texts:
		m = match(query, text)
		if m is not None:
			hits.append((m[0], -m[1], text.lower(), text))
	hits.sort()
	out = [(t, -nq, text) for t, nq, _, text in hits]
	return out if limit is None else out[:limit]
