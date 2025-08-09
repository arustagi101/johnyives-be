from __future__ import annotations

from app.models.agents import StyleSystem


STYLE_GUIDE = """
Criteria only
1. Navigation
Criteria:
Full-width container with logo on the left.


Top-level navigation: 3–6 clearly labeled items (center or right aligned) 



2. Hero Section
Criteria:
Headline
Specific & benefit-driven (states what and why it matters).


Aligned to audience needs.



Large font, high contrast, above the fold.


Body Copy
Expands on “what” with a quick “how” or “why it’s different.”


1–3 short sentences; scannable.


Benefit-first for the customer.


CTA (Call to Action)
One primary CTA in hero (secondary optional).


Action-oriented (“Start Free Trial,” “Get a Demo”).


High visual contrast.


Low friction; clear next step.


Visual/Image
Shows real product, result, or use case (no generic stock art).


Supports headline’s promise.


Retina-quality, fast-loading.


Composition guides eye to headline or CTA.


Mobile-friendly layout (image may stack).



3. Proof Section
Criteria:
Use recognizable, relevant logos.


Display in a clean, uniform style (color or monochrome).



4. Content/Feature Sections


Criteria:
Copy Structure
Headline: Short, direct, benefit-focused (e.g., “Build AI apps in minutes”).


Body Copy: 1–3 sentences max; user pain points + solution.


Visual Guidelines
Headline → short paragraph → relevant visual.


Use screenshots, icons, short animations, or diagrams.


Images should show the product in use.


Consistent text/image placement; balanced alternating layouts.


Ample whitespace for readability.



5. Responsiveness (Mobile, Tablet, Web)
Layout & Structure
Fluid grid system (%/relative units).


Priority content visible without scroll.


Logical stacking on mobile.


Adaptive navigation: horizontal on desktop, hamburger on mobile.


Typography & Readability
Scalable text (em/rem units).


Line length: 45–75 characters desktop, shorter mobile.


Line spacing: 1.4–1.6 (body), tighter for headings.


No text overlaps.


Images & Media
Responsive sizes (srcset), maintain aspect ratio.


Tap targets ≥44px.


Optimized for speed.


Interaction & Controls
Touch-friendly buttons; no hover-only interactions.


Mobile-optimized form inputs.


Optional sticky mobile CTA.


Performance
Load time <3s on 4G.


Minimal layout shift (CLS).


Lazy load media.


Accessibility
WCAG AA contrast.


Alt text for images.


Logical keyboard navigation.



6. Typography Guidelines/ Visual design guidelines

1. Layout & Structure
Hierarchy: Arrange elements in order of importance (headline → key benefit → CTA → supporting content).
Above-the-fold clarity: Users should understand what you offer without scrolling.
Whitespace: Give breathing room around sections and between elements to reduce cognitive load.
Consistent grid system: Align content and components to a baseline grid for balance.

2. Typography
Clear hierarchy: Use distinct styles for headings, subheadings, and body text.
Readable line length: ~50–75 characters for desktop, 35–50 for mobile.
Font pairing: Use no more than two typefaces (e.g., one for headings, one for body).
Contrast: Text should meet WCAG accessibility contrast standards.

3. Color & Contrast
Brand palette: Use 2–4 primary colors consistently.

CTA emphasis: Make the primary button a contrasting, standout color.

Background & text contrast: Ensure legibility under all conditions (light/dark mode, sunlight).

Color psychology: Align colors with desired emotional tone (e.g., blue = trust, red = urgency).

4. Imagery & Media
High-quality visuals: Crisp, optimized images and videos (no pixelation).

Relevance: Visuals should illustrate the product, service, or user outcome.

Human faces: Increase trust and emotional connection.

Performance: Compress assets to keep load time under 2 seconds.

5. Call-to-Action (CTA)
Above-the-fold placement: Have at least one primary CTA visible without scrolling.

Visual hierarchy: Use size, color, and whitespace to make CTAs stand out.

Consistent style: All CTAs should look clickable and align with brand style.

Repetition: Repeat CTAs after major sections for easier action-taking.

6. Responsiveness
Mobile-first: Design for small screens first, then scale up.

Touch targets: Minimum 44px tap area for buttons and links.

Content stacking: Ensure logical order when stacked vertically.

Load optimization: Minimize mobile load time by lazy-loading media.

7. Visual Consistency
Iconography: Use a consistent style set (line, filled, or duotone—never mixed arbitrarily).

Spacing system: Consistent padding/margin increments (e.g., multiples of 8px).

Alignment: Keep elements aligned to a visual rhythm; avoid random placement.

Brand voice: Design elements should match the brand’s tone (playful, minimal, luxury, etc.).

8. Accessibility
Keyboard navigation: All interactive elements should be focusable and navigable.

Alt text: All visuals must have descriptive alt text.

Readable fonts: Avoid overly decorative fonts for body text.

Motion sensitivity: Avoid excessive animations; provide reduced-motion options.


Typography

Typography
Web
Body text: 16–20px.


H1: 32–56px; H2: 24–32px.


Line length: 45–75 chars.


Max 1–2 typefaces.


Consistent hierarchy and spacing.


Mobile
Body: 14–16px; H1: 24–36px; H2: 18–24px.


Line height: 1.5–1.7 (body).


Touch targets: ≥16px padding.


No text cutoffs or awkward wraps.



Archived
UX Evaluation Criteria

1. Navigation
Current Issue:
Logo is not left-aligned.


Improvement:
Align logo to the left.


Criteria:
Full-width container with logo on the left.


Top-level navigation: 3–6 clearly labeled items (center or right aligned) 



2. Hero Section
Current Issue:
Headline is clear, but no visual or interaction shows what Freestyle does.


Improvements:
Add an explainer animation (code snippet → deploy → live app in under 10 seconds).


Add body copy (e.g., “Deploy AI-built apps in seconds”).


Add a primary CTA.


Criteria:
Headline
Specific & benefit-driven (states what and why it matters).


Aligned to audience needs.



Large font, high contrast, above the fold.


Body Copy
Expands on “what” with a quick “how” or “why it’s different.”


1–3 short sentences; scannable.


Benefit-first for the customer.


CTA (Call to Action)
One primary CTA in hero (secondary optional).


Action-oriented (“Start Free Trial,” “Get a Demo”).


High visual contrast.


Low friction; clear next step.


Visual/Image
Shows real product, result, or use case (no generic stock art).


Supports headline’s promise.


Retina-quality, fast-loading.


Composition guides eye to headline or CTA.


Mobile-friendly layout (image may stack).



3. Proof Section
Purpose: Build trust with brand authority.
Criteria:
Use recognizable, relevant logos.


Display in a clean, uniform style (color or monochrome).


Current Issue:
Logo overload; visually heavy and repetitive.


Improvements:


Remove the “hosting production sites” section.



4. Content/Feature Sections
Current Issue:
No clear 3-step onboarding visual; users must infer workflow.


Improvements:
Add clear value props with headline, body copy, and visual for each section.


Criteria:
Copy Structure
Headline: Short, direct, benefit-focused (e.g., “Build AI apps in minutes”).


Body Copy: 1–3 sentences max; user pain points + solution.


Visual Guidelines
Headline → short paragraph → relevant visual.


Use screenshots, icons, short animations, or diagrams.


Images should show the product in use.


Consistent text/image placement; balanced alternating layouts.


Ample whitespace for readability.



5. Responsiveness (Mobile, Tablet, Web)
Layout & Structure
Fluid grid system (%/relative units).


Priority content visible without scroll.


Logical stacking on mobile.


Adaptive navigation: horizontal on desktop, hamburger on mobile.


Typography & Readability
Scalable text (em/rem units).


Line length: 45–75 characters desktop, shorter mobile.


Line spacing: 1.4–1.6 (body), tighter for headings.


No text overlaps.


Images & Media
Responsive sizes (srcset), maintain aspect ratio.


Tap targets ≥44px.


Optimized for speed.


Interaction & Controls
Touch-friendly buttons; no hover-only interactions.


Mobile-optimized form inputs.


Optional sticky mobile CTA.


Performance
Load time <3s on 4G.


Minimal layout shift (CLS).


Lazy load media.


Accessibility
WCAG AA contrast.


Alt text for images.


Logical keyboard navigation.



6. Typography Guidelines
Web
Body text: 16–20px.


H1: 32–56px; H2: 24–32px.


Line length: 45–75 chars.


Max 1–2 typefaces.


Consistent hierarchy and spacing.


Mobile
Body: 14–16px; H1: 24–36px; H2: 18–24px.


Line height: 1.5–1.7 (body).


Touch targets: ≥16px padding.


No text cutoffs or awkward wraps.
"""


def default_style() -> StyleSystem:
    return StyleSystem(
        layout_paradigm="modern",
        design_tokens={
            "color_primary": "#0ea5e9",
            "color_secondary": "#111827",
            "font_sans": "Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, 'Apple Color Emoji', 'Segoe UI Emoji'",
        },
        components=["Navbar", "Footer", "Hero", "CTASection", "FeatureGrid"],
    )

