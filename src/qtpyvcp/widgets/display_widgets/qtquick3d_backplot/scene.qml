import QtQuick
import QtQuick3D

Item {
    id: root
    objectName: "quick3DBackplotRoot"
    width: 640
    height: 480

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
    }

    // Work-offset labels. These are 2D overlays projected through the View3D
    // so they stay readable at any zoom and always face the operator. The
    // cameraRevision dependency makes the projection re-evaluate on orbit,
    // pan, zoom and projection changes.
    Repeater {
        model: (typeof wcsOrigins !== "undefined") ? wcsOrigins : null
        delegate: Text {
            objectName: "wcsOriginLabel"
            property vector3d anchor: model.pos
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
            y: screenPos.y - height - 8
            z: 2
        }
    }

    // Click-to-select. The click ray is unprojected by View3D and handed to
    // Python, which finds the nearest path segment within a tolerance. Doing
    // the pick ourselves keeps it independent of mesh picking support for line
    // primitives, and a drag never registers as a click.
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        onClicked: (mouse) => {
            var near = view3d.mapTo3DScene(Qt.vector3d(mouse.x, mouse.y, 0))
            var far = view3d.mapTo3DScene(Qt.vector3d(mouse.x, mouse.y, 1))
            plotData.reportPick(near, far)
        }
    }
}
