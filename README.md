# ArticleInsights

A data analysis and NLP project exploring ~2,000 Times Network news articles: editorial patterns (author productivity, keyword usage, article length), sentiment, and a full NLP pipeline (entity extraction, automated keyword extraction, summarization, topic modeling, and semantic clustering), with every technique validated against the article dataset's own ground truth (`Keywords`, `Synopsis`) wherever possible.

## Overview

The project scrapes article JSON from Times Network's S3-hosted content store, flattens it into a tabular dataset, and runs two layers of analysis on top:

1. **Descriptive analytics**: who writes the most, what gets tagged, how article length varies by author/keyword.
2. **NLP pipeline**: sentiment scoring, named entity recognition, automated keyword extraction, extractive summarization, topic modeling, and embedding-based clustering, each evaluated where possible against the dataset's real editorial metadata rather than treated as a black box.

All analysis lives in `index.ipynb`; every cell has been executed against the real data, so the notebook's outputs (tables, charts, printed metrics) are genuine results, not placeholders.

## Project Structure

```
ArticleInsights/
├── index.ipynb        # Main analysis notebook (21 cells), the core deliverable
├── new.ipynb           # Alternate/retry-hardened data collection notebook
├── main.py             # FastAPI skeleton for serving article data (work in progress)
├── file.csv            # Scraped dataset: 2000 articles x 7 columns
├── data.json            # Reserved for future use (currently empty)
├── requirements.txt     # Python dependencies + one-time model/data downloads
└── .gitignore           # Excludes virtualenv/ and tnn_lists.json (see Data Notes)
```

## Data

**Source:** Article JSON documents hosted on Times Network's public S3 bucket (`times-network.s3.ap-southeast-1.amazonaws.com/article-content/timesnownews/...`), referenced by a list of ~20,000 article URLs (`tnn_lists.json`, not included in this repo; see below).

**`file.csv`** is the flattened result of scraping the first 2,000 of those URLs, with columns:

| Column | Description |
|---|---|
| `Title` | Article headline |
| `Text` | Full article body (raw scrape includes embedded CMS/HTML markup; see Data Quality Notes) |
| `Synopsis` | Human-written summary/standfirst |
| `Insert Date` | Publish/ingest timestamp |
| `Author` | Byline (single author name) |
| `Keywords` | Human-assigned tags (list) |

**Data collection** happens in two places:
- `index.ipynb`'s first cells: straightforward sequential scrape of 2,000 URLs into `file.csv`.
- `new.ipynb`: a hardened version using a `requests.Session` with `urllib3` retry/backoff (`Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])`) for more resilient large-scale scraping.

**Excluded from the repo** (both gitignored):
- `tnn_lists.json`: the full ~20,000-URL source list, **217 MB**, exceeds GitHub's 100 MB per-file limit.
- `virtualenv/`: local Python environment; regenerate via `requirements.txt` instead of tracking it.

### Data quality notes (discovered during analysis, not assumptions)

- **664 of 2,000 articles (33%) have an empty `Text` field.** All text-dependent analysis operates on the remaining 1,336.
- **Raw `Text` contains embedded CMS/XML markup**, e.g. `<keyword id="..." keywordseo="Bengaluru">Bengaluru</keyword>`, plus `<strong>`, `<div>`, `<br>` tags. Left unstripped, this pollutes topic modeling and keyword extraction with junk tokens (`br`, `keywordseo`, `div`). Fixed in the pipeline with `BeautifulSoup(...).get_text()` before any downstream NLP.
- **Content skews heavily toward lifestyle/astrology content**: the single most common keyword is `astrological predictions` (81 articles), and an unsupervised topic model independently rediscovers the same skew, which cross-validates the finding.

## Analysis Pipeline (`index.ipynb`)

### 1. Descriptive Analytics
- Article count per author (bar chart): 122 unique authors; `TN Lifestyle Desk` is most prolific (318 articles).
- Article count per keyword (heatmap, top 100 of 6,305 unique keywords).
- Average article length by author and by keyword (bar charts / heatmap).
- Author × keyword usage cross-tab (heatmap, top 50 authors x top 50 keywords).

