# Font subset sources

Readex Pro subsets were copied from the existing local landing build:

- `ReadexPro-Arabic.woff2`: `frontend/landing/.next/static/media/52acd2ded95ac6cd-s.p.1ybfybs3k8tn2.woff2`
- `ReadexPro-Latin.woff2`: `frontend/landing/.next/static/media/890431f0a0104557-s.p.3pc31ksexexjr.woff2`

Font identity and Unicode ranges were read from `frontend/landing/.next/static/chunks/13uv1omxfhu_2.css`. The landing declares Readex through `next/font/google` in `frontend/landing/src/lib/fonts.ts`. IBM Plex and Tajawal are embedded from existing repository assets by the builder.
