// Minimal typings for the parts of harfbuzzjs used by lib/og/shapeText.ts (the package ships none).
declare module "harfbuzzjs" {
  type Destroyable = { destroy(): void };

  type HbBlob = Destroyable;
  type HbFace = Destroyable & { upem: number };
  type HbFont = Destroyable & { glyphToPath(glyphId: number): string };
  type HbGlyph = { g: number; cl: number; ax: number; ay: number; dx: number; dy: number };
  type HbBuffer = Destroyable & {
    addText(text: string): void;
    guessSegmentProperties(): void;
    json(): HbGlyph[];
  };

  type HarfBuzz = {
    createBlob(data: ArrayBuffer | Uint8Array): HbBlob;
    createFace(blob: HbBlob, index: number): HbFace;
    createFont(face: HbFace): HbFont;
    createBuffer(): HbBuffer;
    shape(font: HbFont, buffer: HbBuffer, features?: string): void;
  };

  const harfbuzz: Promise<HarfBuzz>;
  export default harfbuzz;
}
