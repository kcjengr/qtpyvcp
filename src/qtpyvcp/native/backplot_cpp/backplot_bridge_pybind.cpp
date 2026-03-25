#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

namespace py = pybind11;

static bool py_equals(const py::handle &lhs, const py::handle &rhs) {
    return PyObject_RichCompareBool(lhs.ptr(), rhs.ptr(), Py_EQ) == 1;
}

static std::array<double, 3> point_xyz(const py::handle &point, double factor) {
    PyObject *seq = PySequence_Fast(point.ptr(), "point must be a sequence");
    if (seq == nullptr) {
        throw py::error_already_set();
    }

    const auto size = PySequence_Fast_GET_SIZE(seq);
    if (size < 3) {
        Py_DECREF(seq);
        throw std::runtime_error("point sequence has fewer than 3 values");
    }

    auto to_double = [](PyObject *obj) -> double {
        const double value = PyFloat_AsDouble(obj);
        if (PyErr_Occurred()) {
            throw py::error_already_set();
        }
        return value;
    };

    std::array<double, 3> xyz{
        to_double(PySequence_Fast_GET_ITEM(seq, 0)) * factor,
        to_double(PySequence_Fast_GET_ITEM(seq, 1)) * factor,
        to_double(PySequence_Fast_GET_ITEM(seq, 2)) * factor,
    };

    Py_DECREF(seq);
    return xyz;
}

static std::array<std::uint8_t, 4> color_rgba(py::object path_colors, const std::string &line_type) {
    py::object color = path_colors.attr("get")(py::str(line_type));
    py::tuple rgba = color.attr("getRgb")().cast<py::tuple>();
    return std::array<std::uint8_t, 4>{
        static_cast<std::uint8_t>(py::int_(rgba[0])),
        static_cast<std::uint8_t>(py::int_(rgba[1])),
        static_cast<std::uint8_t>(py::int_(rgba[2])),
        static_cast<std::uint8_t>(py::int_(rgba[3])),
    };
}

struct LinePoints {
    std::array<double, 3> start;
    std::array<double, 3> end;
};

struct LineTypeInfo {
    std::string color_key;
    bool is_traverse{false};
};

struct NativeLine {
    std::uint8_t type_code{0};
    std::array<double, 3> start{};
    std::array<double, 3> end{};
    std::array<std::uint8_t, 4> rgba{};
};

struct NativeSegment {
    int wcs_index{0};
    std::vector<NativeLine> lines;
};

class NativeCanon {
public:
    explicit NativeCanon(py::object path_colors_obj)
        : path_colors(std::move(path_colors_obj)) {
        last_pos.fill(0.0);
        tool_offsets.fill(0.0);
        g92_offsets.fill(0.0);
        g5x_offsets.fill(0.0);
        external_length_units = 1.0;
        py::module_ gcode = py::module_::import("gcode");
        arc_to_segments_fn = gcode.attr("arc_to_segments");

        line_type_rgba[0] = color_rgba(path_colors, "traverse");
        line_type_rgba[1] = color_rgba(path_colors, "feed");
        line_type_rgba[2] = color_rgba(path_colors, "arcfeed");
        line_type_rgba[3] = color_rgba(path_colors, "dwell");
        line_type_rgba[4] = color_rgba(path_colors, "user");

        trace_logger = py::none();
    }

    bool should_trace_seq() const {
        return false;
    }

    static bool near_value(double value, double target, double tolerance) {
        return std::abs(value - target) <= tolerance;
    }

    bool should_trace_point(const std::array<double, 3> &point) const {
        (void)point;
        return false;
    }

    void trace_debug(const std::string &message) {
        (void)message;
    }

    void next_line(py::object state) {
        try {
            seq_num = py::int_(state.attr("sequence_number"));
        } catch (...) {
            seq_num = -1;
        }

        if (should_trace_seq()) {
            std::ostringstream oss;
            oss << "[cpp-trace] next_line seq=" << seq_num;
            trace_debug(oss.str());
        }
    }

    void set_g5x_offset(int index, double x, double y, double z, double a, double b, double c, double u, double v, double w) {
        g5x_offsets = {x, y, z, a, b, c, u, v, w};

        if (should_trace_seq() || index <= 1) {
            std::ostringstream oss;
            oss << "[cpp-trace] set_g5x_offset seq=" << seq_num
                << " index=" << index
                << " g5x_z=" << z
                << " active_wcs_before=" << active_wcs_index;
            trace_debug(oss.str());
        }

        // G53 (machine coordinates) is non-modal and should not create a WCS segment.
        if (index <= 0) {
            return;
        }

        const int new_wcs = index - 1;
        py::object wcs_key = py::int_(new_wcs);

        if (!initial_wcs_offsets.contains(wcs_key)) {
            initial_wcs_offsets[wcs_key] = py::make_tuple(x, y, z, a, b, c, u, v, w);
            initial_wcs_offsets_native[new_wcs] = {x, y, z};
        }

        const auto initial_it = initial_wcs_offsets_native.find(new_wcs);
        if (initial_it != initial_wcs_offsets_native.end()) {
            active_wcs_initial_x = initial_it->second[0];
            active_wcs_initial_y = initial_it->second[1];
            active_wcs_initial_z = initial_it->second[2];
        } else {
            active_wcs_initial_x = 0.0;
            active_wcs_initial_y = 0.0;
            active_wcs_initial_z = 0.0;
        }

        if (py::len(path_segments) == 0) {
            append_segment(new_wcs);
        } else {
            py::dict last_segment = path_segments[py::len(path_segments) - 1].cast<py::dict>();
            const int last_wcs = py::int_(last_segment["wcs_index"]);
            if (last_wcs != new_wcs) {
                append_segment(new_wcs);
            }
        }

        active_wcs_index = new_wcs;

        if (should_trace_seq() || new_wcs <= 1) {
            std::ostringstream oss;
            oss << "[cpp-trace] set_g5x_offset applied seq=" << seq_num
                << " new_wcs=" << new_wcs
                << " active_wcs_initial_z=" << active_wcs_initial_z;
            trace_debug(oss.str());
        }
    }

