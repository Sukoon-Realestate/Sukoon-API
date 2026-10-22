// Render machine-authored test text with native shaping (including Arabic).
import AppKit

let text = try String(contentsOfFile: CommandLine.arguments[1], encoding: .utf8)
let output = URL(fileURLWithPath: CommandLine.arguments[2])
let width = 1200, height = 600
let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: width, pixelsHigh: height,
                             bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                             isPlanar: false, colorSpaceName: .deviceRGB,
                             bytesPerRow: 0, bitsPerPixel: 0)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: bitmap)
NSColor.white.setFill()
NSBezierPath(rect: NSRect(x: 0, y: 0, width: width, height: height)).fill()
let paragraph = NSMutableParagraphStyle()
paragraph.alignment = .natural
paragraph.lineBreakMode = .byWordWrapping
(text as NSString).draw(in: NSRect(x: 64, y: 64, width: 1072, height: 472),
                       withAttributes: [.font: NSFont.systemFont(ofSize: 46),
                                        .foregroundColor: NSColor.black,
                                        .paragraphStyle: paragraph])
NSGraphicsContext.restoreGraphicsState()
try bitmap.representation(using: .png, properties: [:])!.write(to: output)
