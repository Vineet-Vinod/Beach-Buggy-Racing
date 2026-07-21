#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <span>

namespace formula_forge {

// Inputs stay independent of the runtime track type so generated, rendered,
// and collision widths can be checked against the same centerline.
struct TrackClearanceSample {
    float x = 0.0f;
    float z = 0.0f;
    float elevation = 0.0f;
    float progress = 0.0f;
    float physicalRoadHalfWidth = 0.0f;
    float renderedRoadHalfWidth = 0.0f;
};

struct TrackClearanceAuditSettings {
    float totalLength = 0.0f;
    float widestKartWidth = 0.0f;
    float kartContactHalfWidthScale = 0.64f;
    float roadLaneInset = 0.0f;
    float twoKartPassingMargin = 0.0f;

    // Segments this close along the racing line are part of the same corner,
    // rather than independent branches that can intersect each other.
    float localArcExclusion = 0.0f;
    float verticalOverlapTolerance = 0.0f;
    float minimumSegmentLength = 0.001f;
    float overlapTolerance = 0.01f;
    float widthParityTolerance = 0.01f;
};

struct TrackClearanceAuditResult {
    size_t sampleCount = 0;
    size_t testedNonLocalPairs = 0;
    size_t physicalOverlapPairs = 0;
    size_t renderedOverlapPairs = 0;
    size_t degenerateSegments = 0;
    bool finite = true;
    bool positiveWidths = true;
    bool orderedProgress = true;

    float minPhysicalRoadWidth = std::numeric_limits<float>::infinity();
    float maxPhysicalRoadWidth = 0.0f;
    float minRenderedRoadWidth = std::numeric_limits<float>::infinity();
    float maxRenderedRoadWidth = 0.0f;
    float minKartCenterLimit = std::numeric_limits<float>::infinity();
    float minKartCenterSpan = std::numeric_limits<float>::infinity();
    float minTwoKartPassingClearance = std::numeric_limits<float>::infinity();
    float minRenderedPhysicalMargin = std::numeric_limits<float>::infinity();
    float widthParityTolerance = 0.0f;

    float minNonLocalCenterlineDistance = std::numeric_limits<float>::infinity();
    float minPhysicalNonLocalClearance = std::numeric_limits<float>::infinity();
    float minRenderedNonLocalClearance = std::numeric_limits<float>::infinity();
    float physicalClosestProgressA = 0.0f;
    float physicalClosestProgressB = 0.0f;
    float renderedClosestProgressA = 0.0f;
    float renderedClosestProgressB = 0.0f;

