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

    property int atc_rotation: 90;

    function rotate_atc(widget, steps, direction) {

        widget.duration = 900 * steps;
        widget.from = atc_rotation;

        if (direction === 1)
            atc_rotation = atc_rotation + 360/12 * steps;
        else if (direction === -1)
            atc_rotation = atc_rotation - 360/12 * steps;

        widget.to = atc_rotation;

        widget.restart();
    }

    property int tool_rotation: 90;

    function rotate_tool(widget, steps, direction) {

        widget.anim.duration = 900 * steps;
        widget.anim.from = tool_rotation;

        if (direction === 1) {
            widget.anim.to = -atc_rotation + 360/12 * steps;
        }
        else if (direction === -1) {
            widget.anim.to = -atc_rotation - 360/12 * steps;
        };

        widget.anim.restart()
    }

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

            console.log("QML: ROTATE FWD " + steps)

            rotate_atc(atc_anim, steps, 1);

            for (var j = 0; j < pocket_slot.count; j++) {
                rotate_tool(pocket_slot.itemAt(j), steps, 1);
            }
            for (var i = 0; i < (tool_slot.count); i++) {
                rotate_tool(tool_slot.itemAt(i), steps, 1);
            }
        }

        onRotateRevSig: {

            console.log("QML: ROTATE REV " + steps)

            rotate_atc(atc_anim, steps, -1);

            for (var j = 0; j < pocket_slot.count; j++) {
                rotate_tool(pocket_slot.itemAt(j), steps, -1);
            }

            for (var i = 0; i < (tool_slot.count); i++) {
                rotate_tool(tool_slot.itemAt(i), steps, -1);
            }
        }
    }
}
