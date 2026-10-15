import QtQuick
import QtQuick3D

Item {
    id: root
    objectName: "quick3DBackplotRoot"
    width: 640
    height: 480

    View3D {
        id: view3d
        objectName: "backplotView3D"
        anchors.fill: parent
        camera: plotData.perspective ? perspectiveCamera : orthographicCamera

        environment: SceneEnvironment {
            clearColor: plotData.backgroundColor
            backgroundMode: SceneEnvironment.Color
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

        // Line geometry has no normals, so every material is unlit
        // (PrincipledMaterial.NoLighting) to keep its base color exact.
        Model {
            geometry: plotData.traverse
            materials: [ PrincipledMaterial { baseColor: plotData.traverseColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.arcfeed
            materials: [ PrincipledMaterial { baseColor: plotData.arcfeedColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.feed
            materials: [ PrincipledMaterial { baseColor: plotData.feedColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.dwell
            materials: [ PrincipledMaterial { baseColor: plotData.dwellColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.user
            materials: [ PrincipledMaterial { baseColor: plotData.userColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }

        Model {
            geometry: plotData.grid
            visible: plotData.gridVisible
            materials: [ PrincipledMaterial { baseColor: plotData.gridColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.axesX
            materials: [ PrincipledMaterial { baseColor: plotData.axesXColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.axesY
            materials: [ PrincipledMaterial { baseColor: plotData.axesYColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.axesZ
            materials: [ PrincipledMaterial { baseColor: plotData.axesZColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.machineBounds
            visible: plotData.machineBoundsVisible
            materials: [ PrincipledMaterial { baseColor: plotData.boundsColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.programBounds
            visible: plotData.programBoundsVisible
            materials: [ PrincipledMaterial { baseColor: plotData.boundsColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            geometry: plotData.trail
            materials: [ PrincipledMaterial { baseColor: plotData.trailColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }

        // Active tool body, sized from the QtPyVCP tool table. The built-in
        // primitives are 100 units tall/diameter, so toolScale maps radius and
        // length onto them.
        Model {
            source: "#Cylinder"
            visible: plotData.toolVisible && plotData.toolKind === "cylinder"
            position: plotData.toolPosition
            scale: plotData.toolScale
            materials: [ PrincipledMaterial { baseColor: plotData.toolColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
        Model {
            source: "#Cone"
            visible: plotData.toolVisible && plotData.toolKind === "cone"
            position: plotData.toolPosition
            scale: plotData.toolScale
            eulerRotation: Qt.vector3d(180, 0, 0)
            materials: [ PrincipledMaterial { baseColor: plotData.toolColor; roughness: 1.0; lighting: PrincipledMaterial.NoLighting } ]
        }
    }
}
