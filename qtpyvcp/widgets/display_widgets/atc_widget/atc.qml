import QtQuick 2.7
import QtQuick.Controls 1.5
import QtQuick.Layouts 1.3

Rectangle {
    id: rectangle
    visible: true
    width: 504
    color: "#939695"
    opacity: 1
    property alias rectangle: rectangle
    height: 504


    Image {
        id: atc_holder
        width: 499
        height: 499
        visible: true
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
            x: 429
            y: 217
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
                font.pixelSize: 24
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_2
            x: 401
            y: 110
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
                font.pixelSize: 24
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_3
            x: 323
            y: 32
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
                font.pixelSize: 24
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_4
            x: 216
            y: 4
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
                font.pixelSize: 24
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_5
            x: 110
            y: 32
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
                font.pixelSize: 24
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_6
            x: 32
            y: 111
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
                font.pixelSize: 24
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_7
            x: 3
            y: 217
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
                font.pixelSize: 24
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_8
            x: 32
            y: 323
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
                font.pixelSize: 24
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_9
            x: 110
            y: 401
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
                font.pixelSize: 24
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_10
            x: 216
            y: 430
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
                font.pixelSize: 24
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_11
            x: 322
            y: 401
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
                font.pixelSize: 24
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Rectangle {
            id: tool_12
            x: 401
            y: 323
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
                font.pixelSize: 24
                x: parent.width / 2 - width / 2
                y: parent.height / 2 - height / 2
            }
        }

        Text {
            id: text1
            x: 170
            y: 109
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
            x: 245
            y: 88
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
            x: 321
            y: 106
            width: 11
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
            x: 375
            y: 172
            width: 9
            height: 12
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
            x: 394
            y: 236
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
            x: 91
            y: 237
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
            x: 242
            y: 385
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
            x: 319
            y: 364
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
            x: 371
            y: 311
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
            x: 113
            y: 161
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
            x: 112
            y: 313
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
            x: 170
            y: 365
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

    function rotate_atc_from_to(atc, previous_pocket, tool_no) {

        atc.from = 360/12 * previous_pocket
        atc.to = 360/12 * tool_no
        atc.restart()
    }

    function rotate_tool_from_to(tool, previous_pocket, tool_no) {

        tool.from = -(360/12 * previous_pocket)
        tool.to = -(360/12 * tool_no)
        tool.restart()
    }

    function rotate_atc(name, tool_no, direction) {
        if (direction === 1) {
            name.from = (360/12 * tool_no)
            name.to = (360/12 * tool_no + 360/12)
        }
        else if (direction === -1) {
            name.from = (360/12 * tool_no)
            name.to = (360/12 * tool_no - 360/12)
        }
        name.restart()
    }
    function rotate_tool(name, tool_no, direction) {
        if (direction === 1) {
            name.from = -(360/12 * tool_no)
            name.to = -(360/12 * tool_no + 360/12)
        }
        else if (direction === -1) {
            name.from = -(360/12 * tool_no)
            name.to = -(360/12 * tool_no - 360/12)
        }
        name.restart()
    }

    property var tool_list : [
        tool_anim_1,
        tool_anim_2,
        tool_anim_3,
        tool_anim_4,
        tool_anim_5,
        tool_anim_6,
        tool_anim_7,
        tool_anim_8,
        tool_anim_9,
        tool_anim_10,
        tool_anim_11,
        tool_anim_12
    ]
    property var pocket_list : [
        text1_anim,
        text2_anim,
        text3_anim,
        text4_anim,
        text5_anim,
        text6_anim,
        text7_anim,
        text8_anim,
        text9_anim,
        text10_anim,
        text11_anim,
        text12_anim
    ]

    Connections {
        target: atc_spiner

        onMoveToPocketSig: {
            rotate_atc_from_to(atc_anim, previous_pocket, pocket_num)

            for (var i = 0; i < tool_list.length; i++) {
                rotate_tool_from_to(tool_list[i], previous_pocket, pocket_num)
            }

            for (var i = 0; i < pocket_list.length; i++) {
                rotate_tool_from_to(pocket_list[i], previous_pocket, pocket_num)
            }
        }

        onToolInSpindleSig: {
            console.log("tool_in_spindle")
            // rotate_tool(tool_anim_1, 0, 12)
        }

        onRotateFwdSig: {
            rotate_atc(atc_anim, position, 1)

            for (var i = 0; i < tool_list.length; i++) {
                rotate_tool(tool_list[i], position, 1)
            }

            for (var i = 0; i < pocket_list.length; i++) {
                rotate_tool(pocket_list[i], position, 1)
            }
        }

        onRotateRevSig: {
            rotate_atc(atc_anim, position, -1)

            for (var i = 0; i < tool_list.length; i++) {
                rotate_tool(tool_list[i], position, -1)
            }

            for (var i = 0; i < pocket_list.length; i++) {
                rotate_tool(pocket_list[i], position, -1)
            }
        }
    }
}
