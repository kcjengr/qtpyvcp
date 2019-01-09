import QtQuick 2.7
import QtQuick.Controls 1.5
import QtQuick.Layouts 1.3

Rectangle {
    visible: true
    width: 1024
    clip: false
    transformOrigin: Item.Center
    height: 600
    color: "#919191"
    border.color: "#00000000"

    Image {
        id: holder
        x: 0
        y: 140
        width: 452
        height: 321
        fillMode: Image.PreserveAspectCrop
        z: 0
        rotation: 0
        transformOrigin: Item.Center
        source: "images/lathe_chuck_dim_lines.png"
    }

    Row {
        x: 439
        y: -89
        width: 328
        height: 223
        spacing: 20; // a simple layout do avoid overlapping

            Repeater {
                id: upper_tools
                model: 5; // just define the number you want, can be a variable too

                delegate:
                    Image {
                        x: 379
                        y: 0
                        width: 50
                        height: 200
                        fillMode: Image.PreserveAspectFit
                        z: 0
                        rotation: 0
                        transformOrigin: Item.Center
                        state: "released"
                        source: "images/lathe_center_turning_rp_bs.png"

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                tool_selected(1)
                            }
                        }
                        states: [
                            State {
                                name: "released"
                                PropertyChanges { target: upper_tools; x: 379; y: 0 }
                            },
                            State {
                                name: "selected"
                                PropertyChanges { target: upper_tools; x: 300; y: 50 }
                            }
                        ]
                        transitions: Transition {
                            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
                        }
                   }
            }
        }

    Row {
        x: 439
        y: 467
        width: 333
        height: 273
        spacing: 20; // a simple layout do avoid overlapping

            Repeater {
                id: lower_tools
                model: 5; // just define the number you want, can be a variable too

                delegate:
                    Image {
                        id: lower_tool
                        x: 379
                        y: 0
                        width: 50
                        height: 200
                        fillMode: Image.PreserveAspectFit
                        z: 0
                        rotation: 0
                        transformOrigin: Item.Center
                        state: "released"
                        source: "images/lathe_center_turning_fp_ts.png"

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                tool_selected(1)
                            }
                        }
                        states: [
                            State {
                                name: "released"
                                PropertyChanges { target: lower_tool; x: 379; y: 0 }
                            },
                            State {
                                name: "selected"
                                PropertyChanges { target: lower_tool; x: 300; y: 50 }
                            }
                        ]
                        transitions: Transition {
                            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
                        }
                   }
            }
        }

    Column {
        x: 731
        y: 166
        width: 199
        height: 269
        spacing: 20; // a simple layout do avoid overlapping

            Repeater {
                id: right_tools
                model: 5; // just define the number you want, can be a variable too

                delegate:
                    Image {
                        x: 0
                        y: 0
                        width: 200
                        height: 38
                        fillMode: Image.PreserveAspectFit
                        z: 0
                        rotation: 0
                        transformOrigin: Item.Center
                        state: "released"
                        source: "images/lathe_internal_threading_bs.png"

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                tool_selected(this)
                            }
                        }
                        states: [
                            State {
                                name: "released"
                                PropertyChanges { target: right_tools; x: 0; y: 0 }
                            },
                            State {
                                name: "selected"
                                PropertyChanges { target: right_tools; x: 300; y: 50 }
                            }
                        ]
                        transitions: Transition {
                            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
                        }
                }
            }
        }


    function set_images(element, pics) {
        for (var i = 0; i < 5; i++) {
            element.itemAt(i).source = pics[i];
        }
    }

    Component.onCompleted: {

        var upper_tool_pics = [
            "images/lathe_lh_turning_rp_bs.png",
            "images/lathe_center_turning_rp_bs.png",
            "images/lathe_rh_turning_rp_bs.png",
            "images/lathe_rh_threading_fp_ts.png",
            "images/lathe_lh_turning_fp_ts.png"
        ];

        var lower_tool_pics = [
            "images/lathe_lh_turning_fp_ts.png",
            "images/lathe_center_turning_fp_ts.png",
            "images/lathe_rh_turning_fp_ts.png",
            "images/lathe_rh_threading_fp_ts.png",
            "images/lathe_parting_fp_ts.png"
        ];

        var right_tool_pics = [
            "images/lathe_internal_threading_bs.png",
            "images/lathe_internal_boring_bs.png",
            "images/lathe_internal_drilling_ts.png",
            "images/lathe_internal_boring_ts.png",
            "images/lathe_internal_threading_ts.png"
        ];

        set_images(upper_tools, upper_tool_pics);
        set_images(lower_tools, lower_tool_pics);
        set_images(right_tools, right_tool_pics);
    }

    function tool_selected(tool) {
        tool.state  = "selected"
    }

    Connections {
        target: handler

        onPocketSig: {
            console.log(pocket_number)
        }
    }
}
