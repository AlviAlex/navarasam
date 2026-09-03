---
name: Ventura Aqua Glass
colors:
  surface: '#faf9fe'
  surface-dim: '#dad9df'
  surface-bright: '#faf9fe'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f3f8'
  surface-container: '#eeedf3'
  surface-container-high: '#e9e7ed'
  surface-container-highest: '#e3e2e7'
  on-surface: '#1a1b1f'
  on-surface-variant: '#414755'
  inverse-surface: '#2f3034'
  inverse-on-surface: '#f1f0f5'
  outline: '#717786'
  outline-variant: '#c1c6d7'
  surface-tint: '#005bc1'
  primary: '#0058bc'
  on-primary: '#ffffff'
  primary-container: '#0070eb'
  on-primary-container: '#fefcff'
  inverse-primary: '#adc6ff'
  secondary: '#4c4aca'
  on-secondary: '#ffffff'
  secondary-container: '#6664e4'
  on-secondary-container: '#fffbff'
  tertiary: '#006b27'
  on-tertiary: '#ffffff'
  tertiary-container: '#008733'
  on-tertiary-container: '#f7fff2'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a41'
  on-primary-fixed-variant: '#004493'
  secondary-fixed: '#e2dfff'
  secondary-fixed-dim: '#c2c1ff'
  on-secondary-fixed: '#0c006a'
  on-secondary-fixed-variant: '#3631b4'
  tertiary-fixed: '#72fe88'
  tertiary-fixed-dim: '#53e16f'
  on-tertiary-fixed: '#002107'
  on-tertiary-fixed-variant: '#00531c'
  background: '#faf9fe'
  on-background: '#1a1b1f'
  surface-variant: '#e3e2e7'
typography:
  headline-lg:
    fontFamily: inter
    fontSize: 22px
    fontWeight: '700'
    lineHeight: 28px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: inter
    fontSize: 17px
    fontWeight: '600'
    lineHeight: 22px
    letterSpacing: -0.012em
  headline-sm:
    fontFamily: inter
    fontSize: 15px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: -0.008em
  body-lg:
    fontFamily: inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: -0.005em
  body-md:
    fontFamily: inter
    fontSize: 13.5px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: -0.003em
  body-sm:
    fontFamily: inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0em
  label-md:
    fontFamily: inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: inter
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 12px
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  space-2xs: 2px
  space-xs: 4px
  space-sm: 8px
  space-md: 12px
  space-lg: 16px
  space-xl: 20px
  space-2xl: 24px
  space-3xl: 32px
  sidebar-width-min: 260px
  sidebar-width-default: 320px
  sidebar-width-max: 380px
  titlebar-height: 52px
  composer-min-height: 48px
---

## Brand & Style

This design system delivers a tactile, hyper-refined desktop messaging experience rooted in macOS design principles. The interface bridges the physical and digital through realistic materials: deep optical blur filters, dynamic vibrancy matching desktop wallpapers, translucent surface sheen, and native macOS window physics.

The aesthetic philosophy centers on **Refined Translucent Glassmorphism** mixed with **Apple Human Interface Guidelines (HIG)**:
- **Materials over flat surfaces**: Interfaces are sculpted from layered glass materials with fine hair-thin specular inner borders, transmitting ambient color while preserving legibility.
- **Micro-focused precision**: Crisp typography, pixel-aligned system icons, and tight baseline rhythms create an air of craftsmanship and desktop utility.
- **Distraction-free intimacy**: Redundant chrome, intrusive dialers, and extraneous call controls are stripped away to highlight the core exchange: rich text, media, tapbacks, and live link unfurls.

## Colors

The palette embraces native macOS vibrancy tokens, balancing electric system blues with neutral slate and frosted zinc layers.

### Primary Accents & Gradients
- **iMessage Primary Blue**: `#007AFF` to `#0062D2` vertical gradient (angle 180deg) for active outgoing bubbles, active sidebar selection, and primary action affordances.
- **Bubble Text**: `#FFFFFF` with ultra-sharp rendering on blue backgrounds.

### Neutrals & Surfaces (Light Mode)
- **Window Base / Canvas**: `rgba(246, 246, 246, 0.75)` with `backdrop-filter: blur(40px) saturate(190%)`.
- **Sidebar Background**: `rgba(238, 238, 241, 0.65)` with specular top/right borders.
- **Chat Pane Canvas**: `rgba(255, 255, 255, 0.55)` with diffuse ambient backlight.
- **Incoming Message Bubbles**: `#E9E9EB` (in light mode) and `rgba(255, 255, 255, 0.12)` (in translucent/dark mode), text set to `#000000` / `#F5F5F7`.
- **Hairline Dividers & Inner Borders**: `rgba(0, 0, 0, 0.08)` on light glass; `rgba(255, 255, 255, 0.15)` for light-catching edges.

### Semantic & System Colors
- **Traffic Light Controls**:
  - Close: `#FF5F56` (Border: `#E0443E`)
  - Minimize: `#FFBD2E` (Border: `#DEA123`)
  - Zoom / Fullscreen: `#27C93F` (Border: `#1AAB29`)
- **Tapback Inactive Pill**: `rgba(255, 255, 255, 0.85)` with box-shadow `0 2px 8px rgba(0, 0, 0, 0.12)`.
- **Online / Active Indicator**: `#34C759`.

## Typography

The typography mirrors Apple's San Francisco optical standard through a precision-tuned Inter implementation. It balances compact desktop scale with high readability under varied glass-blur backdrops.

