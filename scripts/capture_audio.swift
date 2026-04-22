import Foundation
import ScreenCaptureKit
import AVFoundation

let SAMPLE_RATE: Double = 48000
let CHANNELS: Int = 2

class AudioCapture: NSObject, SCStreamOutput, SCStreamDelegate {
    var stream: SCStream?
    var fileHandle: FileHandle?
    let outputPath: String
    var frameCount: Int64 = 0
    var stopping = false

    init(outputPath: String) {
        self.outputPath = outputPath
    }

    func writeWAVHeader(frameCount: Int64) {
        guard let fh = FileHandle(forWritingAtPath: outputPath) else { return }
        fh.seek(toFileOffset: 0)
        let byteRate = Int32(SAMPLE_RATE) * Int32(CHANNELS) * 2
        let blockAlign = Int16(CHANNELS * 2)
        let dataSize = Int32(frameCount * Int64(CHANNELS) * 2)
        var header = Data()
        header += "RIFF".data(using: .ascii)!
        header += withUnsafeBytes(of: Int32(36 + dataSize).littleEndian) { Data($0) }
        header += "WAVE".data(using: .ascii)!
        header += "fmt ".data(using: .ascii)!
        header += withUnsafeBytes(of: Int32(16).littleEndian) { Data($0) }
        header += withUnsafeBytes(of: Int16(1).littleEndian) { Data($0) }
        header += withUnsafeBytes(of: Int16(CHANNELS).littleEndian) { Data($0) }
        header += withUnsafeBytes(of: Int32(SAMPLE_RATE).littleEndian) { Data($0) }
        header += withUnsafeBytes(of: byteRate.littleEndian) { Data($0) }
        header += withUnsafeBytes(of: blockAlign.littleEndian) { Data($0) }
        header += withUnsafeBytes(of: Int16(16).littleEndian) { Data($0) }
        header += "data".data(using: .ascii)!
        header += withUnsafeBytes(of: dataSize.littleEndian) { Data($0) }
        fh.write(header)
        fh.closeFile()
    }

    func start() async {
        FileManager.default.createFile(atPath: outputPath, contents: Data(count: 44))
        fileHandle = FileHandle(forWritingAtPath: outputPath)
        fileHandle?.seek(toFileOffset: 44)

        do {
            let content = try await SCShareableContent.current
            let filter = SCContentFilter(display: content.displays[0], excludingWindows: [])
            let config = SCStreamConfiguration()
            config.capturesAudio = true
            config.sampleRate = Int(SAMPLE_RATE)
            config.channelCount = CHANNELS

            stream = SCStream(filter: filter, configuration: config, delegate: self)
            try stream?.addStreamOutput(self, type: .audio, sampleHandlerQueue: .global())
            try await stream?.startCapture()
            print("Recording started.")
        } catch {
            print("Error: \(error)")
        }
    }

    func stop() {
        guard !stopping else { return }
        stopping = true
        Task {
            try? await stream?.stopCapture()
            fileHandle?.closeFile()
            writeWAVHeader(frameCount: frameCount)
            print("Saved \(frameCount) frames to \(outputPath)")
            exit(0)
        }
    }

    func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer, of type: SCStreamOutputType) {
        guard type == .audio, !stopping else { return }
        guard let blockBuffer = sampleBuffer.dataBuffer else { return }

        var lengthAtOffset = 0
        var totalLength = 0
        var dataPointer: UnsafeMutablePointer<Int8>?
        CMBlockBufferGetDataPointer(blockBuffer, atOffset: 0, lengthAtOffsetOut: &lengthAtOffset, totalLengthOut: &totalLength, dataPointerOut: &dataPointer)

        if let ptr = dataPointer, totalLength > 0 {
            // SCStream outputs Float32 non-interleaved — convert to Int16 interleaved
            let floatCount = totalLength / MemoryLayout<Float32>.size
            let samplesPerChannel = floatCount / CHANNELS
            let floatPtr = UnsafeRawPointer(ptr).bindMemory(to: Float32.self, capacity: floatCount)
            var int16Data = Data(count: samplesPerChannel * CHANNELS * MemoryLayout<Int16>.size)
            int16Data.withUnsafeMutableBytes { rawBuf in
                let int16Buf = rawBuf.bindMemory(to: Int16.self)
                for i in 0..<samplesPerChannel {
                    for ch in 0..<CHANNELS {
                        let sample = floatPtr[ch * samplesPerChannel + i]
                        let clamped = max(-1.0, min(1.0, sample))
                        int16Buf[i * CHANNELS + ch] = Int16(clamped * 32767.0)
                    }
                }
            }
            fileHandle?.write(int16Data)
            frameCount += Int64(samplesPerChannel)
        }
    }

    func stream(_ stream: SCStream, didStopWithError error: Error) {
        print("Stream stopped: \(error)")
        stop()
    }
}

let args = CommandLine.arguments
let outputPath = args.count > 1 ? args[1] : "/tmp/system_audio.wav"

let capture = AudioCapture(outputPath: outputPath)

signal(SIGTERM) { _ in capture.stop() }
signal(SIGINT)  { _ in capture.stop() }

Task { await capture.start() }
RunLoop.main.run()
