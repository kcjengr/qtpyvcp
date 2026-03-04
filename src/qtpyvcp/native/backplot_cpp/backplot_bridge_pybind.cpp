#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include <chrono>
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

    const bool is_machine_metric = py::bool_(datasource.attr("isMachineMetric")());
    const double multiplication_factor = is_machine_metric ? 25.4 : 1.0;

    py::dict path_actors = canon.attr("path_actors").cast<py::dict>();
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

    const ssize_t path_actor_count = py::len(path_actors);
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
        if (!path_actors.contains(wcs_key)) {
            continue;
        }

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
            bool has_cut{false};
        };
        std::vector<SegmentSummary> segment_summaries;
        segment_summaries.reserve(static_cast<size_t>(py::len(path_segments)));

        ssize_t segment_index = 0;
        for (auto segment_obj : path_segments) {
            py::dict segment = segment_obj.cast<py::dict>();
            py::object segment_wcs_index = segment["wcs_index"];
            py::list segment_data = segment["lines"].cast<py::list>();
            py::object segment_start = py::none();
            py::object segment_end = py::none();
            bool segment_started = false;
            bool segment_has_cut_motion = false;

            for (auto seg_line_obj : segment_data) {
                py::tuple segment_line_item = seg_line_obj.cast<py::tuple>();
                const auto segment_line_type = decode_line_type(segment_line_item[0]);
                py::handle segment_line_data = segment_line_item[1];

                if (!segment_line_type.is_traverse) {
                    segment_has_cut_motion = true;
                }

                if (segment_index > 0 && !segment_started && segment_line_type.is_traverse) {
                    continue;
                }

                segment_started = true;

                const auto line_points = line_points_xyz(segment_line_data, multiplication_factor);

                if (segment_start.is_none()) {
                    segment_start = py::make_tuple(line_points.start[0], line_points.start[1], line_points.start[2]);
                }

                segment_end = py::make_tuple(line_points.end[0], line_points.end[1], line_points.end[2]);
            }

            segment_summaries.push_back(
                SegmentSummary{
                    segment_wcs_index,
                    segment_start,
                    segment_end,
                    segment_has_cut_motion,
                }
            );
            segment_index += 1;
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
            transition["to_start"] = next.start;
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
}
