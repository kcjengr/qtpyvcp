import QtQuick 2.7
import QtQuick.Controls 1.5
import QtQuick.Layouts 1.3

Rectangle {
    visible: true
    width: 1280
    color: "#919191"
    height: 600

    Image {
        id: holder
        x: 0
        y: 150
        width: 256
        height: 256
        fillMode: Image.PreserveAspectCrop
        z: 0
        rotation: 0
        transformOrigin: Item.Center
        source: "images/lathe_chuck_stock.png"
    }

    // FIRST GROUP TOP 5 TOOLS

    Image {
        id: tool_1
        x: 286
        y: 8
        width: 50
        height: 200
        fillMode: Image.PreserveAspectCrop
        z: 0
        rotation: 0
        transformOrigin: Item.Center
        source: "images/lathe_lh_turning_rp_bs.png"
        state: "released"

        MouseArea {
            anchors.fill: parent
            onClicked: {
                tool_selected(1)
            }
        }
        states: [
            State {
                name: "released"
                PropertyChanges { target: tool_1; x: 286; y: 8 }
            },
            State {
                name: "selected"
                PropertyChanges { target: tool_1; x: 300; y: 50 }
            }
         ]
        transitions: Transition {
            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
        }
    }

    Image {
        id: tool_2
        x: 364
        y: 8
        width: 38
        height: 200
        fillMode: Image.PreserveAspectCrop
        source: "images/lathe_center_turning_rp_bs.png"
        antialiasing: true
        rotation: 0
        z: 0
        transformOrigin: Item.Center
        state: "released"

        MouseArea {
            anchors.fill: parent
            onClicked: {
                tool_selected(2)
            }
        }
        states: [
            State {
                name: "released"
                PropertyChanges { target: tool_2; x: 364; y: 8 }
            },
            State {
                name: "selected"
                PropertyChanges { target: tool_2; x: 300; y: 50 }
            }
         ]
        transitions: Transition {
            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
        }
    }

    Image {
        id: tool_3
        x: 428
        y: 8
        width: 50
        height: 200
        source: "images/lathe_rh_turning_rp_bs.png"
        antialiasing: true
        rotation: 0
        z: 0
        transformOrigin: Item.Center
        state: "released"


        MouseArea {
            anchors.fill: parent
            onClicked: {
                tool_selected(3)
            }
        }
        states: [
            State {
                name: "released"
                PropertyChanges { target: tool_3; x: 428; y: 8 }
            },
            State {
                name: "selected"
                PropertyChanges { target: tool_3; x: 300; y: 50 }
            }
         ]
        transitions: Transition {
            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
        }
    }

    Image {
        id: tool_4
        x: 503
        y: 8
        width: 50
        height: 200
        antialiasing: true
        z: 0
        rotation: 0
        transformOrigin: Item.Center
        source: "images/lathe_rh_threading_rp_bs.png"
        state: "released"


        MouseArea {
            anchors.fill: parent
            onClicked: {
                tool_selected(4)
            }
        }
        states: [
            State {
                name: "released"
                PropertyChanges { target: tool_4; x: 503; y: 8 }
            },
            State {
                name: "selected"
                PropertyChanges { target: tool_4; x: 300; y: 50 }
            }
         ]
        transitions: Transition {
            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
        }
    }

    Image {
        id: tool_5
        x: 575
        y: 8
        width: 38
        height: 200
        source: "images/lathe_rh_parting_rp_bs.png"
        antialiasing: true
        rotation: 0
        z: 0
        transformOrigin: Item.Center
        state: "released"


        MouseArea {
            anchors.fill: parent
            onClicked: {
                tool_selected(5)
            }
        }
        states: [
            State {
                name: "released"
                PropertyChanges { target: tool_5; x: 575; y: 8 }
            },
            State {
                name: "selected"
                PropertyChanges { target: tool_5; x: 300; y: 50 }
            }
         ]
        transitions: Transition {
            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
        }
    }

    // SECCOND GROUP BOTTOM 5 TOOLS

    Image {
        id: tool_6
        x: 286
        y: 351
        width: 50
        height: 200
        source: "images/lathe_lh_turning_fp_ts.png"
        antialiasing: true
        rotation: 0
        z: 0
        transformOrigin: Item.Center
        state: "released"


        MouseArea {
            anchors.fill: parent
            onClicked: {
                tool_selected(6)
            }
        }
        states: [
            State {
                name: "released"
                PropertyChanges { target: tool_6; x: 286; y: 351 }
            },
            State {
                name: "selected"
                PropertyChanges { target: tool_6; x: 300; y: 300 }
            }
         ]
        transitions: Transition {
            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
        }
    }

    Image {
        id: tool_7
        x: 364
        y: 351
        width: 38
        height: 200
        source: "images/lathe_center_turning_fp_ts.png"
        antialiasing: true
        rotation: 0
        z: 0
        transformOrigin: Item.Center
        state: "released"

        MouseArea {
            anchors.fill: parent
            onClicked: {
                tool_selected(7)
            }
        }
        states: [
            State {
                name: "released"
                PropertyChanges { target: tool_7; x: 364; y: 351 }
            },
            State {
                name: "selected"
                PropertyChanges { target: tool_7; x: 300; y: 300 }
            }
         ]
        transitions: Transition {
            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
        }
    }

    Image {
        id: tool_8
        x: 428
        y: 351
        width: 50
        height: 200
        source: "images/lathe_rh_turning_fp_ts.png"
        antialiasing: true
        rotation: 0
        z: 0
        transformOrigin: Item.Center
        state: "released"

        MouseArea {
            anchors.fill: parent
            onClicked: {
                tool_selected(8)
            }
        }
        states: [
            State {
                name: "released"
                PropertyChanges { target: tool_8; x: 428; y: 351 }
            },
            State {
                name: "selected"
                PropertyChanges { target: tool_8; x: 300; y: 300 }
            }
         ]
        transitions: Transition {
            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
        }
    }

    Image {
        id: tool_9
        x: 503
        y: 351
        width: 50
        height: 200
        source: "images/lathe_rh_threading_fp_ts.png"
        antialiasing: true
        rotation: 0
        z: 0
        transformOrigin: Item.Center
        state: "released"

        MouseArea {
            anchors.fill: parent
            onClicked: {
                tool_selected(9)
            }
        }
        states: [
            State {
                name: "released"
                PropertyChanges { target: tool_9; x: 503; y: 351 }
            },
            State {
                name: "selected"
                PropertyChanges { target: tool_9; x: 300; y: 300 }
            }
         ]
        transitions: Transition {
            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
        }
    }

    Image {
        id: tool_10
        x: 575
        y: 351
        width: 38
        height: 200
        source: "images/lathe_parting_fp_ts.png"
        antialiasing: true
        rotation: 0
        z: 0
        transformOrigin: Item.Center
        state: "released"

        MouseArea {
            anchors.fill: parent
            onClicked: {
                tool_selected(10)
            }
        }
        states: [
            State {
                name: "released"
                PropertyChanges { target: tool_10; x: 575; y: 351 }
            },
            State {
                name: "selected"
                PropertyChanges { target: tool_10; x: 300; y: 300 }
            }
         ]
        transitions: Transition {
            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
        }
    }

    // FINAL GROUP MID 5 TOOLS

    Image {
        id: tool_11
        x: 667
        y: 140
        width: 200
        height: 30
        enabled: true
        smooth: true
        visible: true
        clip: false
        source: "images/lathe_internal_threading_bs.png"
        antialiasing: true
        rotation: 0
        z: 0
        transformOrigin: Item.Center
        state: "released"

        MouseArea {
            visible: true
            clip: false
            anchors.fill: parent
            onClicked: {
                tool_selected(11)
            }
        }
        states: [
            State {
                name: "released"
                PropertyChanges { target: tool_11; x: 667; y: 140 }
            },
            State {
                name: "selected"
                PropertyChanges { target: tool_11; x: 300; y: 240}
            }
         ]
        transitions: Transition {
            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
        }
    }

    Image {
        id: tool_12
        x: 667
        y: 201
        width: 200
        height: 30
        source: "images/lathe_internal_boring_bs.png"
        antialiasing: true
        rotation: 0
        transformOrigin: Item.Center
        z: 0
        state: "released"

        MouseArea {
            anchors.fill: parent
            onClicked: {
                tool_selected(12)
            }
        }
        states: [
            State {
                name: "released"
                PropertyChanges { target: tool_12; x: 667; y: 201 }
            },
            State {
                name: "selected"
                PropertyChanges { target: tool_12; x: 300; y: 240 }
            }
         ]
        transitions: Transition {
            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
        }
    }

    Image {
        id: tool_13
        x: 667
        y: 266
        width: 200
        height: 25
        source: "images/lathe_internal_drilling_ts.png"
        antialiasing: true
        rotation: 0
        z: 0
        transformOrigin: Item.Center
        state: "released"

        MouseArea {
            anchors.fill: parent
            onClicked: {
                tool_selected(13)
            }
        }
        states: [
            State {
                name: "released"
                PropertyChanges { target: tool_13; x: 667; y: 266 }
            },
            State {
                name: "selected"
                PropertyChanges { target: tool_13; x: 300; y: 266 }
            }
         ]
        transitions: Transition {
            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
        }
    }

    Image {
        id: tool_14
        x: 667
        y: 318
        width: 200
        height: 30
        source: "images/lathe_internal_boring_ts.png"
        antialiasing: true
        rotation: 0
        transformOrigin: Item.Center
        z: 0
        state: "released"

        MouseArea {
            anchors.fill: parent
            onClicked: {
                tool_selected(14)
            }
        }
        states: [
            State {
                name: "released"
                PropertyChanges { target: tool_14; x: 667; y: 318 }
            },
            State {
                name: "selected"
                PropertyChanges { target: tool_14; x: 300; y: 275 }
            }
         ]
        transitions: Transition {
            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
        }
    }

    Image {
        id: tool_15
        x: 667
        y: 376
        width: 200
        height: 38
        source: "images/lathe_internal_threading_ts.png"
        antialiasing: true
        state: "released"
        rotation: 0
        z: 0
        transformOrigin: Item.Center

        MouseArea {
            anchors.fill: parent
            onClicked: {
                tool_selected(15)
            }
        }
        states: [
            State {
                name: "released"
                PropertyChanges { target: tool_15; x: 667; y: 376 }
            },
            State {
                name: "selected"
                PropertyChanges { target: tool_15; x: 300; y: 275 }
            }
         ]
        transitions: Transition {
            NumberAnimation{ properties: "x,y"; easing.type: Easing.OutExpo }
        }
    }

    function tool_selected(tool_no) {

        if (tool_no === 1){
            if (tool_1.state === "released") {

                tool_1.state = "selected"

                tool_2.visible = false
                tool_3.visible = false
                tool_4.visible = false
                tool_5.visible = false
                tool_6.visible = false
                tool_7.visible = false
                tool_8.visible = false
                tool_9.visible = false
                tool_10.visible = false
                tool_11.visible = false
                tool_12.visible = false
                tool_13.visible = false
                tool_14.visible = false
                tool_15.visible = false

            }
            else {

                tool_1.state = "released"

                tool_2.visible = true
                tool_3.visible = true
                tool_4.visible = true
                tool_5.visible = true
                tool_6.visible = true
                tool_7.visible = true
                tool_8.visible = true
                tool_9.visible = true
                tool_10.visible = true
                tool_11.visible = true
                tool_12.visible = true
                tool_13.visible = true
                tool_14.visible = true
                tool_15.visible = true
            }
        }
        if (tool_no === 2){
            if (tool_2.state === "released") {

                tool_2.state = "selected"

                tool_1.visible = false
                tool_3.visible = false
                tool_4.visible = false
                tool_5.visible = false
                tool_6.visible = false
                tool_7.visible = false
                tool_8.visible = false
                tool_9.visible = false
                tool_10.visible = false
                tool_11.visible = false
                tool_12.visible = false
                tool_13.visible = false
                tool_14.visible = false
                tool_15.visible = false

            }
            else {

                tool_2.state = "released"

                tool_1.visible = true
                tool_3.visible = true
                tool_4.visible = true
                tool_5.visible = true
                tool_6.visible = true
                tool_7.visible = true
                tool_8.visible = true
                tool_9.visible = true
                tool_10.visible = true
                tool_11.visible = true
                tool_12.visible = true
                tool_13.visible = true
                tool_14.visible = true
                tool_15.visible = true
            }
        }
        if (tool_no === 3){
            if (tool_3.state === "released") {

                tool_3.state = "selected"

                tool_1.visible = false
                tool_2.visible = false
                tool_4.visible = false
                tool_5.visible = false
                tool_6.visible = false
                tool_7.visible = false
                tool_8.visible = false
                tool_9.visible = false
                tool_10.visible = false
                tool_11.visible = false
                tool_12.visible = false
                tool_13.visible = false
                tool_14.visible = false
                tool_15.visible = false

            }
            else {

                tool_3.state = "released"

                tool_1.visible = true
                tool_2.visible = true
                tool_4.visible = true
                tool_5.visible = true
                tool_6.visible = true
                tool_7.visible = true
                tool_8.visible = true
                tool_9.visible = true
                tool_10.visible = true
                tool_11.visible = true
                tool_12.visible = true
                tool_13.visible = true
                tool_14.visible = true
                tool_15.visible = true
            }
        }
        if (tool_no === 4){
            if (tool_4.state === "released") {

                tool_4.state = "selected"

                tool_1.visible = false
                tool_2.visible = false
                tool_3.visible = false
                tool_5.visible = false
                tool_6.visible = false
                tool_7.visible = false
                tool_8.visible = false
                tool_9.visible = false
                tool_10.visible = false
                tool_11.visible = false
                tool_12.visible = false
                tool_13.visible = false
                tool_14.visible = false
                tool_15.visible = false

            }
            else {

                tool_4.state = "released"

                tool_1.visible = true
                tool_2.visible = true
                tool_3.visible = true
                tool_5.visible = true
                tool_6.visible = true
                tool_7.visible = true
                tool_8.visible = true
                tool_9.visible = true
                tool_10.visible = true
                tool_11.visible = true
                tool_12.visible = true
                tool_13.visible = true
                tool_14.visible = true
                tool_15.visible = true
            }
        }
        if (tool_no === 5){
            if (tool_5.state === "released") {

                tool_5.state = "selected"

                tool_1.visible = false
                tool_2.visible = false
                tool_3.visible = false
                tool_4.visible = false
                tool_6.visible = false
                tool_7.visible = false
                tool_8.visible = false
                tool_9.visible = false
                tool_10.visible = false
                tool_11.visible = false
                tool_12.visible = false
                tool_13.visible = false
                tool_14.visible = false
                tool_15.visible = false

            }
            else {

                tool_5.state = "released"

                tool_1.visible = true
                tool_2.visible = true
                tool_3.visible = true
                tool_4.visible = true
                tool_6.visible = true
                tool_7.visible = true
                tool_8.visible = true
                tool_9.visible = true
                tool_10.visible = true
                tool_11.visible = true
                tool_12.visible = true
                tool_13.visible = true
                tool_14.visible = true
                tool_15.visible = true
            }
        }
        if (tool_no === 6){
            if (tool_6.state === "released") {

                tool_6.state = "selected"

                tool_1.visible = false
                tool_2.visible = false
                tool_3.visible = false
                tool_4.visible = false
                tool_5.visible = false
                tool_7.visible = false
                tool_8.visible = false
                tool_9.visible = false
                tool_10.visible = false
                tool_11.visible = false
                tool_12.visible = false
                tool_13.visible = false
                tool_14.visible = false
                tool_15.visible = false

            }
            else {

                tool_6.state = "released"

                tool_1.visible = true
                tool_2.visible = true
                tool_3.visible = true
                tool_4.visible = true
                tool_5.visible = true
                tool_7.visible = true
                tool_8.visible = true
                tool_9.visible = true
                tool_10.visible = true
                tool_11.visible = true
                tool_12.visible = true
                tool_13.visible = true
                tool_14.visible = true
                tool_15.visible = true
            }
        }
        if (tool_no === 7){
            if (tool_7.state === "released") {

                tool_7.state = "selected"

                tool_1.visible = false
                tool_2.visible = false
                tool_3.visible = false
                tool_4.visible = false
                tool_5.visible = false
                tool_6.visible = false
                tool_8.visible = false
                tool_9.visible = false
                tool_10.visible = false
                tool_11.visible = false
                tool_12.visible = false
                tool_13.visible = false
                tool_14.visible = false
                tool_15.visible = false

            }
            else {

                tool_7.state = "released"

                tool_1.visible = true
                tool_2.visible = true
                tool_3.visible = true
                tool_4.visible = true
                tool_5.visible = true
                tool_6.visible = true
                tool_8.visible = true
                tool_9.visible = true
                tool_10.visible = true
                tool_11.visible = true
                tool_12.visible = true
                tool_13.visible = true
                tool_14.visible = true
                tool_15.visible = true
            }
        }
        if (tool_no === 8){
            if (tool_8.state === "released") {

                tool_8.state = "selected"

                tool_1.visible = false
                tool_2.visible = false
                tool_3.visible = false
                tool_4.visible = false
                tool_5.visible = false
                tool_6.visible = false
                tool_7.visible = false
                tool_9.visible = false
                tool_10.visible = false
                tool_11.visible = false
                tool_12.visible = false
                tool_13.visible = false
                tool_14.visible = false
                tool_15.visible = false

            }
            else {

                tool_8.state = "released"

                tool_1.visible = true
                tool_2.visible = true
                tool_3.visible = true
                tool_4.visible = true
                tool_5.visible = true
                tool_6.visible = true
                tool_7.visible = true
                tool_9.visible = true
                tool_10.visible = true
                tool_11.visible = true
                tool_12.visible = true
                tool_13.visible = true
                tool_14.visible = true
                tool_15.visible = true
            }
        }
        if (tool_no === 9){
            if (tool_9.state === "released") {

                tool_9.state = "selected"

                tool_1.visible = false
                tool_2.visible = false
                tool_3.visible = false
                tool_4.visible = false
                tool_5.visible = false
                tool_6.visible = false
                tool_7.visible = false
                tool_8.visible = false
                tool_10.visible = false
                tool_11.visible = false
                tool_12.visible = false
                tool_13.visible = false
                tool_14.visible = false
                tool_15.visible = false

            }
            else {

                tool_9.state = "released"

                tool_1.visible = true
                tool_2.visible = true
                tool_3.visible = true
                tool_4.visible = true
                tool_5.visible = true
                tool_6.visible = true
                tool_7.visible = true
                tool_8.visible = true
                tool_10.visible = true
                tool_11.visible = true
                tool_12.visible = true
                tool_13.visible = true
                tool_14.visible = true
                tool_15.visible = true
            }
        }
        if (tool_no === 10){
            if (tool_10.state === "released") {

                tool_10.state = "selected"

                tool_1.visible = false
                tool_2.visible = false
                tool_3.visible = false
                tool_4.visible = false
                tool_5.visible = false
                tool_6.visible = false
                tool_7.visible = false
                tool_8.visible = false
                tool_9.visible = false
                tool_11.visible = false
                tool_12.visible = false
                tool_13.visible = false
                tool_14.visible = false
                tool_15.visible = false

            }
            else {

                tool_10.state = "released"

                tool_1.visible = true
                tool_2.visible = true
                tool_3.visible = true
                tool_4.visible = true
                tool_5.visible = true
                tool_6.visible = true
                tool_7.visible = true
                tool_8.visible = true
                tool_9.visible = true
                tool_11.visible = true
                tool_12.visible = true
                tool_13.visible = true
                tool_14.visible = true
                tool_15.visible = true
            }
        }
        if (tool_no === 11){
            if (tool_11.state === "released") {

                tool_11.state = "selected"

                tool_1.visible = false
                tool_2.visible = false
                tool_3.visible = false
                tool_4.visible = false
                tool_5.visible = false
                tool_6.visible = false
                tool_7.visible = false
                tool_8.visible = false
                tool_9.visible = false
                tool_10.visible = false
                tool_12.visible = false
                tool_13.visible = false
                tool_14.visible = false
                tool_15.visible = false

            }
            else {

                tool_11.state = "released"

                tool_1.visible = true
                tool_2.visible = true
                tool_3.visible = true
                tool_4.visible = true
                tool_5.visible = true
                tool_6.visible = true
                tool_7.visible = true
                tool_8.visible = true
                tool_9.visible = true
                tool_10.visible = true
                tool_12.visible = true
                tool_13.visible = true
                tool_14.visible = true
                tool_15.visible = true
            }
        }
        if (tool_no === 12){
            if (tool_12.state === "released") {

                tool_12.state = "selected"

                tool_1.visible = false
                tool_2.visible = false
                tool_3.visible = false
                tool_4.visible = false
                tool_5.visible = false
                tool_6.visible = false
                tool_7.visible = false
                tool_8.visible = false
                tool_9.visible = false
                tool_10.visible = false
                tool_11.visible = false
                tool_13.visible = false
                tool_14.visible = false
                tool_15.visible = false

            }
            else {

                tool_12.state = "released"

                tool_1.visible = true
                tool_2.visible = true
                tool_3.visible = true
                tool_4.visible = true
                tool_5.visible = true
                tool_6.visible = true
                tool_7.visible = true
                tool_8.visible = true
                tool_9.visible = true
                tool_10.visible = true
                tool_11.visible = true
                tool_13.visible = true
                tool_14.visible = true
                tool_15.visible = true
            }
        }
        if (tool_no === 13){
            if (tool_13.state === "released") {

                tool_13.state = "selected"

                tool_1.visible = false
                tool_2.visible = false
                tool_3.visible = false
                tool_4.visible = false
                tool_5.visible = false
                tool_6.visible = false
                tool_7.visible = false
                tool_8.visible = false
                tool_9.visible = false
                tool_10.visible = false
                tool_11.visible = false
                tool_12.visible = false
                tool_14.visible = false
                tool_15.visible = false

            }
            else {

                tool_13.state = "released"

                tool_1.visible = true
                tool_2.visible = true
                tool_3.visible = true
                tool_4.visible = true
                tool_5.visible = true
                tool_6.visible = true
                tool_7.visible = true
                tool_8.visible = true
                tool_9.visible = true
                tool_10.visible = true
                tool_11.visible = true
                tool_12.visible = true
                tool_14.visible = true
                tool_15.visible = true
            }
        }
        if (tool_no === 14){
            if (tool_14.state === "released") {

                tool_14.state = "selected"

                tool_1.visible = false
                tool_2.visible = false
                tool_3.visible = false
                tool_4.visible = false
                tool_5.visible = false
                tool_6.visible = false
                tool_7.visible = false
                tool_8.visible = false
                tool_9.visible = false
                tool_10.visible = false
                tool_11.visible = false
                tool_12.visible = false
                tool_13.visible = false
                tool_15.visible = false

            }
            else {

                tool_14.state = "released"

                tool_1.visible = true
                tool_2.visible = true
                tool_3.visible = true
                tool_4.visible = true
                tool_5.visible = true
                tool_6.visible = true
                tool_7.visible = true
                tool_8.visible = true
                tool_9.visible = true
                tool_10.visible = true
                tool_11.visible = true
                tool_12.visible = true
                tool_13.visible = true
                tool_15.visible = true
            }
        }
        if (tool_no === 15){
            if (tool_15.state === "released") {

                tool_15.state = "selected"

                tool_1.visible = false
                tool_2.visible = false
                tool_3.visible = false
                tool_4.visible = false
                tool_5.visible = false
                tool_6.visible = false
                tool_7.visible = false
                tool_8.visible = false
                tool_9.visible = false
                tool_10.visible = false
                tool_11.visible = false
                tool_12.visible = false
                tool_13.visible = false
                tool_14.visible = false

            }
            else {

                tool_15.state = "released"

                tool_1.visible = true
                tool_2.visible = true
                tool_3.visible = true
                tool_4.visible = true
                tool_5.visible = true
                tool_6.visible = true
                tool_7.visible = true
                tool_8.visible = true
                tool_9.visible = true
                tool_10.visible = true
                tool_11.visible = true
                tool_12.visible = true
                tool_13.visible = true
                tool_14.visible = true
            }
        }
    }
}
