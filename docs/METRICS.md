# Metrics

## Known plays

Sum of `playCount` in the best available all-record payload. This is **not claimed to equal lifetime plays** unless the upstream provider explicitly guarantees that scope.

## Repeat Index

Share of known plays accounted for by the top 10% of observed songs.

Higher = observed listening is more concentrated. It is not a psychological trait.

## Artist Loyalty

Share of known plays accounted for by the top 10% of observed artists. Multi-artist song plays are divided evenly across credited artists.

## Taste Diversity

Effective number of artists: `exp(Shannon entropy)` over the observed artist play distribution.

## Exploration Proxy

Among recent songs available from the provider, the fraction whose historical observed play count is at most 2.

This is a proxy, not a full novelty score.

## Hidden Favorites

High-play songs absent from current `likedSongIds`. The label is deliberately soft: absence from liked ids does not prove dislike, and high play counts do not prove preference.

## Coverage

Fraction of a predefined V1 capability set successfully observed in the current snapshot. Coverage measures data availability, not data quality or lifetime completeness.