    bool widestKartFits() const { return finite && positiveWidths && minKartCenterLimit >= 0.0f; }
    bool supportsTwoKartPassing() const { return widestKartFits() && minTwoKartPassingClearance >= 0.0f; }
    bool renderedWidthCoversPhysics() const {
        return finite && positiveWidths && minRenderedPhysicalMargin >= -widthParityTolerance;
    }
    bool hasSafeNonLocalClearance() const {
        return finite && physicalOverlapPairs == 0 && renderedOverlapPairs == 0;
    }
    bool ok() const {
        return sampleCount >= 3 && testedNonLocalPairs > 0 && finite && positiveWidths && orderedProgress &&
               degenerateSegments == 0 && widestKartFits() && supportsTwoKartPassing() &&
               renderedWidthCoversPhysics() && hasSafeNonLocalClearance();
    }
};

namespace detail {

struct Point2 {
    float x = 0.0f;
    float z = 0.0f;
};

struct SegmentDistance {
    float distance = 0.0f;
    float firstT = 0.0f;
    float secondT = 0.0f;
};

inline float dot(Point2 a, Point2 b) { return a.x * b.x + a.z * b.z; }
inline Point2 subtract(Point2 a, Point2 b) { return {a.x - b.x, a.z - b.z}; }
inline Point2 add(Point2 a, Point2 b) { return {a.x + b.x, a.z + b.z}; }
inline Point2 scale(Point2 value, float amount) { return {value.x * amount, value.z * amount}; }
inline float lengthSquared(Point2 value) { return dot(value, value); }

inline SegmentDistance segmentDistance(Point2 a0, Point2 a1, Point2 b0, Point2 b1) {
    constexpr float kEpsilon = 0.000001f;
    const Point2 a = subtract(a1, a0);
    const Point2 b = subtract(b1, b0);
    const Point2 offset = subtract(a0, b0);
    const float aa = dot(a, a);
    const float bb = dot(b, b);
    const float ab = dot(a, b);
    const float ao = dot(a, offset);
    const float bo = dot(b, offset);
    const float denominator = aa * bb - ab * ab;

    float firstT = 0.0f;
    float secondT = 0.0f;
    if (aa <= kEpsilon && bb <= kEpsilon) {
        return {std::sqrt(lengthSquared(offset)), 0.0f, 0.0f};
    }
    if (aa <= kEpsilon) {
        secondT = std::clamp(bo / bb, 0.0f, 1.0f);
    } else if (bb <= kEpsilon) {
        firstT = std::clamp(-ao / aa, 0.0f, 1.0f);
    } else {
        firstT = denominator > kEpsilon ? std::clamp((ab * bo - ao * bb) / denominator, 0.0f, 1.0f) : 0.0f;
        secondT = (ab * firstT + bo) / bb;
        if (secondT < 0.0f) {
            secondT = 0.0f;
            firstT = std::clamp(-ao / aa, 0.0f, 1.0f);
        } else if (secondT > 1.0f) {
            secondT = 1.0f;
            firstT = std::clamp((ab - ao) / aa, 0.0f, 1.0f);
        }
    }

    const Point2 closestA = add(a0, scale(a, firstT));
    const Point2 closestB = add(b0, scale(b, secondT));
    return {std::sqrt(lengthSquared(subtract(closestA, closestB))), firstT, secondT};
}

inline float interpolate(float a, float b, float t) { return a + (b - a) * t; }

inline float segmentProgress(const TrackClearanceSample& a, const TrackClearanceSample& b, float t, float totalLength) {
    float end = b.progress;
    if (end < a.progress) {
        end += totalLength;
    }
    float progress = interpolate(a.progress, end, t);
    if (progress >= totalLength) {
        progress -= totalLength;
    }
    return progress;
}

inline float loopDistance(float a, float b, float totalLength) {
    const float direct = std::abs(a - b);
    return std::min(direct, totalLength - direct);
}

inline bool finite(const TrackClearanceSample& sample) {
    return std::isfinite(sample.x) && std::isfinite(sample.z) && std::isfinite(sample.elevation) &&
           std::isfinite(sample.progress) && std::isfinite(sample.physicalRoadHalfWidth) &&
           std::isfinite(sample.renderedRoadHalfWidth);
}

}  // namespace detail

inline TrackClearanceAuditResult AuditTrackClearance(std::span<const TrackClearanceSample> samples,
                                                      const TrackClearanceAuditSettings& settings) {
    TrackClearanceAuditResult result;
    result.sampleCount = samples.size();
    result.widthParityTolerance = settings.widthParityTolerance;
    if (samples.size() < 3 || !std::isfinite(settings.totalLength) || settings.totalLength <= 0.0f ||
        !std::isfinite(settings.widestKartWidth) || settings.widestKartWidth <= 0.0f ||
        !std::isfinite(settings.kartContactHalfWidthScale) || settings.kartContactHalfWidthScale <= 0.0f ||
        !std::isfinite(settings.roadLaneInset) || settings.roadLaneInset < 0.0f ||
        !std::isfinite(settings.twoKartPassingMargin) || settings.twoKartPassingMargin < 0.0f ||
        !std::isfinite(settings.localArcExclusion) || settings.localArcExclusion < 0.0f ||
        !std::isfinite(settings.verticalOverlapTolerance) || settings.verticalOverlapTolerance < 0.0f ||
        !std::isfinite(settings.minimumSegmentLength) || settings.minimumSegmentLength <= 0.0f ||
        !std::isfinite(settings.overlapTolerance) || settings.overlapTolerance < 0.0f ||
        !std::isfinite(settings.widthParityTolerance) || settings.widthParityTolerance < 0.0f) {
        result.finite = false;
        return result;
    }

    const float kartHalfWidth = settings.widestKartWidth * settings.kartContactHalfWidthScale;
    for (size_t index = 0; index < samples.size(); ++index) {
        const TrackClearanceSample& sample = samples[index];
        result.finite = result.finite && detail::finite(sample);
        result.positiveWidths = result.positiveWidths && sample.physicalRoadHalfWidth > 0.0f &&
                                sample.renderedRoadHalfWidth > 0.0f;
        result.orderedProgress = result.orderedProgress && sample.progress >= 0.0f && sample.progress < settings.totalLength &&
                                 (index == 0 || sample.progress > samples[index - 1].progress);
        const float physicalWidth = sample.physicalRoadHalfWidth * 2.0f;
        const float renderedWidth = sample.renderedRoadHalfWidth * 2.0f;
        const float centerLimit = sample.physicalRoadHalfWidth - kartHalfWidth - settings.roadLaneInset;
        const float centerSpan = centerLimit * 2.0f;
        const float passingClearance = centerSpan - kartHalfWidth * 2.0f - settings.twoKartPassingMargin;
        result.minPhysicalRoadWidth = std::min(result.minPhysicalRoadWidth, physicalWidth);
        result.maxPhysicalRoadWidth = std::max(result.maxPhysicalRoadWidth, physicalWidth);
        result.minRenderedRoadWidth = std::min(result.minRenderedRoadWidth, renderedWidth);
        result.maxRenderedRoadWidth = std::max(result.maxRenderedRoadWidth, renderedWidth);
        result.minKartCenterLimit = std::min(result.minKartCenterLimit, centerLimit);
        result.minKartCenterSpan = std::min(result.minKartCenterSpan, centerSpan);
        result.minTwoKartPassingClearance = std::min(result.minTwoKartPassingClearance, passingClearance);
        result.minRenderedPhysicalMargin =
            std::min(result.minRenderedPhysicalMargin, sample.renderedRoadHalfWidth - sample.physicalRoadHalfWidth);
    }
    if (!result.finite || !result.positiveWidths || !result.orderedProgress) {
        return result;
    }

    for (size_t first = 0; first < samples.size(); ++first) {
        const size_t firstNext = (first + 1) % samples.size();
        const TrackClearanceSample& a0 = samples[first];
        const TrackClearanceSample& a1 = samples[firstNext];
        const detail::Point2 firstDelta{a1.x - a0.x, a1.z - a0.z};
        if (detail::lengthSquared(firstDelta) < settings.minimumSegmentLength * settings.minimumSegmentLength) {
            ++result.degenerateSegments;
        }

        for (size_t second = first + 1; second < samples.size(); ++second) {
            const size_t secondNext = (second + 1) % samples.size();
            if (second == firstNext || secondNext == first) {
                continue;
            }
            const TrackClearanceSample& b0 = samples[second];
            const TrackClearanceSample& b1 = samples[secondNext];
            const detail::SegmentDistance closest = detail::segmentDistance({a0.x, a0.z}, {a1.x, a1.z},
                                                                            {b0.x, b0.z}, {b1.x, b1.z});
            const float progressA = detail::segmentProgress(a0, a1, closest.firstT, settings.totalLength);
            const float progressB = detail::segmentProgress(b0, b1, closest.secondT, settings.totalLength);
            if (detail::loopDistance(progressA, progressB, settings.totalLength) < settings.localArcExclusion) {
                continue;
            }

            const float elevationA = detail::interpolate(a0.elevation, a1.elevation, closest.firstT);
            const float elevationB = detail::interpolate(b0.elevation, b1.elevation, closest.secondT);
            if (std::abs(elevationA - elevationB) > settings.verticalOverlapTolerance) {
                continue;
            }

            ++result.testedNonLocalPairs;
            result.minNonLocalCenterlineDistance = std::min(result.minNonLocalCenterlineDistance, closest.distance);
            const float physicalHalfA = detail::interpolate(a0.physicalRoadHalfWidth, a1.physicalRoadHalfWidth, closest.firstT);
            const float physicalHalfB = detail::interpolate(b0.physicalRoadHalfWidth, b1.physicalRoadHalfWidth, closest.secondT);
            const float renderedHalfA = detail::interpolate(a0.renderedRoadHalfWidth, a1.renderedRoadHalfWidth, closest.firstT);
            const float renderedHalfB = detail::interpolate(b0.renderedRoadHalfWidth, b1.renderedRoadHalfWidth, closest.secondT);
            const float physicalClearance = closest.distance - physicalHalfA - physicalHalfB;
            const float renderedClearance = closest.distance - renderedHalfA - renderedHalfB;
            if (physicalClearance < result.minPhysicalNonLocalClearance) {
                result.minPhysicalNonLocalClearance = physicalClearance;
                result.physicalClosestProgressA = progressA;
                result.physicalClosestProgressB = progressB;
            }
            if (renderedClearance < result.minRenderedNonLocalClearance) {
                result.minRenderedNonLocalClearance = renderedClearance;
                result.renderedClosestProgressA = progressA;
                result.renderedClosestProgressB = progressB;
            }
            result.physicalOverlapPairs += physicalClearance < -settings.overlapTolerance ? 1 : 0;
            result.renderedOverlapPairs += renderedClearance < -settings.overlapTolerance ? 1 : 0;
        }
    }
    return result;
}

}  // namespace formula_forge
