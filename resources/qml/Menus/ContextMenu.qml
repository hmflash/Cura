// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Dialogs 1.2
import QtQuick.Window 2.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: base

    property bool shouldShowExtruders: machineExtruderCount.properties.value > 1;

    // Selection-related actions.
    MenuItem { action: Cura.Actions.centerSelection; }
    MenuItem { action: Cura.Actions.deleteSelection; }
    MenuItem { action: Cura.Actions.multiplySelection; }

    // Extruder selection - only visible if there is more than 1 extruder
    MenuSeparator { visible: base.shouldShowExtruders }
    MenuItem { id: extruderHeader; text: catalog.i18ncp("@label", "Print Selected Model With:", "Print Selected Models With:", UM.Selection.selectionCount); enabled: false; visible: base.shouldShowExtruders }
    Instantiator
    {
        model: Cura.ExtrudersModel { id: extrudersModel }
        MenuItem {
            text: "%1: %2 - %3".arg(model.name).arg(model.material).arg(model.variant)
            visible: base.shouldShowExtruders
            enabled: UM.Selection.hasSelection
            checkable: true
            checked: ExtruderManager.selectedObjectExtruders.indexOf(model.id) != -1
            onTriggered: CuraActions.setExtruderForSelection(model.id)
            shortcut: "Ctrl+" + (model.index + 1)
        }
        onObjectAdded: base.insertItem(index, object)
        onObjectRemoved: base.removeItem(object)
    }

    // Global actions
    MenuSeparator {}
    MenuItem { action: Cura.Actions.selectAll; }
    MenuItem { action: Cura.Actions.arrangeAll; }
    MenuItem { action: Cura.Actions.deleteAll; }
    MenuItem { action: Cura.Actions.reloadAll; }
    MenuItem { action: Cura.Actions.resetAllTranslation; }
    MenuItem { action: Cura.Actions.resetAll; }

    // Group actions
    MenuSeparator {}
    MenuItem { action: Cura.Actions.groupObjects; }
    MenuItem { action: Cura.Actions.mergeObjects; }
    MenuItem { action: Cura.Actions.unGroupObjects; }

    Connections
    {
        target: UM.Controller
        onContextMenuRequested: base.popup();
    }

    Connections
    {
        target: Cura.Actions.multiplySelection
        onTriggered: multiplyDialog.open()
    }

    UM.SettingPropertyProvider
    {
        id: machineExtruderCount

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_extruder_count"
        watchedProperties: [ "value" ]
    }

    Dialog
    {
        id: multiplyDialog

        title: catalog.i18ncp("@title:window", "Multiply Selected Model", "Multiply Selected Models", UM.Selection.selectionCount)

        width: 400 * Screen.devicePixelRatio
        height: 80 * Screen.devicePixelRatio

        onAccepted: CuraActions.multiplySelection(copiesField.value)

        signal reset()
        onReset:
        {
            copiesField.value = 1;
            copiesField.focus = true;
        }

        onVisibleChanged:
        {
            copiesField.forceActiveFocus();
        }

        standardButtons: StandardButton.Ok | StandardButton.Cancel

        Row
        {
            spacing: UM.Theme.getSize("default_margin").width

            Label
            {
                text: catalog.i18nc("@label", "Number of Copies")
                anchors.verticalCenter: copiesField.verticalCenter
            }

            SpinBox
            {
                id: copiesField
                focus: true
                minimumValue: 1
                maximumValue: 99
            }
        }
    }

    // Find the index of an item in the list of child items of this menu.
    //
    // This is primarily intended as a helper function so we do not have to
    // hard-code the position of the extruder selection actions.
    //
    // \param item The item to find the index of.
    //
    // \return The index of the item or -1 if it was not found.
    function findItemIndex(item)
    {
        for(var i in base.items)
        {
            if(base.items[i] == item)
            {
                return i;
            }
        }
        return -1;
    }

    UM.I18nCatalog { id: catalog; name: "cura" }
}
