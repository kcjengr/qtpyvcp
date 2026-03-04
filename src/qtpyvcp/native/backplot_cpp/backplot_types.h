#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

namespace qtpyvcp::backplot {

struct SegmentPoint {
    double x{0.0};
    double y{0.0};
    double z{0.0};
};

struct Segment {
    SegmentPoint start;
    SegmentPoint end;
    std::uint8_t motion_type{0};
};

struct BuildStats {
    std::size_t added_segments{0};
    double draw_ms{0.0};
};

}  // namespace qtpyvcp::backplot
