import time

import vtk

from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)

_MIN_CUT_RADIUS = 0.1
_MIN_CUT_FACTOR = 0.20  # Cut after tool moves ~20% of its radius
_MAX_CUTS_PER_SEC = 10
_COLLISION_CLEARANCE = 0.1  # mm clearance — tool must penetrate stock this far

# Sample-dimension budget: max samples in the largest stock dimension.
# The other two axes are scaled proportionally (clamped to a floor).
_SAMPLE_BUDGET = 110  # global resolution (volume mode = no contour overhead)
_SAMPLE_FLOOR = 5  # minimum samples per axis
_LOCAL_BUDGET = 7  # local high-res (carries all cut detail)
_REFRESH_EVERY = 10  # re-contour every N cuts
_CONSOLIDATE_THRESHOLD = 30  # consolidate sooner — keeps eval fast
_LOCAL_BOX_SCALE = 2.5  # local refine box half-size = tool_radius × this


def _compute_sample_dims(x_len, y_len, z_len, budget):
    """Return (nx, ny_swapped, nz_swapped) proportional to stock size.

    ny_swapped / nz_swapped correspond to the *real* Z / Y axes after the
    Y↔Z swap used by the implicit-function coordinate space.
    """
    lengths = [max(x_len, 1e-6), max(z_len, 1e-6), max(y_len, 1e-6)]
    longest = max(lengths)
    scale = budget / longest
    dims = [max(int(length * scale), _SAMPLE_FLOOR) for length in lengths]
    return dims[0], dims[1], dims[2]  # nx, ny(vtk)=real_Z, nz(vtk)=real_Y


def make_z_cylinder(tx_local, ty_local, tz_local, r, h):
    """Finite cylinder along real Z, mapped to vtkCylinder's Y-axis.

    vtkCylinder defaults to the Y axis, so the coordinate mapping is:
        real_x  → x
        real_z  → y
        real_y  → z
    """
    cyl = vtk.vtkCylinder()
    cyl.SetRadius(r)
    cyl.SetCenter(tx_local, tz_local + h / 2.0, ty_local)

    bottom = vtk.vtkPlane()
    bottom.SetNormal(0, -1, 0)
    bottom.SetOrigin(tx_local, tz_local, 0)

    top = vtk.vtkPlane()
    top.SetNormal(0, 1, 0)
    top.SetOrigin(tx_local, tz_local + h, 0)

    finite = vtk.vtkImplicitBoolean()
    finite.SetOperationTypeToIntersection()
    finite.AddFunction(cyl)
    finite.AddFunction(bottom)
    finite.AddFunction(top)
    return finite


