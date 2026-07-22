# PLOT UI Redesign Roadmap

This document records the agreed PLOT redesign so each structural change can be
reviewed independently without losing the overall direction.

## Completed foundation

- Replace absolute positioning with nested Qt layouts and splitters.
- Support resizing, maximizing, and a stable `1300 x 900` minimum window.
- Apply the shared ErgoTools palette, typography, controls, tooltips, and icons.
- Normalize the PLOT tool and filter icons into `assets/ui-icons`.
- Enlarge the main toolbar icons while locking its existing header geometry.
- Make Clear Filters and Apply Filters visually prominent.
- Convert the map tool rail to consistent square controls distributed vertically.
- Replace the Tool combo with a persistent LiFFT, DUET, and Shoulder selector.
- Make worker demographics a real collapsible section.
- Remove the unused Other Options controls.
- Enlarge and strengthen the main risk gauge without increasing its card.
- Stack Tool, Workplace, and Worker demographics as full-width filter rows.
- Replace the chained workplace combos with a collapsed hierarchy selector.
- Restyle the map action rail as a fused navy toolbar with square controls.

## Filter redesign

- Replace the separate Plant, Section, Line, Station, and Shift selectors with a
  workplace hierarchy selector that makes the filtering relationship explicit.
- Replace the Tool combo box with a persistent visual tool selector using the
  LiFFT, DUET, and Shoulder Tool icons.
- Make demographic worker filters collapsible and keep their enabled state clear.
- Remove the unused Other Options group.
- Preserve Clear Filters and Apply Filters as the primary filter actions.

## Summary and worker panel

- Convert the current right-side Summary group into Summary and Worker tabs.
- Keep aggregate charts and metrics in Summary by default.
- Move the current lower Worker controls into the Worker tab.
- Separate worker selection, identity, placement, visibility, enabled state,
  locking, navigation, scale, and persistence into clear control groups.
- Open the existing styled worker-search dialog from the Worker tab.
- Keep selection feedback for the worker marker on the plant map.

## Outcome and lower map area

- Replace the outcome color square with the shared animated risk gauge.
- Calculate the gauge from the average of the currently filtered, visible result set.
- Include the risk range legend and retain the current PLOT highlights.
- Widen Outcome by using space released when Worker moves to the right panel.
- Use the remaining lower map area for additional layout-specific summaries.

## Verification states

- Default, minimum, maximized, and intermediate window sizes.
- Empty and populated projects.
- Filters collapsed and expanded.
- Summary and Worker tabs.
- Worker selected, hidden, disabled, locked, moved, and saved.
- Each tool selection and each risk range.