### 2. Sentiment Analysis
- **Method:** [VADER](https://github.com/cjhutto/vaderSentiment) (`vaderSentiment`), lexicon/rule-based, chosen over a transformer model to keep the dependency footprint light while still being well-suited to short-form news text.
- Computes a compound sentiment score per article, aggregated by author (bar chart) and as an overall Positive/Neutral/Negative distribution.
- **Result:** 922 positive, 679 neutral, 399 negative articles; sentiment varies drastically by author (e.g. +0.31 avg to -0.99 avg across the two extremes), suggesting sentiment correlates with an author's beat more than random variation.

### 3. NLP Pipeline
Built as a chained sequence of cells, each adding columns to a shared, HTML-cleaned dataframe:

| Step | Technique / Library | What it does |
|---|---|---|
| HTML/CMS cleaning | `beautifulsoup4`, `lxml` | Strips embedded markup from `Text` before any NLP touches it (see Data Quality Notes) |
| Language detection | `langdetect` | Confirms the corpus is safe for English-only models (1333/1336 articles detected as English) |
| Preprocessing + NER | `spaCy` (`en_core_web_sm`) | Single `nlp.pipe()` pass: tokenization, stopword/punctuation removal, lemmatization, and named entity recognition together for efficiency |
| Entity analysis | spaCy NER output | Frequency chart of top PERSON/ORG/GPE entities across the corpus |
| Keyword extraction | `KeyBERT` (`all-MiniLM-L6-v2`) | Extracts candidate keyphrases per article, **compared directly against the human-assigned `Keywords` field**: 30.5% of articles have at least one exact match, 6.7% mean overlap fraction |
| Summarization | `sumy` (TextRank) | Generates a 2-sentence extractive summary per article, **scored against the human-written `Synopsis`** with `rouge-score` (ROUGE-1 F1 ≈ 0.31, ROUGE-2 ≈ 0.15, ROUGE-L ≈ 0.23) |
| Topic modeling | `scikit-learn` (LDA, `CountVectorizer`) | Discovers 10 latent topics unsupervised; independently surfaces themes (politics, health/AI, banking, astrology, crime, markets) that corroborate the keyword-frequency findings |
| Semantic clustering | `sentence-transformers` (`all-MiniLM-L6-v2`) + `KMeans` + PCA | Embeds articles, clusters into 8 semantically coherent groups (105-277 articles each), visualized via 2D PCA projection, an embedding-based alternative to manual keyword tagging for finding related articles |

### 4. Key Findings Summary
The notebook's final cell consolidates all of the above into a single numbered list of 13 findings, generated from the actual computed values in the earlier cells (not hand-waved), covering data quality, editorial skew, sentiment patterns, and how well each automated NLP technique agrees with the dataset's existing human-generated labels.

## Tech Stack

| Category | Libraries |
|---|---|
| Data handling | `pandas`, `numpy` |
| Visualization | `matplotlib`, `seaborn` |
| Scraping | `requests` |
| API | `fastapi` |
| Sentiment | `vaderSentiment` |
| Text cleaning | `beautifulsoup4`, `lxml` |
| NLP core | `spacy` (+ `en_core_web_sm` model), `nltk` |
| Language ID | `langdetect` |
| Keyword extraction | `keybert` |
| Summarization / scoring | `sumy`, `rouge-score` |
| Topic modeling / clustering | `scikit-learn` |
| Embeddings | `sentence-transformers` (backed by PyTorch) |

## Setup

```bash
python3 -m venv virtualenv
source virtualenv/bin/activate
pip install -r requirements.txt

# one-time model/data downloads (also noted in requirements.txt)
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt_tab'); nltk.download('stopwords')"
```

Then open `index.ipynb` in Jupyter. Note that the scraping cells (first few cells of `index.ipynb` / `new.ipynb`) require `tnn_lists.json`, which isn't included in this repo due to its size; the rest of the notebook runs entirely off the already-scraped `file.csv`.

## API (`main.py`)

A minimal FastAPI skeleton, currently a work in progress:
- `GET /`: health check
- `GET /view`: intended to return raw scraped article data
- `GET /articles-by-each-author`: intended to return per-author article counts (not yet implemented)

Not yet wired to serve any of the notebook's analysis (sentiment, entities, clusters, etc.); a natural next step would be exposing endpoints like `/similar-articles` (nearest-neighbor search over the sentence embeddings) or `/sentiment` (on-demand VADER scoring).

## Known Limitations

- Sentiment analysis uses a lexicon-based model (VADER); no fine-tuned/transformer sentiment model has been evaluated.
- Keyword extraction and summarization are unsupervised/extractive baselines; no supervised model has been trained against the ground-truth `Keywords`/`Synopsis` fields, though the pipeline is structured to make that comparison straightforward to add.
- Analysis is scoped to the first 2,000 scraped articles out of the ~20,000 URLs available in `tnn_lists.json`.
