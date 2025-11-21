import QtQuick 2.12
import QtQuick.Controls 2.4
import QtQuick.Layouts 1.3

Rectangle {
    id: widget_container
    clip: false
    transformOrigin: Item.Center
    color: "#939695"
    border.color: "#00000000"
    //width: parent ? parent.width : widget_width
    width: 600
    height: 491

    property real widget_width: 600

    Image {
        id: facing_img
        fillMode: Image.PreserveAspectFit
        width: widget_container.width-100
        z: 0
        rotation: 0
        anchors.centerIn: widget_container
        transformOrigin: Item.Center
        source: "images/face_milling.png"
    }

    ColumnLayout {
        TextField {
            id: x_start
            text: "0.0"
            width: 50
        }
        TextField {
            id: y_start
            text: "0.1"
            width: 50
        }
    }

    TextField {
        id: x_end
        text: "20"
        anchors.right: facing_img.right
    }
    Text {
        text: "position 3"
        anchors.bottom: facing_img.bottom
    }

    Text {
        text: "position 4"
        anchors.bottom: facing_img.bottom
        anchors.right: facing_img.right
    }
        


    Connections {
        target: facing_handler;
        
        
    }
}


 
