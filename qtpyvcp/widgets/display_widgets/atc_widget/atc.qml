import QtQuick 2.7
import QtQuick.Controls 1.5
import QtQuick.Layouts 1.3

Rectangle {
    id: rectangle
    visible: true
    width: 550
    color: "#939695"
    opacity: 1
    height: 550

    Image {
        id: atc_holder
        width: 550
        height: 550
        visible: true
        x: parent.width / 2 - width / 2
        y: parent.height / 2 - height / 2
        antialiasing: true
        z: 0
        rotation: 90
        transformOrigin: Item.Center
        source: "images/carousel_12.png"


        RotationAnimator {
            id: atc_anim
            target: atc_holder;
            duration: 500
            running: false
        }

        Repeater {
            id: pocket_slot
            model: 12

            delegate: Item {

                id: pocket_item

                height: atc_holder.height/2
                transformOrigin: Item.Bottom
                rotation: -index * 30
                x: atc_holder.width/2
                y: 0

                property string pocket_num: index+1
                property var anim: pocket_anim

                Rectangle {
                    id: pocket_rectangle

                    height: atc_holder.height * 0.1
                    width: height
                    radius: width/2
                    color: "white"
                    border.color: "white"
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.topMargin: 90
                    border.width: 2
                    rotation: 30 * index - 90


                    Text {
                        id: pocket_text
                        text: "P" + pocket_item.pocket_num
                        font.family: "Bebas Kai"
                        font.bold: false
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                        font.pixelSize: 24
                        x: parent.width / 2 - width / 2
                        y: parent.height / 2 - height / 2
                    }

                    RotationAnimation{
                        id:pocket_anim
                        target:pocket_text
                        direction: RotationAnimator.Shortest
                        duration: atc_anim.duration
                        running: false
                    }
                }
            }
        }

        Repeater {
            id: tool_slot
            model: 12

            delegate: Item {

                id: tool_item
                height: atc_holder.height/2
                transformOrigin: Item.Bottom
                rotation: -index * 30
                x: atc_holder.width/2
                y: 0

                state: "visible"

                property int tool_num: index
                property var anim: tool_anim

                Rectangle {
                    id: tool_rectangle

                    height: atc_holder.height*0.135
                    width: height
                    radius: width/2
                    color: "white"
                    border.color: "grey"
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.topMargin: 4
                    border.width: 2
                    rotation: 30 * index - 90

                    Text {
                        id: tool_text
                        text: "T" + tool_item.tool_num
                        font.family: "Bebas Kai"
                        font.bold: false
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                        font.pixelSize: 24
                        x: parent.width / 2 - width / 2
                        y: parent.height / 2 - height / 2
                    }

                    RotationAnimation {
                        id: tool_anim
                        target:tool_text
                        direction: RotationAnimator.Shortest
                        duration: atc_anim.duration
                        running: false
                    }
                }

                states: [
                    State {
                        name: "hidden"
                        PropertyChanges { target: tool_slot.itemAt(index); visible: false}
                    },
                    State {
                        name: "visible"
                        PropertyChanges { target: tool_slot.itemAt(index); visible: true}
                    }
                ]
            }
        }
    }


    Text {
        id: msg_text
        width: 206
        height: 91
        x: parent.width/2 - width/2
        y: parent.height/2 - height/2
        text: qsTr("UNREFERENCED")
        visible: true
        font.capitalization: Font.AllUppercase
        font.pixelSize: 36
        font.family: "Bebas Kai"
        fontSizeMode: Text.Fit
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
    }


    function rotate_atc(anim, duration, from, to) {

        anim.duration = duration
        anim.from = from
        anim.to = to
        anim.restart()
    }

    function rotate_tool(widget, duration, from, to) {

        widget.anim.duration = duration;
        widget.anim.from = from;
        widget.anim.to = to
        widget.anim.restart()
    }

    property int anim_from: 90;
    property int anim_to: 0;
    property int anim_duration: 0;

    Connections {
        target: atc_spiner

        onHideToolSig: {
            tool_slot.itemAt(tool_num - 1).state = "hidden";
        }

        onShowToolSig: {
            tool_slot.itemAt(pocket - 1).tool_num = tool_num;
            tool_slot.itemAt(pocket - 1).state = "visible";
        }

        onRotateFwdSig: {

            anim_duration = 1000 * steps;

            anim_to = anim_from + (360/12 *steps);

            rotate_atc(atc_anim, anim_duration, anim_from, anim_to);

            for (var j = 0; j < pocket_slot.count; j++) {
                rotate_tool(pocket_slot.itemAt(j), anim_duration, anim_from-90, -anim_to+90);
            }
            for (var i = 0; i < (tool_slot.count); i++) {
                rotate_tool(tool_slot.itemAt(i), anim_duration, anim_from-90, -anim_to+90);
            }
            anim_from = anim_to
        }

        onRotateRevSig: {

            anim_duration = 1000 * steps;

            anim_to = anim_from - 360/12 *steps;

            rotate_atc(atc_anim, anim_duration, anim_from, anim_to);

            for (var j = 0; j < pocket_slot.count; j++) {
                rotate_tool(pocket_slot.itemAt(j), anim_duration, anim_from-90, -anim_to+90);
            }
            for (var i = 0; i < (tool_slot.count); i++) {
                rotate_tool(tool_slot.itemAt(i), anim_duration, anim_from-90, -anim_to+90);
            }
            anim_from = anim_to
        }

        onHomeMsgSig: {
            msg_text.text = message;
        }

        onHomingMsgSig: {
            msg_text.text = message;
        }
    }
}