    void set_g92_offset(double x, double y, double z, double a, double b, double c, double u, double v, double w) {
        g92_offsets = {x, y, z, a, b, c, u, v, w};
    }

    void set_external_length_units(double units) {
        external_length_units = units;
    }

    void set_xy_rotation(double rotation) {
        rotation_xy = rotation;
        const double theta = rotation * M_PI / 180.0;
        rotation_cos = std::cos(theta);
        rotation_sin = std::sin(theta);
    }

    void tool_offset(double xo, double yo, double zo, double ao, double bo, double co, double uo, double vo, double wo) {
        first_move = true;
        path_initialized = false;
        last_pos = {
            last_pos[0] - xo + tool_offsets[0],
            last_pos[1] - yo + tool_offsets[1],
            last_pos[2] - zo + tool_offsets[2],
            last_pos[3] - ao + tool_offsets[3],
            last_pos[4] - bo + tool_offsets[4],
            last_pos[5] - co + tool_offsets[5],
            last_pos[6] - uo + tool_offsets[6],
            last_pos[7] - vo + tool_offsets[7],
            last_pos[8] - wo + tool_offsets[8],
        };
        tool_offsets = {xo, yo, zo, ao, bo, co, uo, vo, wo};

        if (should_trace_seq() || std::abs(zo) > 0.0001) {
            std::ostringstream oss;
            oss << "[cpp-trace] tool_offset seq=" << seq_num
                << " tool_z=" << zo;
            trace_debug(oss.str());
        }
    }

    void straight_traverse(double x, double y, double z, double a, double b, double c, double u, double v, double w) {
        if (suppress > 0) {
            return;
        }
        const auto pos = rotate_and_translate(x, y, z, a, b, c, u, v, w);
        if (!path_initialized) {
            // Initial machine position is unknown in preview; seed without
            // creating unprovable geometry.
            path_initialized = true;
            first_move = false;
            last_pos = pos;
            return;
        }
        if (!first_move) {
            add_path_point(0, last_pos, pos);
        } else {
            first_move = false;
        }
        last_pos = pos;
    }

    void straight_feed(double x, double y, double z, double a, double b, double c, double u, double v, double w) {
        if (suppress > 0) {
            return;
        }
        const auto pos = rotate_and_translate(x, y, z, a, b, c, u, v, w);
        if (!path_initialized) {
            path_initialized = true;
            first_move = false;
            last_pos = pos;
            return;
        }
        first_move = false;
        add_path_point(1, last_pos, pos);
        last_pos = pos;
    }

    void straight_probe(double x, double y, double z, double a, double b, double c, double u, double v, double w) {
        straight_feed(x, y, z, a, b, c, u, v, w);
    }

