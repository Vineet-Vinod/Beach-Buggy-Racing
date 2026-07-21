#include "arcade_audio.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdio>
#include <cstring>
#include <utility>
#include <vector>

#include <SDL3/SDL.h>

namespace {

constexpr unsigned int kSampleRate = 48000;
constexpr unsigned int kChannels = 2;
constexpr std::size_t kFramesPerBuffer = 1024;
constexpr float kPi = 3.14159265358979323846f;

class ArcadeSynth {
  public:
    void setInput(const ArcadeAudioInput& input) {
        if (input.shiftAlert && !wasShiftAlert_) {
            shiftAlertEnvelope_ = 1.0f;
            shiftAlertPhase_ = 0.0f;
        }
        wasShiftAlert_ = input.shiftAlert;
    }

    void render(float* stereo, std::size_t frames) {
        if (stereo == nullptr) return;

        constexpr float dt = 1.0f / static_cast<float>(kSampleRate);
        for (std::size_t frame = 0; frame < frames; ++frame) {
            shiftAlertPhase_ = wrapPhase(shiftAlertPhase_ + 1350.0f * dt);
            const float shiftBeep = std::sin(2.0f * kPi * shiftAlertPhase_) * shiftAlertEnvelope_ * 0.82f;
            shiftAlertEnvelope_ *= 0.99940f;
            if (shiftAlertEnvelope_ < 0.00001f) shiftAlertEnvelope_ = 0.0f;
            stereo[frame * 2] = shiftBeep;
            stereo[frame * 2 + 1] = shiftBeep;
        }
    }

  private:
    static float wrapPhase(float phase) {
        return phase >= 1.0f ? phase - std::floor(phase) : phase;
    }

    float shiftAlertPhase_ = 0.0f;
    float shiftAlertEnvelope_ = 0.0f;
    bool wasShiftAlert_ = false;
};

struct SignalMetrics {
    float rms = 0.0f;
    float peak = 0.0f;
};

SignalMetrics measure(const std::vector<float>& samples) {
    double energy = 0.0;
    float peak = 0.0f;
    for (const float sample : samples) {
        energy += static_cast<double>(sample) * sample;
        peak = std::max(peak, std::abs(sample));
    }
    return {samples.empty() ? 0.0f : static_cast<float>(std::sqrt(energy / samples.size())), peak};
}

uint64_t hashSamples(const std::vector<float>& samples) {
    uint64_t hash = 1469598103934665603ull;
    for (float sample : samples) {
        uint32_t bits = 0;
        std::memcpy(&bits, &sample, sizeof(bits));
        for (int byte = 0; byte < 4; ++byte) {
            hash ^= (bits >> (byte * 8)) & 0xffu;
            hash *= 1099511628211ull;
        }
    }
    return hash;
}

std::vector<float> renderScenario(const ArcadeAudioInput& input, int blocks) {
    ArcadeSynth synth;
    std::vector<float> output(kFramesPerBuffer * kChannels * static_cast<std::size_t>(blocks));
    std::array<float, kFramesPerBuffer * kChannels> block{};
    for (int i = 0; i < blocks; ++i) {
        synth.setInput(input);
        synth.render(block.data(), kFramesPerBuffer);
        std::copy(block.begin(), block.end(), output.begin() + static_cast<std::ptrdiff_t>(i) * block.size());
    }
    return output;
}

}  // namespace

struct ArcadeAudio::Impl {
    SDL_AudioStream* stream = nullptr;
    ArcadeSynth synth{};
    std::array<float, kFramesPerBuffer * kChannels> samples{};
    bool ready = false;
    bool ownsAudioSubsystem = false;
    float volume = 0.72f;
};

ArcadeAudio::ArcadeAudio() : impl_(std::make_unique<Impl>()) {}
ArcadeAudio::~ArcadeAudio() { shutdown(); }
ArcadeAudio::ArcadeAudio(ArcadeAudio&& other) noexcept : impl_(std::move(other.impl_)) {}
ArcadeAudio& ArcadeAudio::operator=(ArcadeAudio&& other) noexcept {
    if (this != &other) {
        shutdown();
        impl_ = std::move(other.impl_);
    }
    return *this;
}

bool ArcadeAudio::initialize() {
    if (!impl_) impl_ = std::make_unique<Impl>();
    if (impl_->ready) return true;
    if (impl_->stream != nullptr) {
        SDL_DestroyAudioStream(impl_->stream);
        impl_->stream = nullptr;
    }

    if ((SDL_WasInit(SDL_INIT_AUDIO) & SDL_INIT_AUDIO) == 0) {
        if (!SDL_InitSubSystem(SDL_INIT_AUDIO)) return false;
        impl_->ownsAudioSubsystem = true;
    }

    SDL_AudioSpec spec{};
    spec.format = SDL_AUDIO_F32;
    spec.channels = kChannels;
    spec.freq = static_cast<int>(kSampleRate);
    impl_->stream = SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK, &spec, nullptr, nullptr);
    if (impl_->stream == nullptr) {
        if (impl_->ownsAudioSubsystem) SDL_QuitSubSystem(SDL_INIT_AUDIO);
        impl_->ownsAudioSubsystem = false;
        return false;
    }

    SDL_SetAudioStreamGain(impl_->stream, impl_->volume);
    for (int buffer = 0; buffer < 2; ++buffer) {
        impl_->synth.render(impl_->samples.data(), kFramesPerBuffer);
        if (!SDL_PutAudioStreamData(impl_->stream, impl_->samples.data(),
                                    static_cast<int>(sizeof(impl_->samples)))) {
            SDL_DestroyAudioStream(impl_->stream);
            impl_->stream = nullptr;
            if (impl_->ownsAudioSubsystem) SDL_QuitSubSystem(SDL_INIT_AUDIO);
            impl_->ownsAudioSubsystem = false;
            return false;
        }
    }
    if (!SDL_ResumeAudioStreamDevice(impl_->stream)) {
        SDL_DestroyAudioStream(impl_->stream);
        impl_->stream = nullptr;
        if (impl_->ownsAudioSubsystem) SDL_QuitSubSystem(SDL_INIT_AUDIO);
        impl_->ownsAudioSubsystem = false;
        return false;
    }
    impl_->ready = true;
    return true;
}

