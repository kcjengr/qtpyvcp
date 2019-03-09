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

        Text {
            id: pocket_text_1
            x: 170
            y: 109
            text: qsTr("5")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: pocket_text_anim_1
                target: pocket_text_1;
                duration: 1000
                running: false
            }
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


        Text {
            id: pocket_text_2
            x: 245
            y: 88
            text: qsTr("4")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: pocket_text_anim_2
                target: pocket_text_2;
                duration: 1000
                running: false
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

        Text {
            id: pocket_text_3
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
                id: pocket_text_anim_3
                target: pocket_text_3;
                duration: 1000
                running: false
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

        Text {
            id: pocket_text_4
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
                id: pocket_text_anim_4
                target: pocket_text_4;
                duration: 1000
                running: false
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

        Text {
            id: pocket_text_5
            x: 394
            y: 236
            text: qsTr("1")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: pocket_text_anim_5
                target: pocket_text_5;
                duration: 1000
                running: false
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

        Text {
            id: pocket_text_6
            x: 91
            y: 237
            text: qsTr("7")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: pocket_text_anim_6
                target: pocket_text_6;
                duration: 1000
                running: false
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

        Text {
            id: pocket_text_7
            x: 242
            y: 385
            text: qsTr("10")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: pocket_text_anim_7
                target: pocket_text_7;
                duration: 1000
                running: false
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

        Text {
            id: pocket_text_8
            x: 319
            y: 364
            text: qsTr("11")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: pocket_text_anim_8
                target: pocket_text_8;
                duration: 1000
                running: false
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

        Text {
            id: pocket_text_9
            x: 371
            y: 311
            text: qsTr("12")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: pocket_text_anim_9
                target: pocket_text_9;
                duration: 1000
                running: false
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

        Text {
            id: pocket_text_10
            x: 113
            y: 161
            text: qsTr("6")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: pocket_text_anim_10
                target: pocket_text_10;
                duration: 1000
                running: false
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

        Text {
            id: pocket_text_11
            x: 112
            y: 313
            text: qsTr("8")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: pocket_text_anim_11
                target: pocket_text_11;
                duration: 1000
                running: false
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

        Text {
            id: pocket_text_12
            x: 170
            y: 365
            text: qsTr("9")
            font.family: "Bebas Kai"
            font.bold: false
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 24

            RotationAnimator {
                id: pocket_text_anim_12
                target: pocket_text_12;
                duration: 1000
                running: false
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
        tool_1,
        tool_2,
        tool_3,
        tool_4,
        tool_5,
        tool_6,
        tool_7,
        tool_8,
        tool_9,
        tool_10,
        tool_11,
        tool_12
    ]
    property var tool_text : [
        tool_text_1,
        tool_text_2,
        tool_text_3,
        tool_text_4,
        tool_text_5,
        tool_text_6,
        tool_text_7,
        tool_text_8,
        tool_text_9,
        tool_text_10,
        tool_text_11,
        tool_text_12
    ]

    property var tool_anim_list : [
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

    property var pocket_anim_list : [
        pocket_text_anim_1,
        pocket_text_anim_2,
        pocket_text_anim_3,
        pocket_text_anim_4,
        pocket_text_anim_5,
        pocket_text_anim_6,
        pocket_text_anim_7,
        pocket_text_anim_8,
        pocket_text_anim_9,
        pocket_text_anim_10,
        pocket_text_anim_11,
        pocket_text_anim_12
    ]

    Connections {
        target: atc_spiner

        onHideToolSig: {
            tool_list[tool].visible = false;
        }
        onShowToolSig: {
            tool_list[pocket].visible = true;
            tool_text[pocket].text = qsTr("T" + tool)

        }

        onMoveToPocketSig: {
            rotate_atc_from_to(atc_anim, previous_pocket, pocket_num)

            for (var i = 0; i < tool_anim_list.length; i++) {
                rotate_tool_from_to(tool_anim_list[i], previous_pocket, pocket_num)
            }

            for (var i = 0; i < pocket_anim_list.length; i++) {
                rotate_tool_from_to(pocket_anim_list[i], previous_pocket, pocket_num)
            }
        }

        onToolInSpindleSig: {
            console.log("tool_in_spindle")
            // rotate_tool(tool_anim_1, 0, 12)
        }

        onRotateFwdSig: {
            rotate_atc(atc_anim, position, 1)

            for (var i = 0; i < tool_anim_list.length; i++) {
                rotate_tool(tool_anim_list[i], position, 1)
            }

            for (var i = 0; i < pocket_anim_list.length; i++) {
                rotate_tool(pocket_anim_list[i], position, 1)
            }
        }

        onRotateRevSig: {
            rotate_atc(atc_anim, position, -1)

            for (var i = 0; i < tool_anim_list.length; i++) {
                rotate_tool(tool_anim_list[i], position, -1)
            }

            for (var i = 0; i < pocket_anim_list.length; i++) {
                rotate_tool(pocket_anim_list[i], position, -1)
            }
        }
    }
}