class StockActor(vtk.vtkActor):
    def __init__(self, linuxcncDataSource):
        super(StockActor, self).__init__()

        self._datasource = linuxcncDataSource
        self.stock_position = self._datasource.getActiveWcsOffsets()

        self._stock_origin = (0.0, 0.0, 0.0)
        self._stock_size = (0.0, 0.0, 0.0)

        # --- Implicit geometry ---

        # Stock is a vtkBox (axis-aligned bounding box)
        self._stock_box = vtk.vtkBox()
        self._stock_box.SetBounds(0, 0, 0, 0, 0, 0)

        # Tool union accumulates all finite cylinders
        self._tool_union = vtk.vtkImplicitBoolean()
        self._tool_union.SetOperationTypeToUnion()

        # Boolean difference: stock - tool_union.
        # Do NOT add the empty _tool_union here — an empty vtkImplicitBoolean
        # evaluates to 0, which would clamp signed distances inside the stock
        # to 0 and prevent the contour filter from finding a clean surface.
        self._boolean = vtk.vtkImplicitBoolean()
        self._boolean.SetOperationTypeToDifference()
        self._boolean.AddFunction(self._stock_box)

        # --- State ---
        self._last_cut_position = None
        self._last_cut_time = -999.0
        self._cutting_enabled = False
        self._in_collision = False
        self._cut_count = 0
        self._tool_union_attached = False  # lazily added on first cut
        self._union_function_count = 0  # tracked for consolidation threshold

        # --- Low-resolution pipeline (used during cutting) ---
        self._sample_lo = vtk.vtkSampleFunction()
        self._sample_lo.SetImplicitFunction(self._boolean)
        self._sample_lo.SetSampleDimensions(30, 30, 5)

        self._contour_lo = vtk.vtkFlyingEdges3D()
        self._contour_lo.SetInputConnection(self._sample_lo.GetOutputPort())
        self._contour_lo.SetValue(0, 0.0)

        # Remove degenerate polygons and duplicate points created by
        # marching cubes before smoothing — prevents rendering artifacts.
        self._clean_lo = vtk.vtkCleanPolyData()
        self._clean_lo.SetInputConnection(self._contour_lo.GetOutputPort())

        # Smooth stair-stepping artifacts from voxelization. 3 iterations
        # at low relaxation rounds the jagged cut edges without blurring
        # the stock silhouette. FeatureEdgeSmoothing preserves the sharp
        # outer-box corners against excessive rounding.
        self._smooth_lo = vtk.vtkSmoothPolyDataFilter()
        self._smooth_lo.SetInputConnection(self._clean_lo.GetOutputPort())
        self._smooth_lo.SetNumberOfIterations(3)
        self._smooth_lo.SetRelaxationFactor(0.05)
        self._smooth_lo.FeatureEdgeSmoothingOn()
        self._smooth_lo.BoundarySmoothingOff()

        self._normals_lo = vtk.vtkPolyDataNormals()
        self._normals_lo.SetInputConnection(self._smooth_lo.GetOutputPort())
        self._normals_lo.SetFeatureAngle(18.0)

        # Un-swap the Y↔Z coordinate mapping introduced by the implicit
        # function space (vtkCylinder defaults to Y-axis).  Without this
        # the mesh renders with Y and Z swapped — a 90° X-axis rotation.
        # Scale(1,1,-1) then RotateX(-90) → maps (x, z, y) back to (x, y, z).
        self._unswap_lo = vtk.vtkTransformPolyDataFilter()
        self._unswap_lo.SetInputConnection(self._normals_lo.GetOutputPort())
        unswap_t = vtk.vtkTransform()
        unswap_t.Scale(1.0, 1.0, -1.0)
        unswap_t.RotateX(-90.0)
        self._unswap_lo.SetTransform(unswap_t)

        self._mapper_lo = vtk.vtkPolyDataMapper()
        self._mapper_lo.SetInputConnection(self._unswap_lo.GetOutputPort())
        self._mapper_lo.ScalarVisibilityOff()

        # --- Local high-res refinement pipeline ---
        # Samples a small volume around the tool at higher resolution and
        # overlays it on the global mesh for crisp cut edges. Both the global
        # and local meshes sample the same implicit function, so they are
        # coincident — any z-fighting is invisible with shared colour/opacity.
        self._local_sample = vtk.vtkSampleFunction()
        self._local_sample.SetImplicitFunction(self._boolean)
        self._local_sample.SetSampleDimensions(
            _LOCAL_BUDGET, _LOCAL_BUDGET, _LOCAL_BUDGET
        )

        self._local_contour = vtk.vtkFlyingEdges3D()
        self._local_contour.SetInputConnection(self._local_sample.GetOutputPort())
        self._local_contour.SetValue(0, 0.0)

        # Same unswap transform as the global pipeline
        self._local_unswap = vtk.vtkTransformPolyDataFilter()
        self._local_unswap.SetInputConnection(self._local_contour.GetOutputPort())
        local_unswap_t = vtk.vtkTransform()
        local_unswap_t.Scale(1.0, 1.0, -1.0)
        local_unswap_t.RotateX(-90.0)
        self._local_unswap.SetTransform(local_unswap_t)

        # Append global mesh + local high-res overlay.
        # Wired into mapper only when refinement is active.
        self._append = vtk.vtkAppendPolyData()
        self._append.AddInputConnection(self._unswap_lo.GetOutputPort())
        self._append.AddInputConnection(self._local_unswap.GetOutputPort())

        self._local_refine_active = False
        self._last_refine_position = None
        self._local_bbox = None  # (min_xyz, max_xyz) in normal local space

        # Start with the mapper and set shiny metal material appearance.
        # Colour is set here (blue) and toggled to red by the caller on collision.
        self.SetMapper(self._mapper_lo)
        self.GetProperty().SetColor(0.62, 0.64, 0.68)  # clear grey
        self.GetProperty().SetOpacity(1.0)
        # Metallic surface: moderate ambient and diffuse for good visibility
        # through the transparency, with a tight specular highlight for shine.
        self.GetProperty().SetAmbient(0.50)
        self.GetProperty().SetDiffuse(0.50)
        self.GetProperty().SetSpecular(0.60)
        self.GetProperty().SetSpecularPower(80.0)

        # --- Volume rendering pipeline (alternative to mesh) ---
        # Renders the sampled SDF grid directly as a 3D texture on the GPU,
        # skipping contour extraction, smoothing, normals, and unswap.
        self._use_volume = True

        self._volume_mapper = vtk.vtkSmartVolumeMapper()
        self._volume_mapper.SetInputConnection(self._sample_lo.GetOutputPort())

        # Transfer function: inside stock = opaque grey, outside = transparent.
        # SDF convention: negative = inside remaining stock, positive = outside.
        opacity_tf = vtk.vtkPiecewiseFunction()
        opacity_tf.AddPoint(-500.0, 0.8)  # deep inside: opaque
        opacity_tf.AddPoint(-0.5, 0.8)  # near surface: opaque
        opacity_tf.AddPoint(0.0, 0.35)  # on surface: semi-transparent
        opacity_tf.AddPoint(0.5, 0.0)  # just outside: transparent
        opacity_tf.AddPoint(500.0, 0.0)  # far outside: transparent

        color_tf = vtk.vtkColorTransferFunction()
        color_tf.AddRGBPoint(-500.0, 0.62, 0.64, 0.68)
        color_tf.AddRGBPoint(500.0, 0.62, 0.64, 0.68)

        self._volume_property = vtk.vtkVolumeProperty()
        self._volume_property.SetScalarOpacity(opacity_tf)
        self._volume_property.SetColor(color_tf)
        self._volume_property.SetInterpolationTypeToLinear()
        self._volume_property.ShadeOn()
        self._volume_property.SetAmbient(0.50)
        self._volume_property.SetDiffuse(0.50)
        self._volume_property.SetSpecular(0.60)
        self._volume_property.SetSpecularPower(80.0)

        self._volume = vtk.vtkVolume()
        self._volume.SetMapper(self._volume_mapper)
        self._volume.SetProperty(self._volume_property)
        self._volume.SetVisibility(0)  # hidden by default

        # Combined transform: unswap(Y↔Z) → UserTransform(rotation/translation).
        # The sample data is in implicit space; this chain maps to world.
        self._volume_transform = vtk.vtkTransform()
        self._volume_transform.Scale(1.0, 1.0, -1.0)
        self._volume_transform.RotateX(-90.0)
        self._volume.SetUserTransform(self._volume_transform)

        # --- Transform for WCS positioning ---
        self._transform = vtk.vtkTransform()
        self._transform.Translate(
            self.stock_position[0], self.stock_position[1], self.stock_position[2]
        )
        self._transform.RotateX(self.stock_position[3])
        self._transform.RotateY(self.stock_position[5])
        self._transform.RotateZ(self.stock_position[4])
        self._transform.Translate(
            -self.stock_position[0], -self.stock_position[1], -self.stock_position[2]
        )

        self.SetUserTransform(self._transform)
        self.SetPosition(
            self.stock_position[0], self.stock_position[1], self.stock_position[2]
        )

        self._datasource.g5xOffsetChanged.connect(self.set_position)
        self._datasource.stockUpdated.connect(self.update_data)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_data(self, stock):
        size = stock.get("stock_size")
        origin = stock.get("stock_origin")

        x_orig = origin.get("x") if origin else 0.0
        y_orig = origin.get("y") if origin else 0.0
        z_orig = origin.get("z") if origin else 0.0
        x_length = size.get("x") if size else 0.0
        y_length = size.get("y") if size else 0.0
        z_length = size.get("z") if size else 0.0

        if not any([x_length, y_length, z_length]):
            LOG.debug("StockActor: no stock data provided – keeping default")
            self._cutting_enabled = False
            return

        self._stock_origin = (x_orig, y_orig, z_orig)
        self._stock_size = (x_length, y_length, z_length)

        # Set stock box bounds (center + size → min/max)
        x_min = x_orig - x_length / 2.0
        x_max = x_orig + x_length / 2.0
        y_min = y_orig - y_length / 2.0
        y_max = y_orig + y_length / 2.0
        z_min = z_orig - z_length / 2.0
        z_max = z_orig + z_length / 2.0
        # Swap Y↔Z bounds to match the implicit function coordinate space
        # (vtkCylinder defaults to Y-axis; see make_z_cylinder).
        self._stock_box.SetBounds(x_min, x_max, z_min, z_max, y_min, y_max)

        # Sample bounds must extend slightly beyond the box surface so the
        # contour filter sees clean sign changes (outside positive, inside
        # negative) rather than sample points landing exactly at value 0.
        pad_x = max(x_length * 0.02, 0.5)
        pad_y = max(y_length * 0.02, 0.5)
        pad_z = max(z_length * 0.02, 0.5)

        # Compute sample dimensions proportional to the stock aspect ratio
        # so every axis gets balanced resolution (no single-axis starvation).
        dims = _compute_sample_dims(x_length, y_length, z_length, _SAMPLE_BUDGET)
        self._sample_lo.SetSampleDimensions(*dims)

        # Set sample grid bounds with Y↔Z swap to match the rotated implicit space:
        #   Real bounds:  X[lo,hi], Y[lo,hi], Z[lo,hi]
        #   Sample bounds: X[lo,hi], Z[lo,hi], Y[lo,hi]
        self._sample_lo.SetModelBounds(
            x_min - pad_x,
            x_max + pad_x,
            z_min - pad_z,
            z_max + pad_z,
            y_min - pad_y,
            y_max + pad_y,
        )
        self._sample_lo.Update()

        # Build initial contour
        self._contour_lo.Update()
        self._smooth_lo.Update()
        self._normals_lo.Update()
        self._unswap_lo.Update()
        self._mapper_lo.Update()

        self._cutting_enabled = True
        self._last_cut_position = None
        self._in_collision = False

    def set_position(self, position):
        self.stock_position = position
        t = vtk.vtkTransform()
        t.Translate(position[0], position[1], position[2])
        t.RotateX(position[3])
        t.RotateY(position[5])
        t.RotateZ(position[4])
        t.Translate(-position[0], -position[1], -position[2])
        self._transform.DeepCopy(t)
        self.SetPosition(position[0], position[1], position[2])

        # Sync volume: unswap(Y↔Z) → UserTransform → Position
        self._volume_transform.Identity()
        self._volume_transform.Scale(1.0, 1.0, -1.0)
        self._volume_transform.RotateX(-90.0)
        self._volume_transform.Concatenate(t)
        self._volume.SetPosition(position[0], position[1], position[2])
        self._volume.SetUserTransform(self._volume_transform)

    def get_source(self):
        return self._stock_box

    def get_volume(self):
        """Return the companion vtkVolume for GPU volume rendering.

        The caller must add this to the renderer alongside the StockActor.
        """
        return self._volume

    def set_use_volume(self, use):
        """Toggle between mesh (polydata) and volume rendering modes.

        In volume mode the global + local mesh pipelines are hidden and
        the sampled SDF grid is rendered directly as a 3D texture.
        """
        self._use_volume = use
        self.SetVisibility(not use)  # mesh actor hidden when volume
        self._volume.SetVisibility(use)  # volume shown when active

    # ------------------------------------------------------------------
    # Collision detection
    # ------------------------------------------------------------------

    def check_collision(
        self, tool_position: tuple, tool_radius: float, tool_height: float
    ) -> bool:
        if not self._cutting_enabled:
            self._in_collision = False
            return False

        tx, ty, tz = (
            float(tool_position[0]),
            float(tool_position[1]),
            float(tool_position[2]),
        )
        r = max(float(tool_radius), _MIN_CUT_RADIUS)
        h = max(float(tool_height), r * 2.0)

        # Get stock bounds in world coordinates (broad-phase reject)
        bounds = self.GetBounds()
        if bounds is None or len(bounds) < 6:
            self._in_collision = False
            return False

        sx_min, sx_max, sy_min, sy_max, sz_min, sz_max = bounds
        cylinder_bottom = tz
        cylinder_top = tz + h

        # Quick AABB reject — avoids expensive signed-distance eval when
        # the tool is nowhere near the stock volume.
        overlap = (
            (tx - r) <= sx_max
            and (tx + r) >= sx_min
            and (ty - r) <= sy_max
            and (ty + r) >= sy_min
            and cylinder_top >= sz_min
            and cylinder_bottom <= sz_max
        )

        if not overlap:
            if self._in_collision:
                LOG.debug("StockActor: collision cleared")
            self._in_collision = False
            self._last_cut_position = None
            return False

        # Narrow-phase: Only check SDF when NOT already in a cutting session.
        # Once cutting has started, the throttle (distance + rate) controls
        # cut placement — not the SDF.  Blocking cuts mid-session because the
        # tool center drifts over already-carved space would leave uncut
        # material at the tool edges.
        if not self._in_collision:
            # Tool is near stock but not currently cutting. Evaluate SDF at
            # the tool center — but gate on tool radius, not zero: if the
            # center is less than one radius from the remaining-stock
            # surface, the tool edge still reaches fresh material.
            local_pos = self._world_to_local((tx, ty, tz))
            # IMPORTANT: implicit functions use Y↔Z swapped space.
            local_imp = (local_pos[0], local_pos[2], local_pos[1])
            sdf = self._boolean.EvaluateFunction(list(local_imp))
            if sdf >= r - _COLLISION_CLEARANCE:
                return False
            # Fresh contact — reset meta counters so the new session
            # begins with an immediate contour refresh.
            LOG.debug(
                "StockActor: new contact at (%.3f, %.3f, %.3f) SDF=%.2f",
                tx,
                ty,
                tz,
                sdf,
            )
            self._cut_count = 0
            self._local_bbox = None  # start fresh bounding box for new session

        # Apply cut (throttled internally)
        self._apply_cut((tx, ty, tz), r, h)
        self._in_collision = True
        return True

    # ------------------------------------------------------------------
    # Cut application
    # ------------------------------------------------------------------

    def _apply_cut(self, world_pos, radius, height):
        """Place a cylindrical cut in the stock, with movement and rate throttling.

        world_pos is in world coordinates; it is converted to model (local)
        coordinates for the implicit function space.
        """
        now = time.time()
        dt = now - self._last_cut_time

        # Convert world position to stock-local (model) coordinates
        local_pos = self._world_to_local(world_pos)
        tx, ty, tz = local_pos

        # Decide whether to cut
        do_cut = False

        if self._last_cut_position is None:
            # First cut of this contact — always apply
            do_cut = True
        else:
            # During collision: cut when tool has moved enough and rate permits
            lx, ly, lz = self._last_cut_position
            dx = tx - lx
            dy = ty - ly
            dz = tz - lz
            dist = (dx * dx + dy * dy + dz * dz) ** 0.5
            cut_threshold = max(radius * _MIN_CUT_FACTOR, _MIN_CUT_RADIUS * 0.1)
            min_interval = 1.0 / _MAX_CUTS_PER_SEC

            if dist >= cut_threshold and dt >= min_interval:
                do_cut = True

        if not do_cut:
            return

        # Build a finite cylinder at the tool position in model space
        cylinder = make_z_cylinder(tx, ty, tz, radius, height)
        self._tool_union.AddFunction(cylinder)
        self._union_function_count += 1

        # First cut: attach the (now non-empty) tool_union to the boolean
        # so it participates in the signed-distance difference.
        if not self._tool_union_attached:
            self._boolean.AddFunction(self._tool_union)
            self._tool_union_attached = True

        # Consolidate accumulated cuts when the union grows too large.
        # Each cylinder adds 1 function; evaluating hundreds per sample point
        # kills performance.  Baking into a single vtkImplicitDataSet keeps
        # the eval cost constant regardless of total cut history.
        if self._union_function_count >= _CONSOLIDATE_THRESHOLD:
            self._consolidate_cuts()

        self._last_cut_position = (tx, ty, tz)
        self._last_cut_time = now
        self._cut_count += 1

        # Update local refinement box (mesh mode only)
        if not self._use_volume:
            self._update_local_refine(world_pos, radius, height)

        # Ensure the first cut of a contact is visible immediately;
        # thereafter rebuild the contour every N cuts.
        if self._cut_count == 1 or self._cut_count % _REFRESH_EVERY == 0:
            self._rebuild_contour()

    def _update_local_refine(self, world_pos, radius, height):
        """Expand the local high-res refinement volume to include the tool.

        Accumulates a bounding box over all cut positions in the current
        cutting session, so the high-res window covers the entire recent
        cut path — not just the tool tip.
        """
        local_pos = self._world_to_local(world_pos)
        lx, ly, lz = local_pos

        margin_xy = radius * _LOCAL_BOX_SCALE
        margin_z = max(radius * _LOCAL_BOX_SCALE * 0.5, radius)

        # Expand the tracked bounding box
        if self._local_bbox is None:
            self._local_bbox = (
                (lx - margin_xy, ly - margin_xy, lz - margin_z),
                (lx + margin_xy, ly + margin_xy, lz + margin_z),
            )
        else:
            bb_min, bb_max = self._local_bbox
            bb_min = (
                min(bb_min[0], lx - margin_xy),
                min(bb_min[1], ly - margin_xy),
                min(bb_min[2], lz - margin_z),
            )
            bb_max = (
                max(bb_max[0], lx + margin_xy),
                max(bb_max[1], ly + margin_xy),
                max(bb_max[2], lz + margin_z),
            )
            self._local_bbox = (bb_min, bb_max)

        bb_min, bb_max = self._local_bbox

        # Compute proportional dimensions for the local bbox shape
        ext_x = bb_max[0] - bb_min[0]
        ext_y = bb_max[1] - bb_min[1]
        ext_z = bb_max[2] - bb_min[2]
        loc_dims = _compute_sample_dims(ext_x, ext_y, ext_z, _LOCAL_BUDGET)
        self._local_sample.SetSampleDimensions(loc_dims[0], loc_dims[1], loc_dims[2])

        # Local sample bounds in IMPLICIT space (Y↔Z swapped)
        self._local_sample.SetModelBounds(
            bb_min[0],
            bb_max[0],  # X
            bb_min[2],
            bb_max[2],  # real Z → VTK Y
            bb_min[1],
            bb_max[1],  # real Y → VTK Z
        )

        self._last_refine_position = local_pos

        # Switch mapper to the append pipeline on first activation
        if not self._local_refine_active:
            self._mapper_lo.SetInputConnection(self._append.GetOutputPort())
        self._local_refine_active = True

    def _rebuild_contour(self):
        """Re-sample the implicit boolean and rebuild the display surface."""
        if not self._cutting_enabled:
            return
        self._sample_lo.Modified()
        self._sample_lo.Update()

        if self._use_volume:
            # Volume mode: skip mesh pipeline entirely.
            # The volume mapper reads from _sample_lo and renders on GPU.
            self._volume_mapper.Update()
            if self._cut_count > 0:
                LOG.debug(
                    "StockActor: volume rebuilt — %d cuts, union functions: %d",
                    self._cut_count,
                    self._union_function_count,
                )
            return

        # Mesh mode: full polydata pipeline
        self._contour_lo.Update()
        self._clean_lo.Update()
        self._smooth_lo.Update()
        self._normals_lo.Update()
        self._unswap_lo.Update()

        # Update local high-res refinement if active
        if self._local_refine_active:
            self._local_sample.Update()
            self._local_contour.Update()
            self._local_unswap.Update()
            self._append.Update()
        self._mapper_lo.Update()
        if self._cut_count > 0:
            LOG.debug(
                "StockActor: contour rebuilt — %d cuts, union functions: %d",
                self._cut_count,
                self._union_function_count,
            )

    def _consolidate_cuts(self):
        """Bake accumulated tool cylinders into a single vtkImplicitDataSet.

        Sampling hundreds of cylinders per voxel gets exponentially slower.
        This samples the current tool_union once onto a grid and replaces it
        with a single fast-lookup implicit dataset — making the eval cost
        constant regardless of total cut history.
        """
        LOG.debug(
            "StockActor: consolidating %d tool functions", self._union_function_count
        )

        # Sample the OLD tool_union *before* we replace it.  The tool_union
        # uses the standard implicit convention (negative=inside, positive=
        # outside) so the baked values have the correct sign for reuse as a
        # tool function in the next round of cuts.
        old_tool_union = self._tool_union

        bake = vtk.vtkSampleFunction()
        bake.SetImplicitFunction(old_tool_union)
        bake.SetModelBounds(self._sample_lo.GetModelBounds())
        # Use the same sample dimensions as the display pipeline so the
        # baked dataset preserves the current level of detail.
        dims = self._sample_lo.GetSampleDimensions()
        bake.SetSampleDimensions(dims[0], dims[1], dims[2])
        bake.Update()

        # Wrap the sampled volume as a fast-lookup implicit function.
        # Points outside the volume return a large positive value (outside tool).
        baked = vtk.vtkImplicitDataSet()
        baked.SetDataSet(bake.GetOutput())
        baked.SetOutValue(1e6)

        # Replace tool_union with just the baked result
        self._tool_union = vtk.vtkImplicitBoolean()
        self._tool_union.SetOperationTypeToUnion()
        self._tool_union.AddFunction(baked)

        # Rebuild the boolean: stock - (baked_cuts ∪ future cylinders)
        self._boolean = vtk.vtkImplicitBoolean()
        self._boolean.SetOperationTypeToDifference()
        self._boolean.AddFunction(self._stock_box)
        self._boolean.AddFunction(self._tool_union)

        # Re-point the sample functions to the fresh boolean
        self._sample_lo.SetImplicitFunction(self._boolean)
        self._local_sample.SetImplicitFunction(self._boolean)

        self._tool_union_attached = True
        self._union_function_count = 0
        # Keep _local_bbox alive — do NOT reset. The local high-res
        # refinement continues to cover the expanding cut area so detail
        # persists across consolidations.

    def _world_to_local(self, world_pos):
        """Convert a world-space position to the stock's model coordinate space.

        The implicit functions (_stock_box, _tool_union, _boolean) operate in
        model space — before the actor's UserTransform and Position are applied.
        """
        matrix = self.GetMatrix()
        inv = vtk.vtkTransform()
        inv.SetMatrix(matrix)
        inv.Inverse()
        return inv.TransformPoint(world_pos)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset_cut(self):
        """Remove all accumulated cuts and restore the uncut stock."""
        # Replace both the union and the boolean with fresh instances.
        # We avoid RemoveAllFunctions() for cross-VTK-version compatibility.
        self._tool_union = vtk.vtkImplicitBoolean()
        self._tool_union.SetOperationTypeToUnion()

        # Rebuild the boolean with only the stock box; the tool_union is now
        # empty and must NOT be added (see init comment).
        self._boolean = vtk.vtkImplicitBoolean()
        self._boolean.SetOperationTypeToDifference()
        self._boolean.AddFunction(self._stock_box)

        # Re-point the sample functions to the fresh boolean
        self._sample_lo.SetImplicitFunction(self._boolean)
        self._local_sample.SetImplicitFunction(self._boolean)

        self._last_cut_position = None
        self._cut_count = 0
        self._in_collision = False
        self._tool_union_attached = False
        self._union_function_count = 0
        self._local_refine_active = False
        self._last_refine_position = None
        self._local_bbox = None
        self._mapper_lo.SetInputConnection(self._unswap_lo.GetOutputPort())
        self.SetMapper(self._mapper_lo)
        self._rebuild_contour()
        self.Modified()
