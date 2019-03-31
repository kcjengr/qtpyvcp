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
        rotation: 0
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
                    rotation: 30 * index


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
                    rotation: 30 * index

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

    function rotate_atc_from_to(atc, previous_pocket, next_pocket) {
        atc.direction = "Shortest"

        atc.from = 360/12 * previous_pocket + 90;
        atc.to = 360/12 * next_pocket + 90;

        var slots_num = 0;
        var direction;

        slots_num = previous_pocket - next_pocket;

        if ( slots_num > 6){
            slots_num -= 12;
        }
        if ( slots_num < -6){
            slots_num += 12;
        }

        if (slots_num > 0){
            direction = "CCW"
        } else if(slots_num < 0){
            slots_num = slots_num * -1
            direction = "CW"
        }

        atc.duration = slots_num * 1000

        atc.restart();

    }

    function rotate_tool_from_to(widget, previous_pocket, next_pocket) {
        widget.anim.from = -(360/12 * previous_pocket)
        widget.anim.to = -(360/12 * next_pocket)

        widget.anim.restart()
    }

    function rotate_atc(widget, position, direction) {
        if (direction === 1) {
            widget.from = 360/12 * position
            widget.to = 360/12 * position + 360/12
        }
        else if (direction === -1) {
            widget.from = 360/12 * position
            widget.to = 360/12 * position - 360/12
        }
        widget.restart()
    }

    function rotate_tool(widget, tool_no, direction) {
        if (direction === 1) {
            widget.anim.from = -(360/12 * tool_no)
            widget.anim.to = -(360/12 * tool_no + 360/12)
        }
        else if (direction === -1) {
            widget.anim.from = -(360/12 * tool_no)
            widget.anim.to = -(360/12 * tool_no - 360/12)
        }
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

        onMoveToPocketSig: {
            rotate_atc_from_to(atc_anim, previous_pocket, pocket_num);


            for (var j = 0; j < pocket_slot.count; j++) {
                rotate_tool_from_to(pocket_slot.itemAt(j), previous_pocket, pocket_num);
            }

            for (var i = 0; i < (tool_slot.count); i++) {
                rotate_tool_from_to(tool_slot.itemAt(i), previous_pocket, pocket_num);
            }
        }

        onRotateFwdSig: {

            rotate_atc(atc_anim, position, 1);

            for (var j = 0; j < pocket_slot.count; j++) {
                rotate_tool(pocket_slot.itemAt(j), position, 1);
            }

            for (var i = 0; i < (tool_slot.count); i++) {
                rotate_tool(tool_slot.itemAt(i), position, 1);
            }
        }

        onRotateRevSig: {
            rotate_atc(atc_anim, position, -1);

            for (var j = 0; j < pocket_slot.count; j++) {
                rotate_tool(pocket_slot.itemAt(j), position, -1);
            }

            for (var i = 0; i < (tool_slot.count); i++) {
                rotate_tool(tool_slot.itemAt(i), position, -1);
            }
        }

    }
}
