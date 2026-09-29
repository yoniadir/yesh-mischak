# Liquid Glass header — design

Follow-up to the Apple HIG redesign. Sources read before designing:
[Materials](https://developer.apple.com/design/human-interface-guidelines/materials) and
[Adopting Liquid Glass](https://developer.apple.com/documentation/technologyoverviews/adopting-liquid-glass).

## Rules taken from Apple's guidance

- Liquid Glass is the **functional layer** (navigation and controls) floating above content.
  It is not used in the content layer: cards, lists and the calendar stay solid.
- Use it **sparingly**, only on the most important functional elements.
- Use the **regular** variant (blur + luminosity) since the controls carry text and content scrolls beneath.
  The clear variant is for media backgrounds; this page has none.
- Do not layer glass on glass.
- Keep content legible where it scrolls beneath controls (scroll edge effect).
- Adapt to Reduced Transparency, Increased Contrast and Reduced Motion.

## Decisions

- The full-width translucent bar becomes two separate floating capsules (title, language
  control) that do not overlap. Only these two elements use glass.
- The selected language segment is a plain highlight inside the glass, not a second glass layer.
- Calendar chevrons and "Today" stay flat: they sit inside an opaque card, so glass would have
  nothing to show through and would add glass for its own sake.
- Scroll edge effect: a `::before` veil on the sticky bar (soft blur + fade, masked to nothing at
  its lower edge) keeps content sliding under the capsules legible.
- Web approximation: `backdrop-filter: blur(16px) saturate(180%)`, translucent tint, an inner
  specular edge (light top/leading, dim bottom/trailing) and a soft drop shadow. No SVG
  refraction filter (Chromium-only).
- Fallbacks: no `backdrop-filter` support → near-opaque tint; `prefers-reduced-transparency` →
  near-opaque, no blur, no veil; `prefers-contrast: more` → solid surface with a 1px label
  outline; `forced-colors` → Canvas with a CanvasText border; reduced motion → existing global
  transition removal.
- Sizes: capsules are 44px tall; the title is `.9375rem` with 14px padding so both languages fit
  at 375px without truncation.
