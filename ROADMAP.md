# Research roadmap

The project now has a reproducible baseline across behavior, lyrics, latent text structure, playlists and daily aggregate history.

## P1 — validated next additions

### Multilingual semantic embeddings

Run as a manual/deep workflow, not every Page build. Candidate outputs:

- multilingual sentence/document embeddings;
- BERTopic or density-based semantic topics;
- long-term vs recent centroid drift;
- topic stability across resampling / random seeds;
- cross-check against current NMF/LSA results.

The lexical baseline remains available even if a model download fails.

### Lyric affect

Add valence/arousal/dominance or emotion-content estimates only with a validated multilingual model/lexicon. Public wording must remain:

> emotional content in listened lyrics

not:

> the listener's emotional state.

### Reception / comments

Treat comments as a **separate corpus**. They describe how other listeners interpret songs, not the account owner's traits.

Potential metric: lyric-topic vs comment-topic divergence.

## P2 — longitudinal inference

Once `history.json` contains enough distinct days:

- rolling concentration/diversity;
- topic prevalence drift;
- lexical/semantic centroid movement;
- change-point detection;
- persistence vs temporary bursts.

No historical event should be reconstructed for periods ne-listen did not actually observe.

## P3 — multimodal music features

If a lawful, stable metadata/audio-feature source is available, fuse text with acoustic descriptors such as tempo, energy, valence proxies, key/mode and timbral embeddings.

Keep modality-specific outputs visible so audio and lyric signals are not collapsed into one opaque score.
