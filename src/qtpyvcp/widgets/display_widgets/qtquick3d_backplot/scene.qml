import QtQuick
import QtQuick3D

Item {
    id: root
    objectName: "quick3DBackplotRoot"
    width: 640
    height: 480

    // Greedy 2D label declutter. Overlapping labels (coincident WCS origins or
    // dense tick values) are pushed down until they no longer collide. Runs
    // after the camera/viewport projection changes and after a model reset.
    function declutterLabels(repeater) {
        if (!repeater)
            return
        var items = []
        for (var i = 0; i < repeater.count; i++) {
            var item = repeater.itemAt(i)
            if (item && item.visible)
                items.push(item)
        }
        items.sort(function (a, b) { return a.screenPos.y - b.screenPos.y })
        var placed = []
        for (var j = 0; j < items.length; j++) {
            var entry = items[j]
            var baseY = entry.screenPos.y - entry.height - 8
            var x = entry.screenPos.x - entry.width / 2
            var y = baseY
            var moved = true
            var guard = 0
            while (moved && guard++ < 16) {
                moved = false
                for (var k = 0; k < placed.length; k++) {
                    var other = placed[k]
                    if (x < other.x + other.w && x + entry.width > other.x
                            && y < other.y + other.h && y + entry.height > other.y) {
                        y = other.y + other.h + 2
                        moved = true
                    }
                }
            }
            entry.stackOffset = y - baseY
            placed.push({ x: x, y: y, w: entry.width, h: entry.height })
        }
    }
    function declutterAll() {
        declutterLabels(wcsLabelRepeater)
        declutterLabels(machineTickRepeater)
        declutterLabels(programTickRepeater)
    }
    Connections {
        target: plotData
        function onCameraChanged() { Qt.callLater(root.declutterAll) }
    }
    Connections {
        target: (typeof wcsOrigins !== "undefined") ? wcsOrigins : null
        function onModelReset() { Qt.callLater(root.declutterAll) }
    }
    Connections {
        target: (typeof machineTickLabels !== "undefined") ? machineTickLabels : null
        function onModelReset() { Qt.callLater(root.declutterAll) }
    }
    Connections {
        target: (typeof programTickLabels !== "undefined") ? programTickLabels : null
        function onModelReset() { Qt.callLater(root.declutterAll) }
    }
    Component.onCompleted: Qt.callLater(root.declutterAll)

    // Two-colour background. The View3D renders
    // with a transparent clear so this gradient shows through; setting both
    // colours equal gives the old solid background.
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: plotData.backgroundColor2 }
            GradientStop { position: 1.0; color: plotData.backgroundColor }
        }
    }

    View3D {
        id: view3d
        objectName: "backplotView3D"
        anchors.fill: parent
        camera: plotData.perspective ? perspectiveCamera : orthographicCamera

        environment: SceneEnvironment {
            clearColor: "transparent"
            backgroundMode: SceneEnvironment.Transparent
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
            // Screen-space ambient occlusion adds contact shading around the
            // tool, spindle and machine parts so they do not look flat.
            aoEnabled: true
            aoStrength: 70
            aoDistance: 20
            aoSoftness: 50
            aoSampleRate: 2
            aoDither: true
            aoBias: 0.1
        }

        // Solid meshes (tool, machine parts) are lit; path lines stay unlit.
        // A key light plus a soft fill avoid the flat, over-bright look.
        DirectionalLight {
            eulerRotation: Qt.vector3d(-50, -40, 0)
            brightness: 0.9
            castsShadow: false
        }
        DirectionalLight {
            eulerRotation: Qt.vector3d(20, 150, 0)
            brightness: 0.35
            castsShadow: false
        }
        // Camera-follow fill: without this, surfaces facing the operator can
        // fall outside both fixed key lights and render almost black.
        DirectionalLight {
            parent: view3d.camera
            brightness: 0.28
            color: "#dbe6ff"
            castsShadow: false
        }

        PerspectiveCamera {
            id: perspectiveCamera
            objectName: "perspectiveCamera"
            clipNear: 0.01
            clipFar: 1000000
            fieldOfView: 35
        }

        OrthographicCamera {
            id: orthographicCamera
            objectName: "orthographicCamera"
            clipNear: 0.01
            clipFar: 1000000
            horizontalMagnification: plotData.orthoMagnification
            verticalMagnification: plotData.orthoMagnification
        }

        // Program paths: one Model per (WCS, motion role). Geometry stays in
        // WCS-local coordinates; the row's pos/rot carries the work offset, so
        // editing an offset never re-uploads vertex data.
        Repeater3D {
            model: (typeof pathGroups !== "undefined") ? pathGroups : null
            delegate: Model {
                objectName: "pathGroup"
                geometry: model.geometry
                position: model.pos
                rotation: model.rot
                pickable: false
                materials: [ PrincipledMaterial { baseColor: model.col; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
            }
        }

        // Line geometry has no normals, so every material is unlit
        // (PrincipledMaterial.NoLighting) to keep its base color exact.
        Model {
            geometry: plotData.grid
            visible: plotData.gridVisible
            pickable: false
            materials: [ PrincipledMaterial { baseColor: plotData.gridColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.axesX
            pickable: false
            materials: [ PrincipledMaterial { baseColor: plotData.axesXColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.axesY
            pickable: false
            materials: [ PrincipledMaterial { baseColor: plotData.axesYColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.axesZ
            pickable: false
            materials: [ PrincipledMaterial { baseColor: plotData.axesZColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.machineBounds
            visible: plotData.machineBoundsVisible
            pickable: false
            materials: [ PrincipledMaterial { baseColor: plotData.boundsColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.programBounds
            visible: plotData.programBoundsVisible
            pickable: false
            materials: [ PrincipledMaterial { baseColor: plotData.boundsColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.machineTicks
            visible: plotData.machineTicksVisible
            pickable: false
            materials: [ PrincipledMaterial { baseColor: plotData.boundsColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.programTicks
            visible: plotData.programTicksVisible && plotData.programBoundsVisible
            pickable: false
            materials: [ PrincipledMaterial { baseColor: plotData.boundsColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.transitions
            pickable: false
            materials: [ PrincipledMaterial { baseColor: plotData.transitionColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.origins
            visible: plotData.wcsOriginsVisible
            pickable: false
            materials: [ PrincipledMaterial { baseColor: plotData.wcsOriginColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.trail
            visible: plotData.trailVisible
            pickable: false
            materials: [ PrincipledMaterial { baseColor: plotData.trailColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.highlight
            pickable: false
            materials: [ PrincipledMaterial { baseColor: plotData.highlightColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }

        // Machine assembly (MACHINE_PARTS). Parts are flat Models fed by the
        // machineParts list model; world transforms are composed in Python.
        Node {
            visible: plotData.machineVisible
            Repeater3D {
                model: (typeof machineParts !== "undefined") ? machineParts : null
                delegate: Model {
                    objectName: "machinePart"
                    geometry: model.geometry ? model.geometry : null
                    source: model.sourceUrl
                    position: model.pos
                    rotation: model.rot
                    visible: model.vis
                    pickable: false
                    materials: [ PrincipledMaterial { baseColor: model.col; roughness: 0.7; metalness: 0.0 } ]
                }
            }
        }

        // Active tool body, sized from the QtPyVCP tool table. The built-in
        // primitives are 100 units tall/diameter, so toolScale maps radius and
        // length onto them.
        Model {
            source: "#Cylinder"
            visible: plotData.toolVisible && plotData.toolKind === "cylinder"
            position: plotData.toolPosition
            scale: plotData.toolScale
            pickable: false
            materials: [ PrincipledMaterial { baseColor: plotData.toolColor; roughness: 0.5; metalness: 0.1 } ]
        }
        Model {
            source: "#Cone"
            visible: plotData.toolVisible && plotData.toolKind === "cone"
            position: plotData.toolPosition
            scale: plotData.toolScale
            eulerRotation: Qt.vector3d(180, 0, 0)
            pickable: false
            materials: [ PrincipledMaterial { baseColor: plotData.toolColor; roughness: 0.5; metalness: 0.1 } ]
        }
        // Lathe insert silhouette or per-tool STL/glTF model. Both are built
        // in tip-relative coordinates, so the live tool position needs no
        // body-centre offset.
        Model {
            objectName: "toolMeshModel"
            geometry: plotData.toolMesh
            visible: plotData.toolVisible
                     && (plotData.toolKind === "insert" || plotData.toolKind === "mesh")
            position: plotData.toolPosition
            pickable: false
            materials: [ PrincipledMaterial {
                baseColor: plotData.toolColor
                roughness: 0.45
                metalness: 0.2
                cullMode: Material.NoCulling
            } ]
        }
    }

    // Work-offset labels. These are 2D overlays projected through the View3D
    // so they stay readable at any zoom and always face the operator. The
    // cameraRevision dependency makes the projection re-evaluate on orbit,
    // pan, zoom and projection changes.
    Repeater {
        id: wcsLabelRepeater
        model: (typeof wcsOrigins !== "undefined") ? wcsOrigins : null
        onCountChanged: Qt.callLater(root.declutterAll)
        delegate: Text {
            objectName: "wcsOriginLabel"
            property vector3d anchor: model.pos
            property real stackOffset: 0
            property vector3d screenPos: {
                plotData.cameraRevision
                view3d.width
                view3d.height
                return view3d.mapFrom3DScene(anchor)
            }
            text: model.label
            color: plotData.wcsOriginColor
            font.pixelSize: 13
            font.bold: true
            style: Text.Outline
            styleColor: "#000000"
            visible: plotData.wcsOriginsVisible
                     && screenPos.x > -80 && screenPos.x < root.width + 80
                     && screenPos.y > -30 && screenPos.y < root.height + 30
            x: screenPos.x - width / 2
            y: screenPos.y - height - 8 + stackOffset
            z: 2
        }
    }

    // Machine/program bound tick labels, projected like the WCS labels.
    Repeater {
        id: machineTickRepeater
        model: (typeof machineTickLabels !== "undefined") ? machineTickLabels : null
        onCountChanged: Qt.callLater(root.declutterAll)
        delegate: Text {
            objectName: "machineTickLabel"
            property vector3d anchor: model.pos
            property real stackOffset: 0
            property vector3d screenPos: {
                plotData.cameraRevision
                view3d.width
                view3d.height
                return view3d.mapFrom3DScene(anchor)
            }
            text: model.label
            color: plotData.boundsColor
            font.pixelSize: 11
            style: Text.Outline
            styleColor: "#000000"
            visible: plotData.machineLabelsVisible
                     && screenPos.x > -80 && screenPos.x < root.width + 80
                     && screenPos.y > -30 && screenPos.y < root.height + 30
            x: screenPos.x - width / 2
            y: screenPos.y - height - 6 + stackOffset
            z: 2
        }
    }
    Repeater {
        id: programTickRepeater
        model: (typeof programTickLabels !== "undefined") ? programTickLabels : null
        onCountChanged: Qt.callLater(root.declutterAll)
        delegate: Text {
            objectName: "programTickLabel"
            property vector3d anchor: model.pos
            property real stackOffset: 0
            property vector3d screenPos: {
                plotData.cameraRevision
                view3d.width
                view3d.height
                return view3d.mapFrom3DScene(anchor)
            }
            text: model.label
            color: plotData.boundsColor
            font.pixelSize: 11
            style: Text.Outline
            styleColor: "#000000"
            visible: plotData.programTicksVisible && plotData.programBoundsVisible
                     && screenPos.x > -80 && screenPos.x < root.width + 80
                     && screenPos.y > -30 && screenPos.y < root.height + 30
            x: screenPos.x - width / 2
            y: screenPos.y - height - 6 + stackOffset
            z: 2
        }
    }

    // Click-to-select. The click ray is unprojected by View3D and handed to
    // Python, which finds the nearest path segment within a tolerance. Doing
    // the pick ourselves keeps it independent of mesh picking support for line
    // primitives, and a drag never registers as a click.
    MouseArea {
        id: pickArea
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        enabled: !plotData.touchEnabled
        onClicked: (mouse) => {
            var near = view3d.mapTo3DScene(Qt.vector3d(mouse.x, mouse.y, 0))
            var far = view3d.mapTo3DScene(Qt.vector3d(mouse.x, mouse.y, 1))
            plotData.reportPick(near, far)
        }
    }

    // Multi-touch navigation (backplot.show-multitouch / enableMultiTouch).
    // Two fingers scale, drag and twist. MultiPointTouchArea is used instead
    // of PinchArea: Qt 6.12 emits a property-cache warning for PinchArea
    // ("enabled overrides a member of the base object") from the QML loader
    // thread, and QtPyVCP's Qt-message handler is not safe to call from that
    // thread while the GUI thread is inside setSource().
    MultiPointTouchArea {
        id: touchArea
        anchors.fill: parent
        enabled: plotData.touchEnabled
        minimumTouchPoints: 2
        maximumTouchPoints: 2
        touchPoints: [
            TouchPoint { id: touch1 },
            TouchPoint { id: touch2 }
        ]
        property real lastDistance: 0.0
        property real lastAngle: 0.0
        property vector2d lastCenter: Qt.vector2d(0, 0)

        function distance() {
            var dx = touch2.x - touch1.x
            var dy = touch2.y - touch1.y
            return Math.sqrt(dx * dx + dy * dy)
        }
        function center() {
            return Qt.vector2d((touch1.x + touch2.x) / 2,
                               (touch1.y + touch2.y) / 2)
        }
        function angle() {
            return Math.atan2(touch2.y - touch1.y,
                              touch2.x - touch1.x) * 180 / Math.PI
        }

        onPressed: {
            lastDistance = distance()
            lastCenter = center()
            lastAngle = angle()
        }
        onUpdated: {
            var currentDistance = distance()
            if (lastDistance > 0.01 && currentDistance > 0.01)
                plotData.pinchZoom(currentDistance / lastDistance)
            lastDistance = currentDistance

            var currentCenter = center()
            var dx = currentCenter.x - lastCenter.x
            var dy = currentCenter.y - lastCenter.y
            if (Math.abs(dx) + Math.abs(dy) > 0.25)
                plotData.pinchPan(dx, dy)
            lastCenter = currentCenter

            var currentAngle = angle()
            var delta = currentAngle - lastAngle
            if (delta > 180)
                delta -= 360
            if (delta < -180)
                delta += 360
            if (Math.abs(delta) > 0.25)
                plotData.pinchRotate(delta)
            lastAngle = currentAngle
        }
        onReleased: {
            lastDistance = 0.0
            lastAngle = 0.0
        }
    }

    // Camera-orientation gizmo ("nav helper"). It is a 2D projection of the
    // scene axes, so it stays crisp and never needs a second View3D. Click an
    // axis to snap to that view (X/Y/Z).
    Item {
        id: navHelper
        objectName: "navHelper"
        property var cfg: plotData.navHelperConfig
        visible: cfg.enabled === true
        width: cfg.width || 96
        height: cfg.height || 96
        x: {
            var pad = cfg.padding_x || 0
            var anchor = String(cfg.anchor || "lower-left")
            if (anchor.indexOf("left") >= 0) return pad
            if (anchor.indexOf("right") >= 0) return root.width - width - pad
            return (root.width - width) / 2
        }
        y: {
            var pad = cfg.padding_y || 0
            var anchor = String(cfg.anchor || "lower-left")
            if (anchor.indexOf("top") >= 0) return pad
            if (anchor.indexOf("bottom") >= 0) return root.height - height - pad
            return (root.height - height) / 2
        }
        z: 3

        Rectangle {
            anchors.fill: parent
            radius: width / 2
            color: "#00000055"
            border.color: navHelper.cfg.axis_color || "#b8c2cc"
            border.width: 1
        }
        Rectangle {
            width: 4; height: 4; radius: 2
            x: navHelper.width / 2 - 2
            y: navHelper.height / 2 - 2
            color: navHelper.cfg.axis_color || "#b8c2cc"
        }

        Repeater {
            model: plotData.navHelperAxes
            delegate: Item {
                id: axisItem
                property var axisData: modelData
                property real cx: navHelper.width / 2
                property real cy: navHelper.height / 2
                property real projected: Math.sqrt(
                    axisData.dx * axisData.dx + axisData.dy * axisData.dy)
                property real axisLength: Math.max(
                    5, (navHelper.cfg.length || 32) * projected)
                property real angle: Math.atan2(-axisData.dy, axisData.dx)
                        * 180 / Math.PI
                anchors.fill: parent

                Rectangle {
                    x: axisItem.cx
                    y: axisItem.cy - height / 2
                    width: axisItem.axisLength
                    height: 3
                    radius: 1.5
                    color: axisItem.axisData.color
                    opacity: 0.55 + 0.45 * Math.max(
                        0, Math.min(1, (axisItem.axisData.depth + 1) / 2))
                    transform: Rotation {
                        origin.x: 0
                        origin.y: 1.5
                        angle: axisItem.angle
                    }
                }
                Rectangle {
                    width: 7; height: 7; radius: 3.5
                    color: axisItem.axisData.color
                    x: axisItem.cx + axisItem.axisData.dx * axisItem.axisLength - 3.5
                    y: axisItem.cy + axisItem.axisData.dy * axisItem.axisLength - 3.5
                }
                Text {
                    visible: navHelper.cfg.labels_visible !== false
                    text: (navHelper.cfg.labels
                           && navHelper.cfg.labels.length > 0)
                          ? navHelper.cfg.labels[axisItem.axisData.axis === "X" ? 0
                                              : axisItem.axisData.axis === "Y" ? 1 : 2]
                          : axisItem.axisData.axis
                    color: axisItem.axisData.color
                    font.pixelSize: 10
                    font.bold: true
                    style: Text.Outline
                    styleColor: "#000000"
                    x: axisItem.cx + axisItem.axisData.dx
                       * (axisItem.axisLength + 8) - width / 2
                    y: axisItem.cy + axisItem.axisData.dy
                       * (axisItem.axisLength + 8) - height / 2
                }
            }
        }
        MouseArea {
            anchors.fill: parent
            enabled: navHelper.cfg.pickable !== false
            onClicked: (mouse) => {
                var cx = navHelper.width / 2
                var cy = navHelper.height / 2
                var best = null
                var bestDistance = 1e9
                var axes = plotData.navHelperAxes
                for (var i = 0; i < axes.length; i++) {
                    var axis = axes[i]
                    var length = Math.max(
                        5, (navHelper.cfg.length || 32)
                           * Math.sqrt(axis.dx * axis.dx + axis.dy * axis.dy))
                    var ex = cx + axis.dx * length
                    var ey = cy + axis.dy * length
                    var vx = ex - cx
                    var vy = ey - cy
                    var wx = mouse.x - cx
                    var wy = mouse.y - cy
                    var segment = vx * vx + vy * vy
                    var t = segment > 1e-9
                            ? Math.max(0, Math.min(1, (wx * vx + wy * vy) / segment))
                            : 0
                    var dx = wx - vx * t
                    var dy = wy - vy * t
                    var distance = Math.sqrt(dx * dx + dy * dy)
                    if (distance < bestDistance) {
                        bestDistance = distance
                        best = axis
                    }
                }
                if (best !== null && bestDistance < 20)
                    plotData.requestView(best.axis)
            }
        }
    }
}
