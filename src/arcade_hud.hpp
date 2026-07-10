#pragma once

#include <array>
#include <string>

namespace harbor::ui {

inline constexpr int kMaxHudRacers = 8;

struct VehicleStatsViewModel {
    float speed = 0.0f;
    float acceleration = 0.0f;
    float handling = 0.0f;
    float strength = 0.0f;
};

struct RaceHudViewModel {
    std::string vehicleName;
    std::string driverName;
    int speedKph = 0;
    int currentLap = 1;
    int totalLaps = 2;
    int position = 1;
    int racerCount = 1;
    float raceTimeSeconds = 0.0f;
    float raceProgress = 0.0f;
    std::array<float, kMaxHudRacers> racerProgress{};
    int racerProgressCount = 0;
    int playerProgressIndex = 0;
    float driftCharge = 0.0f;
    float boostCharge = 0.0f;
    float presentationTimeSeconds = 0.0f;
    bool boostActive = false;
    bool wrongWay = false;
    bool finished = false;
    bool controllerConnected = true;
};

struct GarageHudViewModel {
    std::string eventName;
    std::string vehicleName;
    std::string vehicleClass;
    std::string driverName;
    VehicleStatsViewModel stats;
    int vehicleIndex = 0;
    int vehicleCount = 1;
    int driverIndex = 0;
    int driverCount = 1;
    std::array<int, 4> lapOptions = {2, 5, 10, 0};
    int lapOptionCount = 4;
    int selectedLapOption = 0;
    float presentationTimeSeconds = 0.0f;
    bool canStart = true;
    bool controllerConnected = true;
};

struct CountdownHudViewModel {
    float secondsRemaining = 3.0f;
    bool visible = false;
};

enum class PauseAction {
    Resume,
    Restart,
    Garage,
    Quit,
};

struct PauseHudViewModel {
    std::string eventName;
    int currentLap = 1;
    int totalLaps = 2;
    float raceTimeSeconds = 0.0f;
    PauseAction selectedAction = PauseAction::Resume;
    bool showRestart = true;
    bool showGarage = true;
    bool showQuit = true;
    bool visible = false;
};

void DrawRaceHud(const RaceHudViewModel& viewModel);
void DrawGarageHud(const GarageHudViewModel& viewModel);
void DrawCountdownHud(const CountdownHudViewModel& viewModel);
void DrawPauseHud(const PauseHudViewModel& viewModel);

}  // namespace harbor::ui
