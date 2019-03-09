import QtQuick 2.7
import QtQuick.Controls 1.5
import QtQuick.Layouts 1.3

Rectangle {
    id: rectangle
    visible: true
    width: 600
    color: "#00000000"
    property alias rectangle: rectangle
    border.width: 0
    border.color: "#00000000"
    height: 600

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
            text: qsTr("Reverse")

            Layout.columnSpan: 2

            onClicked: {
                atc_spiner.rotate_reverse()
            }
        }

        Button {
            height: 40
            Layout.fillWidth: true
            text: qsTr("Forward")

            Layout.columnSpan: 2

            onClicked: {
                atc_spiner.rotate_forward()
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
            x: 454
            y: 228
            width: 66
            height: width
            color: "#ffffff"
            radius: width / 2
            border.width: 2

            RotationAnimator {
                id: tool_anim_1
                target: tool_1;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_1
                text: qsTr("T1")
                font.family: "Bebas Kai"
                font.bold: false
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 28
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_2
            x: 424
            y: 116
            width: 66
            height: width
            color: "#ffffff"
            radius: width / 2
            border.width: 2

            RotationAnimator {
                id: tool_anim_2
                target: tool_2;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_2
                text: qsTr("T2")
                font.family: "Bebas Kai"
                font.bold: false
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 28
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_3
            x: 341
            y: 34
            width: 66
            height: width
            color: "#ffffff"
            radius: width / 2
            border.width: 2

            RotationAnimator {
                id: tool_anim_3
                target: tool_3;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_3
                text: qsTr("T3")
                font.family: "Bebas Kai"
                font.bold: false
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 28
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_4
            x: 228
            y: 5
            width: 66
            height: width
            color: "#ffffff"
            radius: width / 2
            border.width: 2

            RotationAnimator {
                id: tool_anim_4
                target: tool_4;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_4
                text: qsTr("T4")
                font.family: "Bebas Kai"
                font.bold: false
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 28
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_5
            x: 117
            y: 35
            width: 66
            height: width
            color: "#ffffff"
            radius: width / 2
            border.width: 2

            RotationAnimator {
                id: tool_anim_5
                target: tool_5;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_5
                text: qsTr("T5")
                font.family: "Bebas Kai"
                font.bold: false
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 28
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_6
            x: 34
            y: 116
            width: 66
            height: width
            color: "#ffffff"
            radius: width / 2
            border.width: 2

            RotationAnimator {
                id: tool_anim_6
                target: tool_6;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_6
                text: qsTr("T6")
                font.family: "Bebas Kai"
                font.bold: false
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 28
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_7
            x: 4
            y: 229
            width: 66
            height: width
            color: "#ffffff"
            radius: width / 2
            border.width: 2

            RotationAnimator {
                id: tool_anim_7
                target: tool_7;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_7
                text: qsTr("T7")
                font.family: "Bebas Kai"
                font.bold: false
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 28
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_8
            x: 34
            y: 341
            width: 66
            height: width
            color: "#ffffff"
            radius: width / 2
            border.width: 2

            RotationAnimator {
                id: tool_anim_8
                target: tool_8;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_8
                text: qsTr("T8")
                font.bold: false
                font.family: "Bebas Kai"
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 28
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_9
            x: 116
            y: 423
            width: 66
            height: width
            color: "#ffffff"
            radius: width / 2
            border.width: 2

            RotationAnimator {
                id: tool_anim_9
                target: tool_9;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_9
                text: qsTr("T9")
                font.family: "Bebas Kai"
                font.bold: false
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 28
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_10
            x: 229
            y: 453
            width: 66
            height: width
            color: "#ffffff"
            radius: width / 2
            border.width: 2

            RotationAnimator {
                id: tool_anim_10
                target: tool_10;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_10
                text: qsTr("T10")
                font.family: "Bebas Kai"
                font.bold: false
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 28
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_11
            x: 341
            y: 423
            width: 66
            height: width
            color: "#ffffff"
            radius: width / 2
            border.width: 2

            RotationAnimator {
                id: tool_anim_11
                target: tool_11;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_11
                text: qsTr("T11")
                font.family: "Bebas Kai"
                font.bold: false
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 28
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_12
            x: 424
            y: 341
            width: 66
            height: width
            color: "#ffffff"
            radius: width / 2
            border.width: 2

            RotationAnimator {
                id: tool_anim_12
                target: tool_12;
                duration: 1000
                running: false
            }

            Text {
                id: tool_text_12
                text: qsTr("T12")
                font.family: "Bebas Kai"
                font.bold: false
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 28
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Text {
            id: text1
            x: 183
            y: 117
            text: qsTr("5")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: text1_anim
                target: text1;
                duration: 1000
                running: false
            }
        }

        Text {
            id: text2
            x: 257
            y: 97
            text: qsTr("4")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: text2_anim
                target: text2;
                duration: 1000
                running: false
            }
        }

        Text {
            id: text3
            x: 334
            y: 115
            text: qsTr("3")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: text3_anim
                target: text3;
                duration: 1000
                running: false
            }
        }

        Text {
            id: text4
            x: 389
            y: 181
            width: 8
            height: 14
            text: qsTr("2")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: text4_anim
                target: text4;
                duration: 1000
                running: false
            }
        }

        Text {
            id: text5
            x: 407
            y: 246
            text: qsTr("1")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: text5_anim
                target: text5;
                duration: 1000
                running: false
            }
        }

        Text {
            id: text6
            x: 102
            y: 247
            text: qsTr("7")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: text6_anim
                target: text6;
                duration: 1000
                running: false
            }
        }

        Text {
            id: text7
            x: 254
            y: 398
            text: qsTr("10")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: text7_anim
                target: text7;
                duration: 1000
                running: false
            }
        }

        Text {
            id: text8
            x: 332
            y: 378
            text: qsTr("11")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: text8_anim
                target: text8;
                duration: 1000
                running: false
            }
        }

        Text {
            id: text9
            x: 384
            y: 322
            text: qsTr("12")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: text9_anim
                target: text9;
                duration: 1000
                running: false
            }
        }

        Text {
            id: text10
            x: 125
            y: 170
            text: qsTr("6")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: text10_anim
                target: text10;
                duration: 1000
                running: false
            }
        }

        Text {
            id: text11
            x: 123
            y: 324
            text: qsTr("8")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: text11_anim
                target: text11;
                duration: 1000
                running: false
            }
        }

        Text {
            id: text12
            x: 181
            y: 377
            text: qsTr("9")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: text12_anim
                target: text12;
                duration: 1000
                running: false
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

    function rotate_atc(atc, previous_pocket, tool_no) {

        atc.from = 360/12 * previous_pocket
        atc.to = 360/12 * tool_no
        atc.restart()
    }

    function rotate_tool(tool, previous_pocket, tool_no) {

        tool.from = -(360/12 * previous_pocket)
        tool.to = -(360/12 * tool_no)
        tool.restart()
    }


    Connections {
        target: atc_spiner

        onMoveToPocketSig: {
            console.log(previous_pocket, pocket_num)

            rotate_atc(atc_anim, previous_pocket, pocket_num)

            rotate_tool(tool_anim_1, previous_pocket, pocket_num)
            rotate_tool(tool_anim_2, previous_pocket, pocket_num)
            rotate_tool(tool_anim_3, previous_pocket, pocket_num)
            rotate_tool(tool_anim_4, previous_pocket, pocket_num)
            rotate_tool(tool_anim_5, previous_pocket, pocket_num)
            rotate_tool(tool_anim_6, previous_pocket, pocket_num)
            rotate_tool(tool_anim_7, previous_pocket, pocket_num)
            rotate_tool(tool_anim_8, previous_pocket, pocket_num)
            rotate_tool(tool_anim_9, previous_pocket, pocket_num)
            rotate_tool(tool_anim_10, previous_pocket, pocket_num)
            rotate_tool(tool_anim_11, previous_pocket, pocket_num)
            rotate_tool(tool_anim_12, previous_pocket, pocket_num)

            rotate_tool(text1_anim, previous_pocket, pocket_num)
            rotate_tool(text2_anim, previous_pocket, pocket_num)
            rotate_tool(text3_anim, previous_pocket, pocket_num)
            rotate_tool(text4_anim, previous_pocket, pocket_num)
            rotate_tool(text5_anim, previous_pocket, pocket_num)
            rotate_tool(text6_anim, previous_pocket, pocket_num)
            rotate_tool(text7_anim, previous_pocket, pocket_num)
            rotate_tool(text8_anim, previous_pocket, pocket_num)
            rotate_tool(text9_anim, previous_pocket, pocket_num)
            rotate_tool(text10_anim, previous_pocket, pocket_num)
            rotate_tool(text11_anim, previous_pocket, pocket_num)
            rotate_tool(text12_anim, previous_pocket, pocket_num)
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

            rotate_tool(text1_anim, rotate_forward, 1)
            rotate_tool(text2_anim, rotate_forward, 1)
            rotate_tool(text3_anim, rotate_forward, 1)
            rotate_tool(text4_anim, rotate_forward, 1)
            rotate_tool(text5_anim, rotate_forward, 1)
            rotate_tool(text6_anim, rotate_forward, 1)
            rotate_tool(text7_anim, rotate_forward, 1)
            rotate_tool(text8_anim, rotate_forward, 1)
            rotate_tool(text9_anim, rotate_forward, 1)
            rotate_tool(text10_anim, rotate_forward, 1)
            rotate_tool(text11_anim, rotate_forward, 1)
            rotate_tool(text12_anim, rotate_forward, 1)
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

            rotate_tool(text1_anim, rotate_reverse, -1)
            rotate_tool(text2_anim, rotate_reverse, -1)
            rotate_tool(text3_anim, rotate_reverse, -1)
            rotate_tool(text4_anim, rotate_reverse, -1)
            rotate_tool(text5_anim, rotate_reverse, -1)
            rotate_tool(text6_anim, rotate_reverse, -1)
            rotate_tool(text7_anim, rotate_reverse, -1)
            rotate_tool(text8_anim, rotate_reverse, -1)
            rotate_tool(text9_anim, rotate_reverse, -1)
            rotate_tool(text10_anim, rotate_reverse, -1)
            rotate_tool(text11_anim, rotate_reverse, -1)
            rotate_tool(text12_anim, rotate_reverse, -1)
        }
    }
}
