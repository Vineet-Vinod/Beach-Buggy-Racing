#pragma once

#include <array>

struct TrackControlPoint {
    float x = 0.0f;
    float y = 0.0f;
};

inline constexpr float kBreakwaterCourseScale = 1.025f;

// Driving line reconstructed from the supplied Shark Harbor footage. The lap
// follows its waterfront run, harbor bend, town complex, hillside climb,
// crest bends, downhill return, jungle corner, and waterfront finish.
// The route stays non-self-intersecting so the visible road is always the road
// the player should follow.
inline constexpr std::array<TrackControlPoint, 27> kBreakwaterControlPoints = {{
    {-920.0f, -940.0f},  {-540.0f, -990.0f}, {-100.0f, -985.0f}, {350.0f, -955.0f},
    {730.0f, -845.0f},   {1010.0f, -650.0f}, {1160.0f, -390.0f}, {1170.0f, -130.0f},
    {1010.0f, 70.0f},    {820.0f, 145.0f},   {1030.0f, 335.0f},  {1060.0f, 580.0f},
    {860.0f, 805.0f},    {560.0f, 930.0f},   {260.0f, 910.0f},   {20.0f, 770.0f},
    {-115.0f, 560.0f},   {55.0f, 365.0f},    {105.0f, 145.0f},   {-80.0f, -35.0f},
    {-355.0f, 45.0f},    {-610.0f, 205.0f},  {-865.0f, 125.0f},  {-1045.0f, -80.0f},
    {-1120.0f, -355.0f}, {-1070.0f, -620.0f}, {-990.0f, -825.0f},
}};
