import QtQuick 2.7
import QtQuick.Controls 1.5
import QtQuick.Layouts 1.3

Rectangle {
    visible: true
    width: 550
    color: "#00000000"
    border.color: "#00000000"
    height: 550

    GridLayout {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 9

        columns: 4
        rows: 4
        rowSpacing: 10
        columnSpacing: 10

        Button {
            height: 40
            Layout.fillWidth: true
            text: qsTr("Forward")

            Layout.columnSpan: 2

            onClicked: {
                atc_spiner.rotate_forward()
            }
        }

        Button {
            height: 40
            Layout.fillWidth: true
            text: qsTr("Reverse")

            Layout.columnSpan: 2

            onClicked: {
                atc_spiner.rotate_reverse()
            }
        }
    }

    Image {
        id: atc_holder
        width: 524
        height: 523
        x: parent.width / 2 - width / 2
        y: parent.height / 2 - height / 2
        antialiasing: true
        z: 0
        rotation: 0
        transformOrigin: Item.Center
        source: "images/carousel_12.png"


        RotationAnimator {
            id: atc_anim
            target: atc_holder;
            duration: 1000
            running: false
        }

        Rectangle {
            id: tool_1
            x: 467
            y: 239
            width: 42
            height: 42
            color: "#ffffff"
            radius: 21
            border.width: 2

            RotationAnimator {
                id: tool_anim_1
                target: tool_1;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_1
                x: 8
                y: 7
                text: qsTr("T1")
                font.bold: true
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 22
            }
        }

        Rectangle {
            id: tool_2
            x: 431
            y: 129
            width: 42
            height: 42
            color: "#ffffff"
            radius: 21
            border.width: 2

            RotationAnimator {
                id: tool_anim_2
                target: tool_2;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_2
                x: 8
                y: 6
                text: qsTr("T2")
                font.bold: true
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 22
            }
        }

        Rectangle {
            id: tool_3
            x: 352
            y: 49
            width: 42
            height: 42
            color: "#ffffff"
            radius: 21
            border.width: 2

            RotationAnimator {
                id: tool_anim_3
                target: tool_3;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_3
                x: 7
                y: 6
                text: qsTr("T3")
                font.bold: true
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 22
            }
        }

        Rectangle {
            id: tool_4
            x: 240
            y: 17
            width: 42
            height: 42
            color: "#ffffff"
            radius: 21
            border.width: 2

            RotationAnimator {
                id: tool_anim_4
                target: tool_4;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_4
                x: 8
                y: 5
                text: qsTr("T4")
                font.bold: true
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 22
            }
        }

        Rectangle {
            id: tool_5
            x: 127
            y: 49
            width: 42
            height: 42
            color: "#ffffff"
            radius: 21
            border.width: 2

            RotationAnimator {
                id: tool_anim_5
                target: tool_5;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_5
                x: 7
                y: 6
                text: qsTr("T5")
                font.bold: true
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 22
            }
        }

        Rectangle {
            id: tool_6
            x: 40
            y: 127
            width: 42
            height: 42
            color: "#ffffff"
            radius: 21
            border.width: 2

            RotationAnimator {
                id: tool_anim_6
                target: tool_6;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_6
                x: 7
                y: 6
                text: qsTr("T6")
                font.bold: true
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 22
            }
        }

        Rectangle {
            id: tool_7
            x: 6
            y: 238
            width: 42
            height: 42
            color: "#ffffff"
            radius: 21
            border.width: 2

            RotationAnimator {
                id: tool_anim_7
                target: tool_7;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_7
                x: 7
                y: 7
                text: qsTr("T7")
                font.bold: true
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 22
            }
        }

        Rectangle {
            id: tool_8
            x: 43
            y: 351
            width: 42
            height: 42
            color: "#ffffff"
            radius: 21
            border.width: 2

            RotationAnimator {
                id: tool_anim_8
                target: tool_8;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_8
                x: 7
                y: 6
                text: qsTr("T8")
                font.bold: true
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 22
            }
        }

        Rectangle {
            id: tool_9
            x: 127
            y: 435
            width: 42
            height: 42
            color: "#ffffff"
            radius: 21
            border.width: 2

            RotationAnimator {
                id: tool_anim_9
                target: tool_9;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_9
                x: 7
                y: 6
                text: qsTr("T9")
                font.bold: true
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 22
            }
        }

        Rectangle {
            id: tool_10
            x: 241
            y: 465
            width: 42
            height: 42
            color: "#ffffff"
            radius: 21
            border.width: 2

            RotationAnimator {
                id: tool_anim_10
                target: tool_10;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_10
                x: 2
                y: 6
                text: qsTr("T10")
                font.bold: true
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 22
            }
        }

        Rectangle {
            id: tool_11
            x: 352
            y: 435
            width: 42
            height: 42
            color: "#ffffff"
            radius: 21
            border.width: 2

            RotationAnimator {
                id: tool_anim_11
                target: tool_11;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_11
                x: 2
                y: 6
                text: qsTr("T11")
                font.bold: true
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 22
            }
        }

        Rectangle {
            id: tool_12
            x: 435
            y: 353
            width: 42
            height: 42
            color: "#ffffff"
            radius: 21
            border.width: 2

            RotationAnimator {
                id: tool_anim_12
                target: tool_12;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_12
                x: 2
                y: 6
                text: qsTr("T12")
                font.bold: true
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 22
            }
        }
    }

//    Timer {
//        id: halTimer
//        interval: 100
//        repeat: true
//        running: true
//        triggeredOnStart: false
//        onTriggered: atc_spiner.get_pins()
//    }


    function rotate_atc(name, tool_no, direction) {
        if (direction === 1) {
            name.from = (360/12 * tool_no)
            name.to = (360/12 * tool_no + 360/12)
            name.restart()
        }
        else if (direction === -1) {
            name.from = (360/12 * tool_no)
            name.to = (360/12 * tool_no - 360/12)
            name.restart()
        }
    }

    function rotate_tool(name, tool_no, direction) {
        if (direction === 1) {
            name.from = -(360/12 * tool_no)
            name.to = -(360/12 * tool_no + 360/12)
            name.restart()
        }
        else if (direction === -1) {
            name.from = -(360/12 * tool_no)
            name.to = -(360/12 * tool_no - 360/12)
            name.restart()
        }
    }

    Connections {
        target: atc_spiner

        onMoveToPocketSig: {
            console.log(pocket_no)
        }

        onRotateFwdSig: {
            rotate_atc(atc_anim, rotate_forward, 1)

            rotate_tool(tool_anim_1, rotate_forward, 1)
            rotate_tool(tool_anim_2, rotate_forward, 1)
            rotate_tool(tool_anim_3, rotate_forward, 1)
            rotate_tool(tool_anim_4, rotate_forward, 1)
            rotate_tool(tool_anim_5, rotate_forward, 1)
            rotate_tool(tool_anim_6, rotate_forward, 1)
            rotate_tool(tool_anim_7, rotate_forward, 1)
            rotate_tool(tool_anim_8, rotate_forward, 1)
            rotate_tool(tool_anim_9, rotate_forward, 1)
            rotate_tool(tool_anim_10, rotate_forward, 1)
            rotate_tool(tool_anim_11, rotate_forward, 1)
            rotate_tool(tool_anim_12, rotate_forward, 1)

        }

        onRotateRevSig: {
            rotate_atc(atc_anim, rotate_reverse, -1)

            rotate_tool(tool_anim_1, rotate_reverse, -1)
            rotate_tool(tool_anim_2, rotate_reverse, -1)
            rotate_tool(tool_anim_3, rotate_reverse, -1)
            rotate_tool(tool_anim_4, rotate_reverse, -1)
            rotate_tool(tool_anim_5, rotate_reverse, -1)
            rotate_tool(tool_anim_6, rotate_reverse, -1)
            rotate_tool(tool_anim_7, rotate_reverse, -1)
            rotate_tool(tool_anim_8, rotate_reverse, -1)
            rotate_tool(tool_anim_9, rotate_reverse, -1)
            rotate_tool(tool_anim_10, rotate_reverse, -1)
            rotate_tool(tool_anim_11, rotate_reverse, -1)
            rotate_tool(tool_anim_12, rotate_reverse, -1)

        }
    }
}
