# RescueRelay pilot and impact measurement plan

The demo proves workflow behavior, not real-world impact. The numbers in the interface are transparent scenario estimates: matched pounds are calculated from allocations, meals use a fixed 0.695 multiplier, and minutes saved use a fixed task estimate. They are not yet field validated.

## Pilot question

Can RescueRelay reduce the time a food-rescue coordinator spends triaging and routing donation offers without increasing corrections, unsafe commitments, or missed pickup windows?

## Four-week pilot

Run with one coordinator and one backup across a participating network of at least three pantries.

1. **Week 1 — baseline:** coordinators process offers normally and record timestamps, corrections, and outcomes.
2. **Week 2 — shadow:** RescueRelay proposes plans, but coordinators continue using the existing process; compare recommendations without operational reliance.
3. **Weeks 3–4 — assisted:** coordinators use RescueRelay for eligible offers, with all external commitments still approval-gated.

Exclude emergency food-safety incidents, offers without a verifiable pickup window, and categories for which pantry handling constraints are not represented.

## Metrics and reversal thresholds

| Measure | Definition | Success signal | Stop / reverse signal |
|---|---|---|---|
| Coordinator handling time | Active minutes from first open to finalized routing plan | Median at least 30% below baseline | No improvement after 20 comparable offers |
| Recommendation correction rate | Plans whose destination, quantity, or time is changed by a coordinator | At most 10% and no worse than baseline | Above 15% or two repeated constraint errors |
| Pickup-window reliability | Approved pickups completed inside the declared window | No worse than baseline | Any statistically credible degradation or two avoidable misses |
| Capacity violations | Approved pounds exceed declared available capacity | Zero | Any violation pauses assisted use |
| Decision precision | Surfaced decisions that coordinators judge genuinely necessary | At least 75% useful | More than 40% marked unnecessary |
| Food routed | Accepted pounds assigned to an eligible pantry | Reported descriptively, not as causal impact | N/A |

## Evidence collection

- Generate a stable source-message ID, run ID, allocation ID, decision record, and final outcome for every offer.
- Record timestamps around coordinator actions without storing unnecessary donor personal data.
- Ask the coordinator for a one-click correction reason and whether each surfaced decision was useful.
- Review mismatches weekly with the participating pantry network.
- Report medians and distributions, not just totals; keep baseline and assisted cohorts visible.

## Evidence that would reverse the product direction

The strongest current hypothesis is that message triage and constraint checking are the bottleneck. If observation shows that vehicle availability, volunteer no-shows, or stale pantry data dominate failure instead, RescueRelay should pivot from inbox automation toward live capacity/transport coordination. Novel agent behavior is not valuable if it automates the wrong bottleneck.
