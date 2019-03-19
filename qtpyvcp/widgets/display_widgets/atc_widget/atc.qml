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
            duration: 1000
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

                property string pocket_num: "P" + (index+1)

                Text {

                    id: pocket_text

                    anchors {
                        horizontalCenter: parent.horizontalCenter
                    }
                    x: 0
                    y: atc_holder.height*0.18
                    rotation: 360 + (index * 30) - 90

                    text: parent.pocket_num
                    font.family: "Bebas Kai"
                    font.bold: false
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    font.pixelSize: 24

                }
                RotationAnimator {
                    id: pocket_anim

                    target: pocket_item;
                    duration: 1000
                    running: false
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
                property string tool_text: "NO"

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
                    rotation: 360 + (index * 30) - 90

                    Text {
                        id: tool_text
                        text: tool_item.tool_text
                        font.family: "Bebas Kai"
                        font.bold: false
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                        font.pixelSize: 24
                        x: parent.width / 2 - width / 2
                        y: parent.height / 2 - height / 2
                    }

                    RotationAnimator {
                        id: tool_anim
                        target: tool_rectangle
                        duration: 1000
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
        atc.from = 360/12 * previous_pocket + 90;
        atc.to = 360/12 * next_pocket + 90;

        var  slots_num = 0;

        if(next_pocket > previous_pocket){
            slots_num = next_pocket - previous_pocket;
        }
        else {
            slots_num = previous_pocket - next_pocket;
        }

        atc.duration = 1000 * slots_num;
        atc.restart();
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

    Connections {
        target: atc_spiner


        onHideToolSig: {
            tool_slot.itemAt(tool_num - 1).state = "hidden";
        }

        onShowToolSig: {
            tool_slot.itemAt(pocket - 1).tool_text = "T" + (tool_num);
            tool_slot.itemAt(pocket - 1).state = "visible";
        }

        onMoveToPocketSig: {
            rotate_atc_from_to(atc_anim, previous_pocket, pocket_num);
            /*
            for (var i = 0; i < 10; i++) {
                console.log("loop i ")
                console.log(tool_slot.itemAt(i))
                rotate_tool_from_to(tool_slot.itemAt(i), previous_pocket, pocket_num);
            }
            */
            for (var j = 0; j < pocket_slot.count; j++) {
                rotate_tool_from_to(pocket_anim, previous_pocket, pocket_num);
            }
        }

        onToolInSpindleSig: {
            console.log("tool_in_spindle")
        }

        onRotateFwdSig: {
            rotate_atc(atc_anim, position, 1);

            for (var i = 0; i < tool_anim_list.length; i++) {
                rotate_tool(tool_anim_list[i], position, 1);
            }

            for (var i = 0; i < pocket_anim_list.length; i++) {
                rotate_tool(pocket_anim_list[i], position, 1);
            }
        }

        onRotateRevSig: {
            rotate_atc(atc_anim, position, -1);

            for (var i = 0; i < tool_anim_list.length; i++) {
                rotate_tool(tool_anim_list[i], position, -1);
            }

            for (var i = 0; i < pocket_anim_list.length; i++) {
                rotate_tool(pocket_anim_list[i], position, -1);
            }
        }
    }
}
