import hbPromise from "harfbuzzjs";

// next/og (Satori) has no bidi support and measures Arabic words with their
// unjoined glyph widths, so RTL text comes out in the wrong order with dead
// space after every word. For Arabic we shape with HarfBuzz (the engine browsers
// use) and hand Satori a vector SVG of the finished line instead.

export type ShapedLine = { src: string; width: number; height: number };

const LINE_HEIGHT = 1.3;
// Baseline as a share of the font size; leaves room for Arabic descenders.
const BASELINE = 1;

export async function shapeLine(fontData: Buffer, text: string, fontSize: number, color: string): Promise<ShapedLine> {
  const hb = await hbPromise;
  const blob = hb.createBlob(fontData);
  const face = hb.createFace(blob, 0);
  const font = hb.createFont(face);
  const buffer = hb.createBuffer();

  try {
    buffer.addText(text);
    buffer.guessSegmentProperties();
    hb.shape(font, buffer);

    // Glyphs come back in visual (left-to-right) order with advances in font units.
    const scale = fontSize / face.upem;
    let penX = 0;
    const paths: string[] = [];
    for (const glyph of buffer.json()) {
      const d = font.glyphToPath(glyph.g);
      if (d) {
        const x = ((penX + glyph.dx) * scale).toFixed(2);
        const y = (fontSize * BASELINE - glyph.dy * scale).toFixed(2);
        paths.push(`<path transform="translate(${x} ${y}) scale(${scale.toFixed(5)} ${(-scale).toFixed(5)})" d="${d}"/>`);
      }
      penX += glyph.ax;
    }

    const width = Math.ceil(penX * scale);
    const height = Math.ceil(fontSize * LINE_HEIGHT);
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><g fill="${color}">${paths.join("")}</g></svg>`;

    return { src: `data:image/svg+xml;base64,${Buffer.from(svg).toString("base64")}`, width, height };
  } finally {
    buffer.destroy();
    font.destroy();
    face.destroy();
    blob.destroy();
  }
}
