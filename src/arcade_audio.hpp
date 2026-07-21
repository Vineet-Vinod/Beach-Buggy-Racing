#pragma once

#include <cstdint>
#include <memory>

struct ArcadeAudioInput {
    bool shiftAlert = false;
};

struct ArcadeAudioAuditResult {
    bool ok = false;
    int checks = 0;
    int failures = 0;
    float silenceRms = 0.0f;
    float beepRms = 0.0f;
    float heldAlertRms = 0.0f;
    float peakMagnitude = 0.0f;
    uint64_t deterministicHash = 0;
};

// Owns the one-shot shift-alert output. It is silent at all other times. All
// methods are safe when no audio device is available.
class ArcadeAudio {
  public:
    ArcadeAudio();
    ~ArcadeAudio();

    ArcadeAudio(const ArcadeAudio&) = delete;
    ArcadeAudio& operator=(const ArcadeAudio&) = delete;
    ArcadeAudio(ArcadeAudio&&) noexcept;
    ArcadeAudio& operator=(ArcadeAudio&&) noexcept;

    bool initialize();
    void shutdown();
    void update(const ArcadeAudioInput& input);
    void setMasterVolume(float volume);

    [[nodiscard]] bool isReady() const;

  private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

ArcadeAudioAuditResult runArcadeAudioUnitAudit();
bool playArcadeShiftBeepPreview();