- **Headline Large (`22px`)**: Used sparingly for window header titles or modal sheets.
- **Headline Medium (`17px`)**: Dedicated to the active conversation partner’s title in the center toolbar.
- **Headline Small (`15px`)**: Conversation names within the conversation sidebar.
- **Body Large (`15px`)**: Standard scale for chat bubbles, rich unfurls, and message composer input.
- **Body Medium (`13.5px`)**: Subtitles, conversation snippets, and preview descriptions.
- **Label Small (`10px`–`11px`)**: Timestamps, delivery receipts ("Delivered", "Read 10:42 AM"), and section categorization badges.

## Layout & Spacing

The layout is built around the classic macOS split-view pattern with continuous window vibrancy and safe-insets for native controls.

### Structural Grid & Panes
- **Unified Titlebar (`52px` height)**: Houses window controls at `x: 14px, y: 18px` with 8px gaps between individual traffic light dots. The title area seamlessly merges into the pane backgrounds.
- **Primary Sidebar (260px–380px, default 320px)**: Holds search, filter tokens, pinned contact circles, and the full thread list. Border right is a 1px composite stroke (`rgba(0, 0, 0, 0.08)`).
- **Detail / Chat Stage (Remaining canvas, min-width 480px)**: Anchored chat container. Bubbles have maximum width of `65%` of chat stage width, maintaining ergonomic tracking for long paragraphs.
- **Composer Dock**: Suspended `16px` above the bottom window border, inset `20px` laterally, floating as a pill-shaped translucent sub-panel.

## Elevation & Depth

Visual hierarchy is attained through optical physics, material refraction, and composite ambient shadows rather than stark elevation lifts.

### Material Stack
1. **Desktop Layer**: Base system wallpaper.
2. **Window Base (Material Level 0)**: `backdrop-filter: blur(50px) saturate(210%)` with a `1px` outer hairline `rgba(0, 0, 0, 0.2)` and an inner highlight inset border of `rgba(255, 255, 255, 0.25)`.
3. **Sidebar Recess (Material Level 1)**: Matte translucency (`rgba(240, 240, 243, 0.5)`).
4. **Active Thread & Floating Elements (Material Level 2)**:
   - Floating composer pill: `rgba(255, 255, 255, 0.85)` light blur (`20px`), supported by ambient shadow `0 8px 24px rgba(0, 0, 0, 0.07)`, border `0.5px solid rgba(0, 0, 0, 0.06)`.
   - Tapback overlay bubble: `0 4px 16px rgba(0, 0, 0, 0.12)`, `0 1px 2px rgba(0, 0, 0, 0.08)`.
5. **Contextual Menus & Sheets (Material Level 3)**: Deep acrylic glass `rgba(255, 255, 255, 0.92)` with `0 16px 36px rgba(0, 0, 0, 0.18)`.

## Shapes

Shapes utilize Apple-style continuous curves (squircle curvature) to ensure smooth transitions between borders and contents.

- **Window Chrome**: `12px` to `16px` border-radius with clip-path smoothing.
- **Traffic Light Controls**: Perfect circle `12px × 12px`.
- **Chat Bubbles**:
  - Outgoing / Incoming Single Bubble: `18px` continuous border-radius.
  - Bubble Stacks: Adjacent bubbles within the same minute group contract inner corners to `4px`, retaining `18px` on outer opposite corners.
- **Search Bar & Composer**: Fully continuous pill shape (`9999px`) or `22px` rounded rectangle.
- **Avatars**: Continuous circle or `14px` squircle for group clusters.

## Components

### Message Bubbles
- **Outgoing**: Gradient background linear `#007AFF` to `#0062D2`. Text `#FFFFFF`. Selection text highlight `#B3D7FF`. Padding: `8px 14px`. Tail anchors to bottom right.
- **Incoming**: Background `#E9E9EB`. Text `#000000`. Padding: `8px 14px`. Tail anchors to bottom left.
- **Stacking Behavior**: Gap between same-sender bubbles is `2px`; gap between sender changes is `10px`.

### Tapback Reactions
- Suspended mini-capsule attached to the top-edge corner of the target bubble.
- Contains 6 core glyphs: Heart (Love), Thumbs Up (Like), Thumbs Down (Dislike), HaHa (Laugh), Exclamation (Emphasize), Question (Question).
- Active reaction highlighted with an electric blue border ring and subtle micro-bounce animation.

### Conversation List Item
- Padding: `8px 12px`, corner radius: `10px`.
- **Normal**: Transparent background.
- **Hover**: `rgba(0, 0, 0, 0.04)`.
- **Selected**: Solid `#007AFF` (with text flipping to white and subtext to `rgba(255, 255, 255, 0.8)`).
- Contains: Avatar (`40px`), Contact Name, Timestamp, Snippet, and Unread Count badge (vibrant `#007AFF` pill).

### Rich Link Previews
- Contained card inside message stream, clipping with `14px` radius.
- Top: OpenGraph image thumbnail (`aspect-ratio: 16/9`, cover).
- Bottom: Translucent metadata bar (`rgba(0, 0, 0, 0.03)`), Favicon (`14px`), Site Title in bold `12px`, Article Title in `13px`.

### Message Composer
- Pill container featuring:
  - Left button: Plus icon (`+`) inside a circle for applets/attachments.
  - Center: Multiline text-input (`max-height: 120px`), placeholder "iMessage".
  - Right: Dictation / Send indicator button.
  - Audio and video calling shortcuts are deliberately omitted to preserve one-on-one text focus.