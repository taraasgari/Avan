# AVAN Architecture Blueprint

## Product definition
AVAN is a fashion e-commerce platform centered on AVAN-manufactured garments, customization, limited drops, lightweight creator discovery, rewards, and later AI assistance.

## Product priority
Shopping remains the primary goal. Social and gamification should increase discovery and conversion, not maximize time-on-site.

## Planned capabilities
- Storefront, categories, variants (size/color), inventory
- Highly visual product pages
- Drops / limited collections
- Saved designs and remix
- AI-assisted design generation/editing later
- Lightweight public creator profiles and design discovery
- Outfit Builder
- Size Passport (private)
- Challenges and reward points/coupons
- In-site notifications, later web/mobile push
- PWA first; native app can later consume the same APIs

## Reliability boundary
Core commerce is Tier 0 and must degrade independently of optional capabilities.

### Tier 0 — required
- Product/catalog
- Variants and stock
- Cart
- Checkout
- Payment state
- Orders
- Account authentication needed for purchases

### Tier 1 — non-blocking
- Notifications
- Rewards
- Wishlist
- Drops
- Size Passport

### Tier 2 — optional experience
- Social/creator layer
- Challenges
- Outfit Builder
- AI
- External analytics

## Connectivity / internet-disruption policy
- Critical frontend assets are self-hosted.
- No runtime dependency on Google Fonts, jsDelivr, unpkg, cdnjs, Cloudinary, etc. for core UX.
- Production hosting and DNS must be selected so target customers can still reach the origin in the intended domestic-network outage scenario.
- Third-party failures must degrade gracefully.
- Offline/PWA cache may provide shell/content continuity but never fabricate successful orders or stale stock/payment confirmation.

## API direction
Domain logic lives server-side. Web templates/PWA and future Android/iOS clients should consume stable domain services/API endpoints rather than duplicate commerce logic.