void ArcadeAudio::shutdown() {
    if (!impl_) return;
    if (impl_->stream != nullptr) {
        SDL_DestroyAudioStream(impl_->stream);
        impl_->stream = nullptr;
    }
    impl_->ready = false;
    if (impl_->ownsAudioSubsystem) SDL_QuitSubSystem(SDL_INIT_AUDIO);
    impl_->ownsAudioSubsystem = false;
}

void ArcadeAudio::update(const ArcadeAudioInput& input) {
    if (!impl_) return;
    impl_->synth.setInput(input);
    if (!impl_->ready || impl_->stream == nullptr) return;

    constexpr int bytesPerBuffer = static_cast<int>(kFramesPerBuffer * kChannels * sizeof(float));
    for (int buffer = 0; buffer < 2 && SDL_GetAudioStreamQueued(impl_->stream) < bytesPerBuffer * 2; ++buffer) {
        impl_->synth.render(impl_->samples.data(), kFramesPerBuffer);
        if (!SDL_PutAudioStreamData(impl_->stream, impl_->samples.data(), bytesPerBuffer)) {
            impl_->ready = false;
            break;
        }
    }
}

void ArcadeAudio::setMasterVolume(float volume) {
    if (!impl_) return;
    impl_->volume = std::clamp(std::isfinite(volume) ? volume : 0.0f, 0.0f, 1.0f);
    if (impl_->ready) SDL_SetAudioStreamGain(impl_->stream, impl_->volume);
}

bool ArcadeAudio::isReady() const {
    return impl_ && impl_->ready && impl_->stream != nullptr;
}

ArcadeAudioAuditResult runArcadeAudioUnitAudit() {
    ArcadeAudioAuditResult result;
    auto check = [&](bool condition) {
        ++result.checks;
        if (!condition) ++result.failures;
        return condition;
    };

    const ArcadeAudioInput silent;
    const std::vector<float> silentSignal = renderScenario(silent, 8);
    const SignalMetrics silentMetrics = measure(silentSignal);
    result.silenceRms = silentMetrics.rms;
    check(silentMetrics.rms < 0.000001f && silentMetrics.peak < 0.000001f);

    ArcadeAudioInput alert;
    alert.shiftAlert = true;
    const std::vector<float> beepSignal = renderScenario(alert, 4);
    const SignalMetrics beepMetrics = measure(beepSignal);
    result.beepRms = beepMetrics.rms;
    result.peakMagnitude = beepMetrics.peak;
    check(beepMetrics.rms > 0.12f);
    check(beepMetrics.peak > 0.75f && beepMetrics.peak < 0.90f);

    ArcadeSynth heldSynth;
    std::array<float, kFramesPerBuffer * kChannels> block{};
    heldSynth.setInput(alert);
    heldSynth.render(block.data(), kFramesPerBuffer);
    for (int heldBlock = 0; heldBlock < 15; ++heldBlock) {
        heldSynth.setInput(alert);
        heldSynth.render(block.data(), kFramesPerBuffer);
    }
    const std::vector<float> heldSignal(block.begin(), block.end());
    result.heldAlertRms = measure(heldSignal).rms;
    check(result.heldAlertRms < 0.001f);

    ArcadeAudioInput released;
    heldSynth.setInput(released);
    heldSynth.render(block.data(), kFramesPerBuffer);
    heldSynth.setInput(alert);
    heldSynth.render(block.data(), kFramesPerBuffer);
    check(measure(std::vector<float>(block.begin(), block.end())).rms > 0.12f);

    result.deterministicHash = hashSamples(beepSignal);
    check(result.deterministicHash == hashSamples(renderScenario(alert, 4)));
    check(std::all_of(beepSignal.begin(), beepSignal.end(), [](float sample) { return std::isfinite(sample); }));

    result.ok = result.failures == 0;
    return result;
}

bool playArcadeShiftBeepPreview() {
    ArcadeAudio audio;
    if (!audio.initialize()) {
        std::fprintf(stderr, "shift beep preview could not open audio: %s\navailable SDL audio drivers:", SDL_GetError());
        const int driverCount = SDL_GetNumAudioDrivers();
        for (int driver = 0; driver < driverCount; ++driver) {
            std::fprintf(stderr, " %s", SDL_GetAudioDriver(driver));
        }
        std::fprintf(stderr, "\n");
        return false;
    }

    ArcadeAudioInput input;
    for (int frame = 0; frame < 120; ++frame) {
        input.shiftAlert = frame >= 12 && frame < 36;
        audio.update(input);
        SDL_Delay(8);
    }
    audio.shutdown();
    return true;
}