    void rigid_tap(double x, double y, double z) {
        if (suppress > 0) {
            return;
        }
        auto pos = rotate_and_translate(x, y, z, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
        pos[3] = last_pos[3];
        pos[4] = last_pos[4];
        pos[5] = last_pos[5];
        pos[6] = last_pos[6];
        pos[7] = last_pos[7];
        pos[8] = last_pos[8];
        if (!path_initialized) {
            path_initialized = true;
            first_move = false;
            last_pos = pos;
            return;
        }
        first_move = false;
        add_path_point(1, last_pos, pos);
        last_pos = pos;
    }

    void arc_feed(double end_x, double end_y, double center_x, double center_y, int rot, double end_z,
                  double a, double b, double c, double u, double v, double w) {
        if (suppress > 0) {
            return;
        }
        if (!path_initialized) {
            // An initial arc cannot be resolved without a known start point.
            // Seed at arc end and defer plotting until position is known.
            path_initialized = true;
            first_move = false;
            last_pos = rotate_and_translate(end_x, end_y, end_z, a, b, c, u, v, w);
            return;
        }
        first_move = false;
        in_arc = true;
        try {
            lo = py::make_tuple(
                last_pos[0], last_pos[1], last_pos[2], last_pos[3], last_pos[4],
                last_pos[5], last_pos[6], last_pos[7], last_pos[8]
            );
            py::object segs = arc_to_segments_fn(
                py::cast(this),
                end_x, end_y, center_x, center_y, rot, end_z, a, b, c, u, v, w, arcdivision
            );
            straight_arcsegments(segs);
        } catch (...) {
            in_arc = false;
            throw;
        }
        in_arc = false;
    }

    void straight_arcsegments(py::iterable segs) {
        first_move = false;
        auto arc_last = last_pos;
        for (auto pos_obj : segs) {
            const auto pos = seq_to_array9(pos_obj);
            add_path_point(2, arc_last, pos);
            arc_last = pos;
        }
        last_pos = arc_last;
    }

    void user_defined_function(int, double, double) {
        if (suppress > 0) {
            return;
        }
        add_path_point(4, last_pos, last_pos);
    }

    void dwell(double arg) {
        if (suppress > 0) {
            return;
        }
        dwell_time += arg;
        add_path_point(3, last_pos, last_pos);
    }

    void comment(py::object) {}
    void message(py::object) {}
    void check_abort() {}
    void set_spindle_rate(double) {}
    void set_feed_rate(double feed_rate) { feedrate = feed_rate / 60.0; }
    void set_plane(int plane_value) { plane = plane_value; }
    void select_plane(int plane_value) { plane = plane_value; }
    void set_traverse_rate(double) {}
    void set_feed_mode(int) {}
    void change_tool(int) {
        first_move = true;
        path_initialized = false;
    }
    py::tuple get_tool(int) {
        return py::make_tuple(-1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0);
    }
    double get_external_angular_units() { return 1.0; }
    double get_external_length_units() { return external_length_units; }
    int get_axis_mask() { return axis_mask; }
    void set_axis_mask(int mask) { axis_mask = mask; }
    int get_block_delete() { return 0; }
    void calc_extents() {}

    double get_g5x_offset_x() const { return g5x_offsets[0]; }
    double get_g5x_offset_y() const { return g5x_offsets[1]; }
    double get_g5x_offset_z() const { return g5x_offsets[2]; }
    double get_g5x_offset_a() const { return g5x_offsets[3]; }
    double get_g5x_offset_b() const { return g5x_offsets[4]; }
    double get_g5x_offset_c() const { return g5x_offsets[5]; }
    double get_g5x_offset_u() const { return g5x_offsets[6]; }
    double get_g5x_offset_v() const { return g5x_offsets[7]; }
    double get_g5x_offset_w() const { return g5x_offsets[8]; }

    double get_g92_offset_x() const { return g92_offsets[0]; }
    double get_g92_offset_y() const { return g92_offsets[1]; }
    double get_g92_offset_z() const { return g92_offsets[2]; }
    double get_g92_offset_a() const { return g92_offsets[3]; }
    double get_g92_offset_b() const { return g92_offsets[4]; }
    double get_g92_offset_c() const { return g92_offsets[5]; }
    double get_g92_offset_u() const { return g92_offsets[6]; }
    double get_g92_offset_v() const { return g92_offsets[7]; }
    double get_g92_offset_w() const { return g92_offsets[8]; }

    double get_rotation_cos() const { return rotation_cos; }
    double get_rotation_sin() const { return rotation_sin; }
    int get_plane() const { return plane; }

    py::object path_colors;
    py::list path_segments;
    py::dict initial_wcs_offsets;
    py::list offset_transitions;
    int added_segments{0};
    std::string parameter_file;
    py::tuple lo;

    const std::vector<NativeSegment> &native_segments_ref() const { return native_segments; }

private:
    void append_segment(int wcs_index) {
        py::dict segment;
        segment["wcs_index"] = py::int_(wcs_index);
        segment["lines"] = py::list();
        path_segments.append(segment);

        NativeSegment native_segment;
        native_segment.wcs_index = wcs_index;
        native_segments.push_back(std::move(native_segment));
    }

    static std::array<double, 9> seq_to_array9(const py::handle &seq_obj) {
        PyObject *seq = PySequence_Fast(seq_obj.ptr(), "expected a sequence");
        if (seq == nullptr) {
            throw py::error_already_set();
        }
        const auto size = PySequence_Fast_GET_SIZE(seq);
        if (size < 9) {
            Py_DECREF(seq);
            throw std::runtime_error("expected sequence with 9 items");
        }
        std::array<double, 9> out{};
        for (int i = 0; i < 9; ++i) {
            out[i] = PyFloat_AsDouble(PySequence_Fast_GET_ITEM(seq, i));
            if (PyErr_Occurred()) {
                Py_DECREF(seq);
                throw py::error_already_set();
            }
        }
        Py_DECREF(seq);
        return out;
    }

    std::array<double, 9> rotate_and_translate(double x, double y, double z, double a, double b, double c, double u, double v, double w) const {
        std::array<double, 9> p{x, y, z, a, b, c, u, v, w};

        for (int i = 0; i < 9; ++i) {
            p[i] += g92_offsets[i];
        }

        if (rotation_xy != 0.0) {
            const double rotx = p[0] * rotation_cos - p[1] * rotation_sin;
            const double roty = p[0] * rotation_sin + p[1] * rotation_cos;
            p[0] = rotx;
            p[1] = roty;
        }

        for (int i = 0; i < 9; ++i) {
            p[i] += g5x_offsets[i];
        }

        return p;
    }

    void add_path_point(std::uint8_t line_type_code, const std::array<double, 9> &start_point, const std::array<double, 9> &end_point) {
        if (py::len(path_segments) == 0) {
            append_segment(active_wcs_index);
        }

        if (native_segments.empty()) {
            NativeSegment native_segment;
            native_segment.wcs_index = active_wcs_index;
            native_segments.push_back(std::move(native_segment));
        }

        auto adjust = [&](const std::array<double, 9> &src, std::array<double, 3> &out) {
            out[0] = src[0] + tool_offsets[0] - active_wcs_initial_x;
            out[1] = src[1] + tool_offsets[1] - active_wcs_initial_y;
            out[2] = src[2] - tool_offsets[2] - active_wcs_initial_z;
        };

        std::array<double, 3> start_xyz{};
        std::array<double, 3> end_xyz{};
        adjust(start_point, start_xyz);
        adjust(end_point, end_xyz);

        if (should_trace_seq() || should_trace_point(start_xyz) || should_trace_point(end_xyz)) {
            std::ostringstream oss;
            oss << "[cpp-trace] add_path_point seq=" << seq_num
                << " line_type=" << static_cast<int>(line_type_code)
                << " active_wcs=" << active_wcs_index
                << " start_z_raw=" << start_point[2]
                << " end_z_raw=" << end_point[2]
                << " tool_z=" << tool_offsets[2]
                << " active_wcs_initial_z=" << active_wcs_initial_z
                << " start_z_adj=" << start_xyz[2]
                << " end_z_adj=" << end_xyz[2];
            trace_debug(oss.str());
        }

        NativeLine native_line;
        native_line.type_code = line_type_code;
        native_line.start = start_xyz;
        native_line.end = end_xyz;
        native_line.rgba = line_type_rgba[static_cast<size_t>(line_type_code)];
        native_segments.back().lines.push_back(std::move(native_line));
    }

    std::array<double, 9> last_pos;
    std::array<double, 9> tool_offsets;
    std::array<double, 9> g92_offsets;
    std::array<double, 9> g5x_offsets;
    double external_length_units{1.0};
    int seq_num{-1};
    int suppress{0};
    int active_wcs_index{0};
    int arcdivision{64};
    bool first_move{true};
    bool in_arc{false};
    bool path_initialized{false};
    int plane{1};
    int axis_mask{0x1FF};
    double feedrate{1.0};
    double dwell_time{0.0};
    double rotation_xy{0.0};
    double rotation_cos{1.0};
    double rotation_sin{0.0};
    double active_wcs_initial_x{0.0};
    double active_wcs_initial_y{0.0};
    double active_wcs_initial_z{0.0};
    std::unordered_map<int, std::array<double, 3>> initial_wcs_offsets_native;
    py::object arc_to_segments_fn;
    py::object trace_logger{py::none()};
    std::vector<NativeSegment> native_segments;
    std::array<std::array<std::uint8_t, 4>, 5> line_type_rgba{{
        std::array<std::uint8_t, 4>{255, 255, 255, 255},
        std::array<std::uint8_t, 4>{0, 255, 0, 255},
        std::array<std::uint8_t, 4>{0, 200, 255, 255},
        std::array<std::uint8_t, 4>{255, 255, 0, 255},
        std::array<std::uint8_t, 4>{255, 0, 255, 255},
    }};
};

static LineTypeInfo decode_line_type(const py::handle &line_type_obj) {
    if (PyLong_Check(line_type_obj.ptr())) {
        const long code = PyLong_AsLong(line_type_obj.ptr());
        if (PyErr_Occurred()) {
            throw py::error_already_set();
        }
        switch (code) {
            case 0: return LineTypeInfo{"traverse", true};
            case 1: return LineTypeInfo{"feed", false};
            case 2: return LineTypeInfo{"arcfeed", false};
            case 3: return LineTypeInfo{"dwell", false};
            case 4: return LineTypeInfo{"user", false};
            default: return LineTypeInfo{"user", false};
        }
    }

    const std::string line_type = py::str(line_type_obj);
    return LineTypeInfo{line_type, line_type == "traverse"};
}

static LinePoints line_points_xyz(const py::handle &line_data, double factor) {
    PyObject *seq = PySequence_Fast(line_data.ptr(), "line data must be a sequence");
    if (seq == nullptr) {
        throw py::error_already_set();
    }

    const auto size = PySequence_Fast_GET_SIZE(seq);
    auto to_double = [](PyObject *obj) -> double {
        const double value = PyFloat_AsDouble(obj);
        if (PyErr_Occurred()) {
            throw py::error_already_set();
        }
        return value;
    };

    LinePoints points{};

    if (size >= 6 && PyNumber_Check(PySequence_Fast_GET_ITEM(seq, 0))) {
        points.start = {
            to_double(PySequence_Fast_GET_ITEM(seq, 0)) * factor,
            to_double(PySequence_Fast_GET_ITEM(seq, 1)) * factor,
            to_double(PySequence_Fast_GET_ITEM(seq, 2)) * factor,
        };
        points.end = {
            to_double(PySequence_Fast_GET_ITEM(seq, 3)) * factor,
            to_double(PySequence_Fast_GET_ITEM(seq, 4)) * factor,
            to_double(PySequence_Fast_GET_ITEM(seq, 5)) * factor,
        };
        Py_DECREF(seq);
        return points;
    }

    if (size < 2) {
        Py_DECREF(seq);
        throw std::runtime_error("line data sequence has fewer than 2 elements");
    }

    py::handle start_point(PySequence_Fast_GET_ITEM(seq, 0));
    py::handle end_point(PySequence_Fast_GET_ITEM(seq, 1));
    points.start = point_xyz(start_point, factor);
    points.end = point_xyz(end_point, factor);
    Py_DECREF(seq);
    return points;
}

static py::array_t<double> make_points_array(const std::vector<double> &points_xyz) {
    const ssize_t point_count = static_cast<ssize_t>(points_xyz.size() / 3);
    py::array_t<double> arr({point_count, static_cast<ssize_t>(3)});
    auto *dst = static_cast<double *>(arr.mutable_data());
    std::copy(points_xyz.begin(), points_xyz.end(), dst);
    return arr;
}

static py::array_t<std::uint8_t> make_colors_array(const std::vector<std::uint8_t> &colors_rgba) {
    const ssize_t color_count = static_cast<ssize_t>(colors_rgba.size() / 4);
    py::array_t<std::uint8_t> arr({color_count, static_cast<ssize_t>(4)});
    auto *dst = static_cast<std::uint8_t *>(arr.mutable_data());
    std::copy(colors_rgba.begin(), colors_rgba.end(), dst);
    return arr;
}

static py::dict build_from_native_canon(NativeCanon &canon, py::object datasource) {
    const bool is_machine_metric = py::bool_(datasource.attr("isMachineMetric")());
    const double multiplication_factor = is_machine_metric ? 25.4 : 1.0;

    const auto &native_segments = canon.native_segments_ref();

    std::unordered_map<int, bool> wcs_seen;
    for (const auto &segment : native_segments) {
        wcs_seen[segment.wcs_index] = true;
    }
    const ssize_t path_actor_count = static_cast<ssize_t>(wcs_seen.size());

    std::optional<int> first_cut_wcs;
    for (const auto &segment : native_segments) {
        for (const auto &line : segment.lines) {
            if (line.type_code != 0) {
                first_cut_wcs = segment.wcs_index;
                break;
            }
        }
        if (first_cut_wcs.has_value()) {
            break;
        }
    }

    const auto t0 = std::chrono::steady_clock::now();

    struct WcsPayloadAccum {
        int wcs_index{0};
        ssize_t segment_count{0};
        std::vector<double> points_xyz;
        std::vector<std::uint8_t> colors_rgba;
    };

    std::vector<WcsPayloadAccum> wcs_accums;
    std::unordered_map<int, size_t> wcs_to_accum_index;
    std::size_t added_segment_count = 0;

    for (const auto &segment : native_segments) {
        const int segment_wcs = segment.wcs_index;
        auto it = wcs_to_accum_index.find(segment_wcs);
        if (it == wcs_to_accum_index.end()) {
            const size_t new_index = wcs_accums.size();
            wcs_to_accum_index.emplace(segment_wcs, new_index);
            wcs_accums.push_back(WcsPayloadAccum{});
            wcs_accums.back().wcs_index = segment_wcs;
            it = wcs_to_accum_index.find(segment_wcs);
        }

        WcsPayloadAccum &acc = wcs_accums[it->second];
        if (acc.points_xyz.capacity() < (acc.points_xyz.size() + segment.lines.size() * 6)) {
            acc.points_xyz.reserve(acc.points_xyz.size() + segment.lines.size() * 6);
        }
        if (acc.colors_rgba.capacity() < (acc.colors_rgba.size() + segment.lines.size() * 4)) {
            acc.colors_rgba.reserve(acc.colors_rgba.size() + segment.lines.size() * 4);
        }

        for (const auto &line : segment.lines) {
            // First traverse in each segment has no provable start point in
            // preview context; skip rendering it as segment geometry.
            if (acc.segment_count == 0 && line.type_code == 0) {
                continue;
            }

            acc.points_xyz.push_back(line.end[0] * multiplication_factor);
            acc.points_xyz.push_back(line.end[1] * multiplication_factor);
            acc.points_xyz.push_back(line.end[2] * multiplication_factor);
            acc.points_xyz.push_back(line.start[0] * multiplication_factor);
            acc.points_xyz.push_back(line.start[1] * multiplication_factor);
            acc.points_xyz.push_back(line.start[2] * multiplication_factor);

            acc.colors_rgba.push_back(line.rgba[0]);
            acc.colors_rgba.push_back(line.rgba[1]);
            acc.colors_rgba.push_back(line.rgba[2]);
            acc.colors_rgba.push_back(line.rgba[3]);

            acc.segment_count += 1;
            added_segment_count += 1;
        }
    }

    py::list wcs_payload;
    for (auto &acc : wcs_accums) {
        py::dict entry;
        entry["wcs_index"] = py::int_(acc.wcs_index);
        entry["segment_count"] = py::int_(acc.segment_count);
        entry["points"] = make_points_array(acc.points_xyz);
        entry["colors"] = make_colors_array(acc.colors_rgba);
        wcs_payload.append(entry);
    }

    py::list offset_transitions;
    if (native_segments.size() > 1) {
        struct SegmentSummary {
            int wcs_index{0};
            std::array<double, 3> start{};
            std::array<double, 3> end{};
            std::array<double, 3> first_cut_start{};
            std::array<double, 3> last_cut_end{};
            bool has_start{false};
            bool has_end{false};
            bool has_cut{false};
            bool has_first_cut_start{false};
            bool has_last_cut_end{false};
        };

        std::vector<SegmentSummary> segment_summaries;
        segment_summaries.reserve(native_segments.size());

        py::object trace_logger = py::none();
        try {
            py::module_ logging = py::module_::import("logging");
            trace_logger = logging.attr("getLogger")("qtpyvcp.native.backplot_cpp.bridge");
        } catch (...) {
            trace_logger = py::none();
        }

        for (const auto &segment : native_segments) {
            SegmentSummary summary;
            summary.wcs_index = segment.wcs_index;

            for (const auto &line : segment.lines) {
                if (!summary.has_start) {
                    summary.start = {
                        line.start[0] * multiplication_factor,
                        line.start[1] * multiplication_factor,
                        line.start[2] * multiplication_factor,
                    };
                    summary.has_start = true;
                }

                summary.end = {
                    line.end[0] * multiplication_factor,
                    line.end[1] * multiplication_factor,
                    line.end[2] * multiplication_factor,
                };
                summary.has_end = true;

                if (line.type_code != 0) {
                    summary.has_cut = true;

                    if (!summary.has_first_cut_start) {
                        summary.first_cut_start = {
                            line.start[0] * multiplication_factor,
                            line.start[1] * multiplication_factor,
                            line.start[2] * multiplication_factor,
                        };
                        summary.has_first_cut_start = true;
                    }

                    summary.last_cut_end = {
                        line.end[0] * multiplication_factor,
                        line.end[1] * multiplication_factor,
                        line.end[2] * multiplication_factor,
                    };
                    summary.has_last_cut_end = true;
                }
            }

            segment_summaries.push_back(summary);
        }

        for (size_t i = 1; i < segment_summaries.size(); ++i) {
            const auto &prev = segment_summaries[i - 1];
            const auto &next = segment_summaries[i];

            if (!prev.has_end || !next.has_start) {
                continue;
            }
            if (!prev.has_cut || !next.has_cut) {
                continue;
            }
            if (prev.wcs_index == next.wcs_index) {
                continue;
            }
            if (prev.wcs_index < 0 || next.wcs_index < 0) {
                continue;
            }

            // Source from the actual end of prior segment (preserves final
            // reposition like G53), but target the first cutting point in the
            // next segment to avoid snapping to an intermediate traverse start.
            const auto &transition_from = prev.end;
            const auto &transition_to = next.has_first_cut_start ? next.first_cut_start : next.start;

            std::array<double, 3> prev_raw_end{0.0, 0.0, 0.0};
            int prev_last_type = -1;
            if (!native_segments[i - 1].lines.empty()) {
                prev_raw_end = native_segments[i - 1].lines.back().end;
                prev_last_type = static_cast<int>(native_segments[i - 1].lines.back().type_code);
            }

            std::array<double, 3> next_raw_start{0.0, 0.0, 0.0};
            int next_first_type = -1;
            if (!native_segments[i].lines.empty()) {
                next_raw_start = native_segments[i].lines.front().start;
                next_first_type = static_cast<int>(native_segments[i].lines.front().type_code);
            }

            py::dict transition;
            transition["from_wcs"] = py::int_(prev.wcs_index);
            transition["to_wcs"] = py::int_(next.wcs_index);
            transition["from_end"] = py::make_tuple(transition_from[0], transition_from[1], transition_from[2]);
            transition["to_start"] = py::make_tuple(transition_to[0], transition_to[1], transition_to[2]);
            transition["debug_mul"] = py::float_(multiplication_factor);
            transition["debug_prev_raw_end"] = py::make_tuple(prev_raw_end[0], prev_raw_end[1], prev_raw_end[2]);
            transition["debug_prev_last_type"] = py::int_(prev_last_type);
            transition["debug_prev_scaled_last_cut_end"] = py::make_tuple(prev.last_cut_end[0], prev.last_cut_end[1], prev.last_cut_end[2]);
            transition["debug_next_raw_start"] = py::make_tuple(next_raw_start[0], next_raw_start[1], next_raw_start[2]);
            transition["debug_next_first_type"] = py::int_(next_first_type);
            transition["debug_next_scaled_first_cut_start"] = py::make_tuple(next.first_cut_start[0], next.first_cut_start[1], next.first_cut_start[2]);
            offset_transitions.append(transition);
        }
    }

    canon.offset_transitions = offset_transitions;
    canon.added_segments = static_cast<int>(added_segment_count);

    const auto t1 = std::chrono::steady_clock::now();
    const auto elapsed_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();

    py::dict result;
    result["wcs_payload"] = wcs_payload;
    result["offset_transitions"] = offset_transitions;
    result["added_segments"] = py::int_(added_segment_count);
    result["draw_ms"] = py::float_(elapsed_ms);
    return result;
}

static py::dict build_from_canon(py::object canon, py::object datasource) {
    if (canon.is_none()) {
        throw std::runtime_error("canon is None");
    }
    if (datasource.is_none()) {
        throw std::runtime_error("datasource is None");
    }

    const bool is_machine_foam = py::bool_(datasource.attr("isMachineFoam")());
    if (is_machine_foam) {
        throw std::runtime_error("C++ bridge non-foam path only (foam falls back to Python)");
    }

    if (py::isinstance<NativeCanon>(canon)) {
        NativeCanon &native_canon = canon.cast<NativeCanon &>();
        return build_from_native_canon(native_canon, datasource);
    }

    const bool is_machine_metric = py::bool_(datasource.attr("isMachineMetric")());
    const double multiplication_factor = is_machine_metric ? 25.4 : 1.0;

    py::list path_segments = canon.attr("path_segments").cast<py::list>();
    py::object path_colors = canon.attr("path_colors");
    std::unordered_map<std::string, std::array<std::uint8_t, 4>> color_cache;

    py::object first_cut_wcs = py::none();
    for (auto segment_obj : path_segments) {
        py::dict segment = segment_obj.cast<py::dict>();
        py::list lines = segment["lines"].cast<py::list>();
        bool has_cut = false;
        for (auto line_obj : lines) {
            py::tuple line_item = line_obj.cast<py::tuple>();
            const auto line_type = decode_line_type(line_item[0]);
            if (!line_type.is_traverse) {
                has_cut = true;
                break;
            }
        }
        if (has_cut) {
            first_cut_wcs = segment["wcs_index"];
            break;
        }
    }

    std::unordered_map<int, bool> wcs_seen;
    for (auto segment_obj : path_segments) {
        py::dict segment = segment_obj.cast<py::dict>();
        const int segment_wcs = py::int_(segment["wcs_index"]);
        wcs_seen[segment_wcs] = true;
    }
    const ssize_t path_actor_count = static_cast<ssize_t>(wcs_seen.size());
    std::size_t added_segment_count = 0;

    const auto t0 = std::chrono::steady_clock::now();

    struct WcsPayloadAccum {
        int wcs_index{0};
        ssize_t segment_count{0};
        std::vector<double> points_xyz;
        std::vector<std::uint8_t> colors_rgba;
    };

    std::vector<WcsPayloadAccum> wcs_accums;
    std::unordered_map<int, size_t> wcs_to_accum_index;

    for (auto segment_obj : path_segments) {
        py::dict segment = segment_obj.cast<py::dict>();
        const int segment_wcs = py::int_(segment["wcs_index"]);
        py::object wcs_key = py::int_(segment_wcs);
        auto it = wcs_to_accum_index.find(segment_wcs);
        if (it == wcs_to_accum_index.end()) {
            const size_t new_index = wcs_accums.size();
            wcs_to_accum_index.emplace(segment_wcs, new_index);
            wcs_accums.push_back(WcsPayloadAccum{});
            wcs_accums.back().wcs_index = segment_wcs;
            it = wcs_to_accum_index.find(segment_wcs);
        }

        WcsPayloadAccum &acc = wcs_accums[it->second];
        py::list lines = segment["lines"].cast<py::list>();
        if (acc.points_xyz.capacity() < (acc.points_xyz.size() + static_cast<size_t>(py::len(lines)) * 6)) {
            acc.points_xyz.reserve(acc.points_xyz.size() + static_cast<size_t>(py::len(lines)) * 6);
        }
        if (acc.colors_rgba.capacity() < (acc.colors_rgba.size() + static_cast<size_t>(py::len(lines)) * 4)) {
            acc.colors_rgba.reserve(acc.colors_rgba.size() + static_cast<size_t>(py::len(lines)) * 4);
        }

        for (auto line_obj : lines) {
            py::tuple line_item = line_obj.cast<py::tuple>();
            const auto line_type = decode_line_type(line_item[0]);
            py::handle line_data = line_item[1];

            if (path_actor_count > 1 && acc.segment_count == 0 && line_type.is_traverse && !first_cut_wcs.is_none() && !py_equals(wcs_key, first_cut_wcs)) {
                continue;
            }

            const auto line_points = line_points_xyz(line_data, multiplication_factor);

            acc.points_xyz.push_back(line_points.end[0]);
            acc.points_xyz.push_back(line_points.end[1]);
            acc.points_xyz.push_back(line_points.end[2]);
            acc.points_xyz.push_back(line_points.start[0]);
            acc.points_xyz.push_back(line_points.start[1]);
            acc.points_xyz.push_back(line_points.start[2]);

            auto color_it = color_cache.find(line_type.color_key);
            if (color_it == color_cache.end()) {
                color_it = color_cache.emplace(line_type.color_key, color_rgba(path_colors, line_type.color_key)).first;
            }
            const auto &rgba = color_it->second;
            acc.colors_rgba.push_back(rgba[0]);
            acc.colors_rgba.push_back(rgba[1]);
            acc.colors_rgba.push_back(rgba[2]);
            acc.colors_rgba.push_back(rgba[3]);

            acc.segment_count += 1;
            added_segment_count += 1;
        }
    }

    py::list wcs_payload;
    for (auto &acc : wcs_accums) {
        py::dict entry;
        entry["wcs_index"] = py::int_(acc.wcs_index);
        entry["segment_count"] = py::int_(acc.segment_count);
        entry["points"] = make_points_array(acc.points_xyz);
        entry["colors"] = make_colors_array(acc.colors_rgba);
        wcs_payload.append(entry);
    }

    py::list offset_transitions;
    if (py::len(path_segments) > 1) {
        struct SegmentSummary {
            py::object wcs_index;
            py::object start;
            py::object end;
            std::array<double, 3> raw_start{};
            std::array<double, 3> raw_end{};
            std::array<double, 3> first_cut_start{};
            std::array<double, 3> last_cut_end{};
            int first_type{-1};
            int last_type{-1};
            bool has_cut{false};
            bool has_raw_start{false};
            bool has_raw_end{false};
            bool has_first_cut_start{false};
            bool has_last_cut_end{false};
        };
        std::vector<SegmentSummary> segment_summaries;
        segment_summaries.reserve(static_cast<size_t>(py::len(path_segments)));

        for (auto segment_obj : path_segments) {
            py::dict segment = segment_obj.cast<py::dict>();
            py::object segment_wcs_index = segment["wcs_index"];
            py::list segment_data = segment["lines"].cast<py::list>();
            py::object segment_start = py::none();
            py::object segment_end = py::none();
            bool segment_has_cut_motion = false;

            for (auto seg_line_obj : segment_data) {
                py::tuple segment_line_item = seg_line_obj.cast<py::tuple>();
                const auto segment_line_type = decode_line_type(segment_line_item[0]);
                py::handle segment_line_data = segment_line_item[1];

                if (!segment_line_type.is_traverse) {
                    segment_has_cut_motion = true;
                }

                const auto line_points = line_points_xyz(segment_line_data, multiplication_factor);

                if (segment_start.is_none()) {
                    segment_start = py::make_tuple(line_points.start[0], line_points.start[1], line_points.start[2]);
                }

                segment_end = py::make_tuple(line_points.end[0], line_points.end[1], line_points.end[2]);
            }

            SegmentSummary summary{};
            summary.wcs_index = segment_wcs_index;
            summary.start = segment_start;
            summary.end = segment_end;
            summary.has_cut = segment_has_cut_motion;

            if (py::len(segment_data) > 0) {
                py::tuple first_line_item = segment_data[0].cast<py::tuple>();
                py::tuple last_line_item = segment_data[py::len(segment_data) - 1].cast<py::tuple>();

                const auto first_raw = line_points_xyz(first_line_item[1], 1.0);
                const auto last_raw = line_points_xyz(last_line_item[1], 1.0);
                summary.raw_start = first_raw.start;
                summary.raw_end = last_raw.end;
                summary.has_raw_start = true;
                summary.has_raw_end = true;

                if (PyLong_Check(first_line_item[0].ptr())) {
                    summary.first_type = static_cast<int>(PyLong_AsLong(first_line_item[0].ptr()));
                }
                if (PyLong_Check(last_line_item[0].ptr())) {
                    summary.last_type = static_cast<int>(PyLong_AsLong(last_line_item[0].ptr()));
                }
            }

            for (auto seg_line_obj : segment_data) {
                py::tuple segment_line_item = seg_line_obj.cast<py::tuple>();
                const auto segment_line_type = decode_line_type(segment_line_item[0]);
                if (segment_line_type.is_traverse) {
                    continue;
                }
                const auto line_points = line_points_xyz(segment_line_item[1], multiplication_factor);
                if (!summary.has_first_cut_start) {
                    summary.first_cut_start = line_points.start;
                    summary.has_first_cut_start = true;
                }
                summary.last_cut_end = line_points.end;
                summary.has_last_cut_end = true;
            }

            segment_summaries.push_back(summary);
        }

        for (size_t i = 1; i < segment_summaries.size(); ++i) {
            const auto &prev = segment_summaries[i - 1];
            const auto &next = segment_summaries[i];

            if (prev.end.is_none() || next.start.is_none()) {
                continue;
            }
            if (!prev.has_cut || !next.has_cut) {
                continue;
            }
            if (py_equals(prev.wcs_index, next.wcs_index)) {
                continue;
            }

            py::dict transition;
            transition["from_wcs"] = prev.wcs_index;
            transition["to_wcs"] = next.wcs_index;
            transition["from_end"] = prev.end;
            transition["to_start"] = next.has_first_cut_start
                ? py::make_tuple(next.first_cut_start[0], next.first_cut_start[1], next.first_cut_start[2])
                : next.start;
            transition["debug_mul"] = py::float_(multiplication_factor);
            if (prev.has_raw_end) {
                transition["debug_prev_raw_end"] = py::make_tuple(prev.raw_end[0], prev.raw_end[1], prev.raw_end[2]);
            }
            transition["debug_prev_last_type"] = py::int_(prev.last_type);
            if (prev.has_last_cut_end) {
                transition["debug_prev_scaled_last_cut_end"] = py::make_tuple(prev.last_cut_end[0], prev.last_cut_end[1], prev.last_cut_end[2]);
            }
            if (next.has_raw_start) {
                transition["debug_next_raw_start"] = py::make_tuple(next.raw_start[0], next.raw_start[1], next.raw_start[2]);
            }
            transition["debug_next_first_type"] = py::int_(next.first_type);
            if (next.has_first_cut_start) {
                transition["debug_next_scaled_first_cut_start"] = py::make_tuple(next.first_cut_start[0], next.first_cut_start[1], next.first_cut_start[2]);
            }
            offset_transitions.append(transition);
        }
    }

    canon.attr("offset_transitions") = offset_transitions;
    canon.attr("added_segments") = py::int_(added_segment_count);

    const auto t1 = std::chrono::steady_clock::now();

    const auto elapsed_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();

    py::dict result;
    result["wcs_payload"] = wcs_payload;
    result["offset_transitions"] = offset_transitions;
    result["added_segments"] = py::int_(added_segment_count);
    result["draw_ms"] = py::float_(elapsed_ms);
    return result;
}

PYBIND11_MODULE(_backplot_cpp, m) {
    m.doc() = "QtPyVCP C++ backplot builder bridge";
    m.def("build_from_canon", &build_from_canon, "Build VTK backplot data from canon stream");
    py::class_<NativeCanon>(m, "NativeCanon")
        .def(py::init<py::object>(), py::arg("path_colors"))
        .def("next_line", &NativeCanon::next_line)
        .def("set_g5x_offset", &NativeCanon::set_g5x_offset)
        .def("set_g92_offset", &NativeCanon::set_g92_offset)
        .def("set_external_length_units", &NativeCanon::set_external_length_units)
        .def("set_xy_rotation", &NativeCanon::set_xy_rotation)
        .def("tool_offset", &NativeCanon::tool_offset)
        .def("straight_traverse", &NativeCanon::straight_traverse)
        .def("straight_feed", &NativeCanon::straight_feed)
        .def("straight_probe", &NativeCanon::straight_probe)
        .def("rigid_tap", &NativeCanon::rigid_tap)
        .def("arc_feed", &NativeCanon::arc_feed)
        .def("straight_arcsegments", &NativeCanon::straight_arcsegments)
        .def("user_defined_function", &NativeCanon::user_defined_function)
        .def("dwell", &NativeCanon::dwell)
        .def("comment", &NativeCanon::comment)
        .def("message", &NativeCanon::message)
        .def("check_abort", &NativeCanon::check_abort)
        .def("set_spindle_rate", &NativeCanon::set_spindle_rate)
        .def("set_feed_rate", &NativeCanon::set_feed_rate)
        .def("set_plane", &NativeCanon::set_plane)
        .def("select_plane", &NativeCanon::select_plane)
        .def("set_feed_mode", &NativeCanon::set_feed_mode)
        .def("set_traverse_rate", &NativeCanon::set_traverse_rate)
        .def("change_tool", &NativeCanon::change_tool)
        .def("get_tool", &NativeCanon::get_tool)
        .def("get_external_angular_units", &NativeCanon::get_external_angular_units)
        .def("get_external_length_units", &NativeCanon::get_external_length_units)
        .def("get_axis_mask", &NativeCanon::get_axis_mask)
        .def("set_axis_mask", &NativeCanon::set_axis_mask)
        .def("get_block_delete", &NativeCanon::get_block_delete)
        .def("calc_extents", &NativeCanon::calc_extents)
        .def_readwrite("path_colors", &NativeCanon::path_colors)
        .def_readwrite("path_segments", &NativeCanon::path_segments)
        .def_readwrite("initial_wcs_offsets", &NativeCanon::initial_wcs_offsets)
        .def_readwrite("offset_transitions", &NativeCanon::offset_transitions)
        .def_readwrite("added_segments", &NativeCanon::added_segments)
        .def_readwrite("parameter_file", &NativeCanon::parameter_file)
        .def_readwrite("lo", &NativeCanon::lo)
        .def_property_readonly("g5x_offset_x", &NativeCanon::get_g5x_offset_x)
        .def_property_readonly("g5x_offset_y", &NativeCanon::get_g5x_offset_y)
        .def_property_readonly("g5x_offset_z", &NativeCanon::get_g5x_offset_z)
        .def_property_readonly("g5x_offset_a", &NativeCanon::get_g5x_offset_a)
        .def_property_readonly("g5x_offset_b", &NativeCanon::get_g5x_offset_b)
        .def_property_readonly("g5x_offset_c", &NativeCanon::get_g5x_offset_c)
        .def_property_readonly("g5x_offset_u", &NativeCanon::get_g5x_offset_u)
        .def_property_readonly("g5x_offset_v", &NativeCanon::get_g5x_offset_v)
        .def_property_readonly("g5x_offset_w", &NativeCanon::get_g5x_offset_w)
        .def_property_readonly("g92_offset_x", &NativeCanon::get_g92_offset_x)
        .def_property_readonly("g92_offset_y", &NativeCanon::get_g92_offset_y)
        .def_property_readonly("g92_offset_z", &NativeCanon::get_g92_offset_z)
        .def_property_readonly("g92_offset_a", &NativeCanon::get_g92_offset_a)
        .def_property_readonly("g92_offset_b", &NativeCanon::get_g92_offset_b)
        .def_property_readonly("g92_offset_c", &NativeCanon::get_g92_offset_c)
        .def_property_readonly("g92_offset_u", &NativeCanon::get_g92_offset_u)
        .def_property_readonly("g92_offset_v", &NativeCanon::get_g92_offset_v)
        .def_property_readonly("g92_offset_w", &NativeCanon::get_g92_offset_w)
        .def_property_readonly("rotation_cos", &NativeCanon::get_rotation_cos)
        .def_property_readonly("rotation_sin", &NativeCanon::get_rotation_sin)
        .def_property_readonly("plane", &NativeCanon::get_plane);
}
